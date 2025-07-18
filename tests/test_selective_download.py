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

def test_selective_download():
    """Test the selective download functionality specifically"""
    
    # Test track - this should have a perfect match
    test_track = {
        'name': 'She Wants To Move',
        'artist': 'N.E.R.D',
        'album': 'Fly Or Die'
    }
    
    logger.info("=== TESTING SELECTIVE DOWNLOAD ===")
    logger.info(f"Test track: {test_track['artist']} - {test_track['name']}")
    
    # First, clear any existing downloads in Transmission
    logger.info("Starting selective download test...")
    
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
    
    # Extract torrent download URL
    logger.info("Extracting torrent download URL...")
    download_url = extract_torrent_download_url(session, match['link'])
    
    if not download_url:
        logger.error("Failed to extract torrent download URL")
        return
    
    # Download torrent file with a unique name
    logger.info("Downloading torrent file...")
    torrent_filename = f"selective_test_{test_track['artist']}-{test_track['name']}.torrent"
    torrent_filename = re.sub(r'[^\w\s-]', '', torrent_filename)
    torrent_filename = re.sub(r'[-\s]+', '-', torrent_filename)
    
    torrent_file = download_torrent_file(session, download_url, torrent_filename)
    
    if not torrent_file:
        logger.error("Failed to download torrent file")
        return
    
    logger.info(f"Downloaded torrent file: {torrent_file}")
    
    # Test selective download with Transmission
    logger.info("Testing selective download with Transmission...")
    logger.info("This should download ONLY the .flac file, not the .cue, .log, or cover images")
    
    if open_with_transmission(torrent_file, test_track['name'], test_track['artist']):
        logger.info("✓ Successfully added to Transmission with selective download")
        logger.info("")
        logger.info("🔍 CHECK TRANSMISSION NOW:")
        logger.info("- Look for the torrent in Transmission")
        logger.info("- Check that only 'N.E.R.D - She Wants To Move.flac' is selected for download")
        logger.info("- Other files (.cue, .log, cover images) should be deselected")
        logger.info("")
        logger.info("If selective download worked correctly, you should see:")
        logger.info("✓ N.E.R.D - She Wants To Move.flac (downloading)")
        logger.info("✗ N.E.R.D - She Wants To Move.cue (not downloading)")
        logger.info("✗ N.E.R.D - She Wants To Move.log (not downloading)")
        logger.info("✗ CD.png (not downloading)")
        logger.info("✗ Sleeve Back.png (not downloading)")
        logger.info("✗ Sleeve Front.png (not downloading)")
    else:
        logger.error("✗ Failed to add to Transmission")
    
    logger.info("=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_selective_download()