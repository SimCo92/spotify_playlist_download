"""
RuTracker client for searching and downloading torrents
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urlparse, parse_qs
import os

from ..utils.config import Config
from ..utils.matching import MatchingEngine

logger = logging.getLogger(__name__)


class RuTrackerClient:
    """Client for interacting with RuTracker"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None
        self.matching_engine = MatchingEngine()
        
    def login(self) -> bool:
        """Log in to RuTracker and return authenticated session"""
        logger.info("Logging in to RuTracker...")
        self.session = requests.Session()
        login_url = 'https://rutracker.org/forum/login.php'
        
        try:
            # Get login form
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://rutracker.org/forum/index.php'
            }
            response = self.session.get(login_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Login page failed: HTTP {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.text, 'html.parser')
            login_data = {
                'login_username': self.config.rutracker_login,
                'login_password': self.config.rutracker_password,
                'login': 'Вход'
            }
            
            # Find all hidden input fields
            for hidden in soup.select('input[type=hidden]'):
                if hidden.get('name') and hidden.get('value'):
                    login_data[hidden['name']] = hidden['value']
            
            # Perform login
            response = self.session.post(login_url, data=login_data, headers=headers)
            
            # Check login success by looking for username in response
            if self.config.rutracker_login in response.text:
                logger.info("Login successful")
                return True
            elif 'Вы ввели неверное имя пользователя или пароль' in response.text:
                logger.error("Login failed: Invalid credentials")
                self._save_debug_html(response.text, 'login_failed.html')
                return False
            else:
                logger.error("Login verification failed")
                self._save_debug_html(response.text, 'login_unknown.html')
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search RuTracker for a query and return results"""
        logger.info(f"Searching RuTracker: {query}")
        search_url = 'https://rutracker.org/forum/search.php'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://rutracker.org/forum/index.php'
        }
        
        try:
            # Clean the query of problematic characters first
            clean_query = re.sub(r'[^\w\s.-]', '', query)
            
            # Use simple UTF-8 encoding for better compatibility
            encoded_query = quote(clean_query, safe='')
            params = {'nm': encoded_query}
            
            # Log the exact search URL we're using
            search_full_url = f"{search_url}?nm={encoded_query}"
            logger.info(f"Search URL: {search_full_url}")
            
            response = self.session.get(search_url, params=params, headers=headers)
            
            # Handle possible redirect to tracker.php
            final_url = response.url
            if 'tracker.php' in final_url:
                logger.debug(f"Redirected to: {final_url}")
                # Extract actual search parameters from redirect URL
                parsed_url = urlparse(final_url)
                query_params = parse_qs(parsed_url.query)
                actual_query = query_params.get('nm', [''])[0]
                logger.debug(f"Actual search query: {actual_query}")
            
            if response.status_code != 200:
                logger.warning(f"Search failed: HTTP {response.status_code} for query: {query}")
                return []
            
            # Save HTML for debugging
            filename = f"search_{re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]}.html"
            self._save_debug_html(response.text, filename)
            
            # Parse results
            results = self._parse_search_results(response.text)
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {str(e)}")
            return []
    
    def get_best_match(self, track: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Find the best RuTracker match for a track"""
        artist = track['artist']
        track_name = track['name']
        album = track['album']
        
        # Clean problematic characters and normalize text
        def clean_text(text):
            # Remove special characters but keep alphanumeric, spaces, dots, and hyphens
            cleaned = re.sub(r'[^\w\s.-]', '', text)
            # Normalize whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned
        
        artist = clean_text(artist)
        track_name = clean_text(track_name)
        album = clean_text(album)
        
        # Multiple search strategies with different approaches
        # Start with more specific searches, then broaden
        search_strategies = [
            # Strategy 1: Artist + track (most specific)
            (f"Searching for artist + track: {artist} {track_name}", f"{artist} {track_name}"),
            
            # Strategy 2: Artist + album 
            (f"Searching for artist + album: {artist} {album}", f"{artist} {album}"),
            
            # Strategy 3: Artist only (often gives good results)
            (f"Searching for artist: {artist}", artist),
            
            # Strategy 4: Track name only (broader search)
            (f"Searching for track: {track_name}", track_name),
            
            # Strategy 5: Album only (if it's distinctive)
            (f"Searching for album: {album}", album),
            
            # Strategy 6: Simplified versions (only if original searches fail)
            (f"Searching simplified artist: {artist.split()[0] if artist else ''}", artist.split()[0] if artist else ''),
        ]
        
        all_results = []
        
        for strategy_desc, query in search_strategies:
            if not query or len(query.strip()) < 2:
                continue
                
            logger.info(strategy_desc)
            results = self.search(query)
            
            if results:
                # Tag results with their search strategy for better ranking
                for result in results:
                    result['search_strategy'] = strategy_desc
                all_results.extend(results)
        
        if all_results:
            # Remove duplicates based on link
            seen_links = set()
            unique_results = []
            for result in all_results:
                if result['link'] not in seen_links:
                    seen_links.add(result['link'])
                    unique_results.append(result)
            
            # Calculate match scores for all results
            logger.info(f"Calculating match scores for {len(unique_results)} unique results...")
            for result in unique_results:
                result['match_score'] = self.matching_engine.calculate_match_score(result, artist, track_name, album)
                logger.debug(f"Score {result['match_score']:.3f}: {result['title'][:60]}...")
            
            # Sort by match score (higher is better), then by priority
            unique_results.sort(key=lambda x: (x['match_score'], x['priority']), reverse=True)
            
            best_match = unique_results[0]
            logger.info(f"Best match (score: {best_match['match_score']:.3f}): {best_match['title']}")
            
            return best_match
        
        logger.warning(f"No results found for: {artist} - {track_name}")
        return None
    
    def get_torrent_download_url(self, torrent_page_url: str) -> Optional[str]:
        """Extract the torrent download URL from a RuTracker page"""
        logger.debug(f"Extracting torrent download URL from: {torrent_page_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://rutracker.org/forum/index.php'
            }
            
            response = self.session.get(torrent_page_url, headers=headers)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch torrent page: HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Find the download link using CSS selectors
            download_link = soup.find('a', {'class': 'dl-link'})
            if download_link:
                href = download_link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = 'https://rutracker.org/forum/' + href
                    logger.debug(f"Found download link: {href}")
                    return href
            
            # Method 2: Look for dl.php links in the HTML
            dl_links = soup.find_all('a', href=re.compile(r'dl\.php\?t=\d+'))
            if dl_links:
                href = dl_links[0].get('href')
                if not href.startswith('http'):
                    href = 'https://rutracker.org/forum/' + href
                logger.debug(f"Found dl.php link: {href}")
                return href
            
            # Method 3: Extract topic ID from URL and construct download link
            topic_id_match = re.search(r't=(\d+)', torrent_page_url)
            if topic_id_match:
                topic_id = topic_id_match.group(1)
                constructed_url = f'https://rutracker.org/forum/dl.php?t={topic_id}'
                logger.debug(f"Constructed download link: {constructed_url}")
                return constructed_url
            
            logger.warning("No download links found")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting torrent download URL: {str(e)}")
            return None
    
    def download_torrent_file(self, download_url: str, filename: str) -> Optional[str]:
        """Download a torrent file"""
        logger.info(f"Downloading torrent: {download_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://rutracker.org/forum/index.php'
            }
            
            response = self.session.get(download_url, headers=headers)
            
            if response.status_code == 200:
                # Check if it's actually a torrent file
                content_type = response.headers.get('content-type', '')
                if 'application/x-bittorrent' in content_type or filename.endswith('.torrent'):
                    filepath = os.path.join(self.config.torrents_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Downloaded torrent file: {filepath}")
                    return filepath
                else:
                    logger.warning(f"Response doesn't appear to be a torrent file. Content-Type: {content_type}")
                    return None
            else:
                logger.warning(f"Download failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading torrent: {str(e)}")
            return None
    
    def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse RuTracker search results from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find results table - correct selector based on actual HTML structure
        table = soup.find('table', class_=lambda c: c and 'forumline' in c and 'tablesorter' in c)
        if not table:
            logger.debug("No results table found")
            return results
        
        # Process each result row
        tbody = table.find('tbody')
        if not tbody:
            logger.debug("No tbody found in results table")
            return results
            
        for row in tbody.find_all('tr', class_=lambda c: c and 'tCenter' in c):
            try:
                # Find the title cell (3rd column, index 2)
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                    
                title_cell = cells[2]  # Third column contains the title
                
                # Find the topic link inside the topictitle div
                topictitle_div = title_cell.find('div', class_='topictitle')
                if not topictitle_div:
                    continue
                    
                # Find the anchor tag with the topic link
                title_tag = topictitle_div.find('a', class_='topictitle')
                if not title_tag:
                    continue
                        
                title = title_tag.get_text(strip=True)
                relative_link = title_tag.get('href')
                
                # Handle relative URLs
                if relative_link.startswith('viewtopic.php'):
                    link = 'https://rutracker.org/forum/' + relative_link
                elif relative_link.startswith('/forum/viewtopic.php'):
                    link = 'https://rutracker.org' + relative_link
                else:
                    link = relative_link
                
                # Determine quality
                quality = 'lossy'
                if re.search(r'\b(FLAC|APE|WAV|24bit|lossless|无损)\b', title, re.IGNORECASE):
                    quality = 'lossless'
                
                # Determine type
                result_type = 'single'
                if re.search(r'\b(album|дискография|сборник|collection|disc|LP|EP|CD|box)\b', title, re.IGNORECASE):
                    result_type = 'album'
                    
                # Calculate priority
                priority = 1
                if quality == 'lossless' and result_type == 'single':
                    priority = 4
                elif quality == 'lossless' and result_type == 'album':
                    priority = 3
                elif quality == 'lossy' and result_type == 'single':
                    priority = 2
                    
                results.append({
                    'title': title,
                    'link': link,
                    'quality': quality,
                    'type': result_type,
                    'priority': priority
                })
            except Exception as e:
                logger.debug(f"Error parsing result row: {str(e)}")
                continue
        
        return results
    
    def _save_debug_html(self, content: str, filename: str) -> None:
        """Save HTML content for debugging"""
        path = os.path.join(self.config.debug_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved debug HTML: {path}")