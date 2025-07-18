#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import quote

# Test credentials
RUTRACKER_LOGIN = 'totoskillato'
RUTRACKER_PASSWORD = 'J56ah'

def rutracker_login():
    """Log in to Rutracker and return authenticated session"""
    print("Logging in to Rutracker...")
    session = requests.Session()
    login_url = 'https://rutracker.org/forum/login.php'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://rutracker.org/forum/index.php'
        }
        response = session.get(login_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        login_data = {
            'login_username': RUTRACKER_LOGIN,
            'login_password': RUTRACKER_PASSWORD,
            'login': 'Вход'
        }
        
        for hidden in soup.select('input[type=hidden]'):
            if hidden.get('name') and hidden.get('value'):
                login_data[hidden['name']] = hidden['value']
        
        response = session.post(login_url, data=login_data, headers=headers)
        
        if RUTRACKER_LOGIN in response.text:
            print("Login successful")
            return session
        else:
            print("Login failed")
            return None
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return None

def parse_rutracker_results(html):
    """Parse Rutracker search results from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Find results table - correct selector based on actual HTML structure
    table = soup.find('table', class_=lambda c: c and 'forumline' in c and 'tablesorter' in c)
    if not table:
        print("No results table found")
        return results
    
    # Process each result row
    tbody = table.find('tbody')
    if not tbody:
        print("No tbody found in results table")
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
            print(f"Error parsing result row: {str(e)}")
            continue
    
    return results

def search_rutracker(session, query):
    """Search Rutracker for a query and return results"""
    print(f"Searching Rutracker: {query}")
    search_url = 'https://rutracker.org/forum/search.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://rutracker.org/forum/index.php'
    }
    
    try:
        # Clean the query of problematic characters
        clean_query = re.sub(r'[^\w\s.-]', '', query)
        
        # Use simple UTF-8 encoding for better compatibility
        encoded_query = quote(clean_query, safe='')
        params = {'nm': encoded_query}
        
        response = session.get(search_url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Search failed: HTTP {response.status_code} for query: {query}")
            return []
        
        # Parse results
        results = parse_rutracker_results(response.text)
        print(f"Found {len(results)} results for query: {query}")
        return results
        
    except Exception as e:
        print(f"Search error for query '{query}': {str(e)}")
        return []

def get_best_rutracker_match(session, track):
    """Find the best Rutracker match for a track"""
    artist = track['artist']
    track_name = track['name']
    album = track['album']
    
    # Strategy 1: Search for track (artist + track name)
    print(f"Searching for track: {artist} - {track_name}")
    track_query = f"{artist} {track_name}"
    track_results = search_rutracker(session, track_query)
    
    if track_results:
        # Sort by priority and return best match
        track_results.sort(key=lambda x: x['priority'], reverse=True)
        return track_results[0]
    
    # Strategy 2: Search for album (artist + album)
    print(f"Searching for album: {artist} - {album}")
    album_query = f"{artist} {album}"
    album_results = search_rutracker(session, album_query)
    
    if album_results:
        # Sort by priority and return best match
        album_results.sort(key=lambda x: x['priority'], reverse=True)
        return album_results[0]
    
    # Strategy 3: Search with simplified query (track name only)
    print(f"Searching simplified: {track_name}")
    simple_results = search_rutracker(session, track_name)
    
    if simple_results:
        simple_results.sort(key=lambda x: x['priority'], reverse=True)
        return simple_results[0]
    
    print(f"No results found for: {artist} - {track_name}")
    return None

def test_full_workflow():
    """Test the full workflow with sample tracks"""
    session = rutracker_login()
    if not session:
        return
    
    # Test with sample tracks
    test_tracks = [
        {'name': 'Yesterday', 'artist': 'The Beatles', 'album': 'Help!'},
        {'name': 'Bohemian Rhapsody', 'artist': 'Queen', 'album': 'A Night at the Opera'},
        {'name': 'Hotel California', 'artist': 'Eagles', 'album': 'Hotel California'}
    ]
    
    print("\n=== TESTING FULL WORKFLOW ===")
    
    for i, track in enumerate(test_tracks):
        print(f"\n--- Processing track {i+1}: {track['artist']} - {track['name']} ---")
        
        try:
            match = get_best_rutracker_match(session, track)
            if match:
                print(f"✓ Found match: {match['title']}")
                print(f"  Link: {match['link']}")
                print(f"  Quality: {match['quality']}, Type: {match['type']}, Priority: {match['priority']}")
            else:
                print("✗ No match found")
        except Exception as e:
            print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    test_full_workflow()