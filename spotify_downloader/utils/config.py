"""
Configuration management for Spotify Playlist Downloader
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings for the downloader"""
    
    # Spotify API credentials
    spotify_client_id: str
    spotify_client_secret: str
    
    # RuTracker credentials
    rutracker_login: str
    rutracker_password: str
    
    # Playlist settings
    spotify_playlist_id: str
    
    # Output settings
    output_csv: str = 'rutracker_links.csv'
    debug_dir: str = 'debug_html'
    torrents_dir: str = 'torrents'
    download_folder: Optional[str] = None  # Custom download folder for torrents
    
    # Feature flags
    download_torrents: bool = True
    open_with_transmission: bool = True
    selective_download: bool = True
    enable_content_analysis: bool = False
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls(
            spotify_client_id=os.getenv('SPOTIFY_CLIENT_ID', ''),
            spotify_client_secret=os.getenv('SPOTIFY_CLIENT_SECRET', ''),
            rutracker_login=os.getenv('RUTRACKER_LOGIN', ''),
            rutracker_password=os.getenv('RUTRACKER_PASSWORD', ''),
            spotify_playlist_id=os.getenv('SPOTIFY_PLAYLIST_ID', ''),
            output_csv=os.getenv('OUTPUT_CSV', 'rutracker_links.csv'),
            debug_dir=os.getenv('DEBUG_DIR', 'debug_html'),
            torrents_dir=os.getenv('TORRENTS_DIR', 'torrents'),
            download_folder=os.getenv('DOWNLOAD_FOLDER'),
            download_torrents=os.getenv('DOWNLOAD_TORRENTS', 'true').lower() == 'true',
            open_with_transmission=os.getenv('OPEN_WITH_TRANSMISSION', 'true').lower() == 'true',
            selective_download=os.getenv('SELECTIVE_DOWNLOAD', 'true').lower() == 'true',
            enable_content_analysis=os.getenv('ENABLE_CONTENT_ANALYSIS', 'false').lower() == 'true'
        )
    
    def validate(self) -> None:
        """Validate configuration settings"""
        if not self.spotify_client_id:
            raise ValueError("Spotify client ID is required")
        if not self.spotify_client_secret:
            raise ValueError("Spotify client secret is required")
        if not self.rutracker_login:
            raise ValueError("RuTracker login is required")
        if not self.rutracker_password:
            raise ValueError("RuTracker password is required")
        if not self.spotify_playlist_id:
            raise ValueError("Spotify playlist ID is required")
    
    def create_directories(self) -> None:
        """Create necessary directories"""
        os.makedirs(self.debug_dir, exist_ok=True)
        os.makedirs(self.torrents_dir, exist_ok=True)
        if self.download_folder:
            os.makedirs(self.download_folder, exist_ok=True)