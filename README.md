# Spotify Torrent Downloader

A Python tool to download high-quality music from Spotify playlists via torrent sites with intelligent selective downloading.

## Features

- **Spotify Integration**: Extract tracks from any Spotify playlist
- **Smart Torrent Search**: Find high-quality music torrents on RuTracker
- **Selective Download**: Automatically download only the specific songs you want from multi-file torrents
- **Transmission Integration**: Seamlessly integrate with Transmission BitTorrent client on macOS
- **Quality Prioritization**: Prefer lossless formats (FLAC, WAV) over lossy (MP3)
- **Match Scoring**: Intelligent algorithm to find the best matches for your tracks
- **Progress Tracking**: CSV output with detailed information about each download

## Installation

### Prerequisites

- Python 3.8 or higher
- [Transmission BitTorrent client](https://transmissionbt.com/) (for automatic torrent handling)
- [transmission-cli](https://github.com/transmission/transmission) (for selective download features)

### Install transmission-cli on macOS

```bash
brew install transmission-cli
```

### Install the package

```bash
# Clone the repository
git clone https://github.com/yourusername/spotify-torrent-downloader.git
cd spotify-torrent-downloader

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
RUTRACKER_LOGIN=your_rutracker_username
RUTRACKER_PASSWORD=your_rutracker_password
SPOTIFY_PLAYLIST_ID=your_playlist_id

# Optional
OUTPUT_CSV=rutracker_links.csv
DEBUG_DIR=debug_html
TORRENTS_DIR=torrents
DOWNLOAD_TORRENTS=true
OPEN_WITH_TRANSMISSION=true
SELECTIVE_DOWNLOAD=true
ENABLE_CONTENT_ANALYSIS=false
```

### Getting Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Copy the Client ID and Client Secret

### Getting Playlist ID

From a Spotify playlist URL like `https://open.spotify.com/playlist/16xx0lOkwugbnZygJ41Dm4`, the playlist ID is `16xx0lOkwugbnZygJ41Dm4`.

## Usage

### Command Line Interface

```bash
# Basic usage (using environment variables)
spotify-downloader

# Specify playlist ID
spotify-downloader --playlist-id 16xx0lOkwugbnZygJ41Dm4

# Download only first 5 tracks for testing
spotify-downloader --limit 5

# Download without opening Transmission
spotify-downloader --no-transmission

# Download without selective file selection
spotify-downloader --no-selective

# Only find matches, don't download torrents
spotify-downloader --no-download

# Set custom output file
spotify-downloader --output my_results.csv

# Enable debug logging
spotify-downloader --log-level DEBUG
```

### Python API

```python
from spotify_downloader.utils.config import Config
from spotify_downloader.core.downloader import SpotifyPlaylistDownloader

# Create configuration
config = Config.from_env()

# Override specific settings
config.spotify_playlist_id = "16xx0lOkwugbnZygJ41Dm4"
config.selective_download = True

# Create downloader
downloader = SpotifyPlaylistDownloader(config)

# Run the process
downloader.run(limit=5)  # Limit to 5 tracks for testing
```

## How It Works

1. **Playlist Extraction**: Connects to Spotify API to extract track information
2. **Smart Search**: Searches RuTracker using multiple strategies (artist+track, artist+album, etc.)
3. **Match Scoring**: Uses intelligent algorithms to score potential matches
4. **Torrent Analysis**: Analyzes torrent contents to identify specific song files
5. **Selective Download**: Automatically selects only the desired audio files
6. **Transmission Integration**: Adds torrents to Transmission with proper file selection

## Selective Download

The tool automatically analyzes multi-file torrents and selects only the audio files that match your target songs. For example, from a torrent containing:

- ✗ Album cover images
- ✗ .cue files
- ✗ .log files
- ✓ **Target song.flac** (selected)
- ✗ Other songs from the album

Only the target song file will be downloaded, saving bandwidth and storage.

## Output

The tool generates a CSV file with the following columns:

- `spotify_track`: Original track name
- `spotify_artist`: Original artist name
- `spotify_album`: Original album name
- `rutracker_link`: Link to the torrent page
- `rutracker_title`: Title of the torrent
- `quality`: Audio quality (lossless/lossy)
- `type`: Torrent type (single/album)
- `match_score`: Confidence score (0-1)
- `torrent_download_url`: Direct download URL
- `torrent_file`: Path to downloaded .torrent file
- `transmission_opened`: Whether successfully added to Transmission

## Project Structure

```
spotify-torrent-downloader/
├── spotify_downloader/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py              # CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── downloader.py        # Main orchestrator
│   │   ├── rutracker.py         # RuTracker client
│   │   └── transmission.py      # Transmission client
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── matching.py          # Matching algorithms
│       └── torrent.py           # Torrent analysis
├── tests/                       # Test files
├── requirements.txt             # Dependencies
├── setup.py                     # Package setup
└── README.md                    # This file
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=spotify_downloader tests/
```

### Code Quality

```bash
# Format code
black spotify_downloader/

# Check style
flake8 spotify_downloader/

# Type checking
mypy spotify_downloader/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Legal Notice

This tool is for educational purposes only. Please ensure you have the right to download any content and comply with all applicable laws and terms of service.

## License

MIT License - see LICENSE file for details.

## Transmission Remote Commands

### Monitoring Downloads

```bash
# List all torrents with status
transmission-remote -l

# Get detailed info for all torrents
transmission-remote -t all -i

# List only active downloads
transmission-remote -l | grep -E "(Downloading|Up & Down)"

# Show peer information
transmission-remote -t all --peer-info
```

### Managing Downloads

```bash
# Start stalled torrents
transmission-remote -t 1,2,3 --start

# Stop specific torrents
transmission-remote -t 1,2,3 --stop

# Set high priority for all files
transmission-remote -t all --priority-high

# Remove download/upload limits
transmission-remote -D && transmission-remote -U

# Set download limit (in kB/s)
transmission-remote -d 1000

# Set upload limit (in kB/s)  
transmission-remote -u 100
```

### File Selection

```bash
# List files in a torrent
transmission-remote -t 1 --files

# Enable specific files for download
transmission-remote -t 1 --get 1,2,3

# Disable specific files
transmission-remote -t 1 --no-get 4,5,6

# Set file priorities
transmission-remote -t 1 --priority-high 1,2
transmission-remote -t 1 --priority-low 3,4
```

### Troubleshooting

```bash
# Verify torrent data
transmission-remote -t 1 --verify

# Force tracker update
transmission-remote -t 1 --reannounce

# Remove torrent and delete data
transmission-remote -t 1 --remove-and-delete
```

## Changelog

### v1.0.0
- Initial release
- Spotify playlist extraction
- RuTracker search and matching
- Selective torrent downloading
- Transmission integration
- CLI interface
- Comprehensive logging and error handling