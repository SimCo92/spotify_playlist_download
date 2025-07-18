#!/usr/bin/env python3

# Simple test of key functions from the fixed main script
import sys
import os
sys.path.append('/Users/simonecolonna')

# Import the fixed functions
from spotify_playlist_download import rutracker_login, search_rutracker, get_best_rutracker_match

def test_fixed_functions():
    """Test the fixed functions with sample data"""
    print("=== TESTING FIXED FUNCTIONS ===")
    
    # Login
    session = rutracker_login()
    if not session:
        print("Login failed")
        return
    
    # Test with a simple track
    test_track = {
        'name': 'Yesterday',
        'artist': 'The Beatles',
        'album': 'Help!'
    }
    
    print(f"\nTesting with track: {test_track['artist']} - {test_track['name']}")
    
    try:
        match = get_best_rutracker_match(session, test_track)
        if match:
            print(f"✓ Found match: {match['title']}")
            print(f"  Link: {match['link']}")
            print(f"  Quality: {match['quality']}, Type: {match['type']}, Priority: {match['priority']}")
        else:
            print("✗ No match found")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_functions()