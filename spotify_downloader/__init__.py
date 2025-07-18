"""
Spotify Playlist Downloader

A tool to download high-quality music from Spotify playlists via torrent sites.
"""

__version__ = "1.0.0"
__author__ = "Spotify Downloader Team"
__email__ = "contact@example.com"

from .core.downloader import SpotifyPlaylistDownloader
from .core.rutracker import RuTrackerClient
from .core.transmission import TransmissionClient

__all__ = [
    "SpotifyPlaylistDownloader",
    "RuTrackerClient", 
    "TransmissionClient"
]