"""
Main downloader class that orchestrates the entire process
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv
import re
import time
import logging
from typing import List, Dict, Any, Optional

from ..utils.config import Config
from .rutracker import RuTrackerClient
from .transmission import TransmissionClient

logger = logging.getLogger(__name__)


class SpotifyPlaylistDownloader:
    """Main downloader class that orchestrates the entire process"""
    
    def __init__(self, config: Config):
        self.config = config
        self.config.validate()
        self.config.create_directories()
        
        # Initialize Spotify client
        auth_manager = SpotifyClientCredentials(
            client_id=self.config.spotify_client_id,
            client_secret=self.config.spotify_client_secret
        )
        self.spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        
        # Initialize other clients
        self.rutracker_client = RuTrackerClient(config)
        self.transmission_client = TransmissionClient(config)
    
    def get_playlist_tracks(self, playlist_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Retrieve all tracks from a Spotify playlist"""
        playlist_id = playlist_id or self.config.spotify_playlist_id
        logger.info("Fetching Spotify playlist tracks...")
        
        try:
            results = self.spotify_client.playlist_tracks(playlist_id)
            tracks = []
            
            while results:
                for item in results['items']:
                    track = item['track']
                    # Skip non-track items (podcasts, etc.)
                    if track is None or track['type'] != 'track':
                        continue
                        
                    artist = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                    album = track['album']['name'] if track['album'] else 'Unknown Album'
                    tracks.append({
                        'name': track['name'],
                        'artist': artist,
                        'album': album
                    })
                
                if results['next']:
                    results = self.spotify_client.next(results)
                else:
                    break
            
            logger.info(f"Found {len(tracks)} tracks in the playlist")
            return tracks
        except Exception as e:
            logger.error(f"Error fetching Spotify playlist: {str(e)}")
            return []
    
    def process_tracks(self, tracks: List[Dict[str, str]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process tracks and find their matches on RuTracker"""
        if limit:
            tracks = tracks[:limit]
            logger.info(f"Processing {len(tracks)} tracks (limited)")
        
        # Login to RuTracker
        if not self.rutracker_client.login():
            logger.error("RuTracker login failed. Exiting.")
            return []
        
        # Process tracks
        logger.info("Searching for matches on RuTracker...")
        results = []
        
        for i, track in enumerate(tracks):
            logger.info(f"Processing {i+1}/{len(tracks)}: {track['artist']} - {track['name']}")
            
            try:
                match = self.rutracker_client.get_best_match(track)
            except Exception as e:
                logger.error(f"Error processing track: {str(e)}")
                match = None
            
            # Initialize result data
            result_data = {
                'spotify_track': track['name'],
                'spotify_artist': track['artist'],
                'spotify_album': track['album'],
                'rutracker_link': match['link'] if match else 'Not found',
                'rutracker_title': match['title'] if match else '',
                'quality': match['quality'] if match else '',
                'type': match['type'] if match else '',
                'match_score': f"{match['match_score']:.3f}" if match and 'match_score' in match else '',
                'torrent_download_url': '',
                'torrent_file': '',
                'transmission_opened': 'No'
            }
            
            # If we found a match and torrent downloading is enabled
            if match and self.config.download_torrents:
                try:
                    # Extract torrent download URL
                    download_url = self.rutracker_client.get_torrent_download_url(match['link'])
                    if download_url:
                        result_data['torrent_download_url'] = download_url
                        
                        # Create a safe filename
                        safe_filename = re.sub(r'[^\\w\\s-]', '', f"{track['artist']} - {track['name']}")
                        safe_filename = re.sub(r'[-\\s]+', '-', safe_filename)
                        torrent_filename = f"{safe_filename}.torrent"
                        
                        # Download the torrent file
                        torrent_file = self.rutracker_client.download_torrent_file(download_url, torrent_filename)
                        if torrent_file:
                            result_data['torrent_file'] = torrent_file
                            
                            # Open with Transmission if enabled
                            if self.config.open_with_transmission:
                                if self.transmission_client.add_torrent(torrent_file, track['name'], track['artist']):
                                    result_data['transmission_opened'] = 'Yes'
                                else:
                                    result_data['transmission_opened'] = 'Failed'
                            
                            logger.info(f"Successfully processed torrent for: {track['artist']} - {track['name']}")
                        else:
                            logger.warning(f"Failed to download torrent for: {track['artist']} - {track['name']}")
                    else:
                        logger.warning(f"No download URL found for: {track['artist']} - {track['name']}")
                        
                except Exception as e:
                    logger.error(f"Error processing torrent for {track['artist']} - {track['name']}: {str(e)}")
            
            results.append(result_data)
            
            # Add delay to avoid overwhelming the server
            time.sleep(2)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_file: Optional[str] = None) -> None:
        """Save results to CSV file"""
        output_file = output_file or self.config.output_csv
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'spotify_track', 'spotify_artist', 'spotify_album',
                    'rutracker_link', 'rutracker_title', 'quality', 'type', 'match_score',
                    'torrent_download_url', 'torrent_file', 'transmission_opened'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error writing CSV: {str(e)}")
    
    def run(self, playlist_id: Optional[str] = None, limit: Optional[int] = None) -> None:
        """Run the complete download process"""
        logger.info("Starting Spotify playlist download process")
        
        # Get playlist tracks
        tracks = self.get_playlist_tracks(playlist_id)
        if not tracks:
            logger.error("No tracks found. Exiting.")
            return
        
        # Process tracks
        results = self.process_tracks(tracks, limit)
        
        # Save results
        self.save_results(results)
        
        logger.info("Download process completed")