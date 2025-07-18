"""
Command line interface for Spotify Playlist Downloader
"""

import argparse
import logging
import sys
from pathlib import Path

from ..utils.config import Config
from ..core.downloader import SpotifyPlaylistDownloader


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('spotify_downloader.log')
        ]
    )


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Download high-quality music from Spotify playlists via torrent sites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download using environment variables
  spotify-downloader

  # Download with specific playlist ID
  spotify-downloader --playlist-id 16xx0lOkwugbnZygJ41Dm4

  # Download only first 5 tracks for testing
  spotify-downloader --limit 5

  # Download without opening Transmission
  spotify-downloader --no-transmission

  # Download without selective file selection
  spotify-downloader --no-selective

Environment Variables:
  SPOTIFY_CLIENT_ID       - Spotify API client ID
  SPOTIFY_CLIENT_SECRET   - Spotify API client secret
  RUTRACKER_LOGIN        - RuTracker username
  RUTRACKER_PASSWORD     - RuTracker password
  SPOTIFY_PLAYLIST_ID    - Spotify playlist ID
        """
    )
    
    # Required arguments (can be provided via env vars)
    parser.add_argument(
        "--playlist-id",
        help="Spotify playlist ID (can be set via SPOTIFY_PLAYLIST_ID env var)"
    )
    
    parser.add_argument(
        "--spotify-client-id",
        help="Spotify API client ID (can be set via SPOTIFY_CLIENT_ID env var)"
    )
    
    parser.add_argument(
        "--spotify-client-secret",
        help="Spotify API client secret (can be set via SPOTIFY_CLIENT_SECRET env var)"
    )
    
    parser.add_argument(
        "--rutracker-login",
        help="RuTracker username (can be set via RUTRACKER_LOGIN env var)"
    )
    
    parser.add_argument(
        "--rutracker-password",
        help="RuTracker password (can be set via RUTRACKER_PASSWORD env var)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output",
        default="rutracker_links.csv",
        help="Output CSV file (default: rutracker_links.csv)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of tracks to process (useful for testing)"
    )
    
    parser.add_argument(
        "--no-transmission",
        action="store_true",
        help="Don't open torrents with Transmission"
    )
    
    parser.add_argument(
        "--no-selective",
        action="store_true",
        help="Don't use selective file downloading"
    )
    
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Don't download torrent files, only find matches"
    )
    
    parser.add_argument(
        "--debug-dir",
        default="debug_html",
        help="Directory for debug HTML files (default: debug_html)"
    )
    
    parser.add_argument(
        "--torrents-dir",
        default="torrents",
        help="Directory for downloaded torrent files (default: torrents)"
    )
    
    parser.add_argument(
        "--download-folder",
        help="Custom download folder for torrent contents (e.g., ~/Music/Downloads)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    return parser


def main() -> None:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Create configuration
        config = Config.from_env()
        
        # Override with command line arguments
        if args.playlist_id:
            config.spotify_playlist_id = args.playlist_id
        if args.spotify_client_id:
            config.spotify_client_id = args.spotify_client_id
        if args.spotify_client_secret:
            config.spotify_client_secret = args.spotify_client_secret
        if args.rutracker_login:
            config.rutracker_login = args.rutracker_login
        if args.rutracker_password:
            config.rutracker_password = args.rutracker_password
        
        # Override feature flags
        config.output_csv = args.output
        config.debug_dir = args.debug_dir
        config.torrents_dir = args.torrents_dir
        config.open_with_transmission = not args.no_transmission
        config.selective_download = not args.no_selective
        config.download_torrents = not args.no_download
        
        # Override download folder if provided
        if args.download_folder:
            config.download_folder = args.download_folder
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please set the required environment variables or command line arguments")
            sys.exit(1)
        
        # Create and run downloader
        downloader = SpotifyPlaylistDownloader(config)
        downloader.run(limit=args.limit)
        
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()