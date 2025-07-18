#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spotify_playlist_download import (
    rutracker_login, 
    get_best_rutracker_match, 
    extract_torrent_download_url,
    download_torrent_file,
    open_with_transmission,
    logger
)
import re

def test_enhanced_functionality():
    """Test the enhanced functionality with torrent download and Transmission opening"""
    
    # Test track
    test_track = {
        'name': 'She Wants To Move',
        'artist': 'N.E.R.D',
        'album': 'Fly Or Die'
    }
    
    logger.info("=== TESTING ENHANCED FUNCTIONALITY ===")
    logger.info(f"Test track: {test_track['artist']} - {test_track['name']}")
    
    # Login to Rutracker
    session = rutracker_login()
    if not session:
        logger.error("Failed to login to Rutracker")
        return
    
    # Find the best match
    logger.info("Finding best match...")
    match = get_best_rutracker_match(session, test_track)
    
    if not match:
        logger.error("No match found")
        return
    
    logger.info(f"Best match: {match['title']}")
    logger.info(f"Match link: {match['link']}")
    logger.info(f"Match score: {match['match_score']:.3f}")
    
    # Extract torrent download URL
    logger.info("Extracting torrent download URL...")
    download_url = extract_torrent_download_url(session, match['link'])
    
    if not download_url:
        logger.error("Failed to extract torrent download URL")
        return
    
    logger.info(f"Download URL: {download_url}")
    
    # Download torrent file
    logger.info("Downloading torrent file...")
    safe_filename = re.sub(r'[^\w\s-]', '', f"{test_track['artist']} - {test_track['name']}")
    safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
    torrent_filename = f"{safe_filename}.torrent"
    
    torrent_file = download_torrent_file(session, download_url, torrent_filename)
    
    if not torrent_file:
        logger.error("Failed to download torrent file")
        return
    
    logger.info(f"Downloaded torrent file: {torrent_file}")
    
    # Test opening with Transmission with selective download
    logger.info("Testing Transmission opening with selective download...")
    if open_with_transmission(torrent_file, test_track['name'], test_track['artist']):
        logger.info("✓ Successfully opened with Transmission and selective download")
    else:
        logger.error("✗ Failed to open with Transmission")
    
    logger.info("=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_enhanced_functionality()