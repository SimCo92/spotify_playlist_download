#!/usr/bin/env python3

# Test the improved matching system
import sys
import os
sys.path.append('/Users/simonecolonna')

from spotify_playlist_download import rutracker_login, get_best_rutracker_match, calculate_match_score

def test_improved_matching():
    """Test the improved matching system with better scoring"""
    print("=== TESTING IMPROVED MATCHING SYSTEM ===")
    
    # Login
    session = rutracker_login()
    if not session:
        print("Login failed")
        return
    
    # Test with multiple tracks to see how scoring works
    test_tracks = [
        {
            'name': 'Yesterday',
            'artist': 'The Beatles',
            'album': 'Help!'
        },
        {
            'name': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera'
        },
        {
            'name': 'Imagine',
            'artist': 'John Lennon',
            'album': 'Imagine'
        }
    ]
    
    for i, track in enumerate(test_tracks):
        print(f"\n--- Test {i+1}: {track['artist']} - {track['name']} ---")
        
        try:
            match = get_best_rutracker_match(session, track)
            if match:
                print(f"✓ Found match (score: {match.get('match_score', 'N/A'):.3f})")
                print(f"  Title: {match['title']}")
                print(f"  Link: {match['link']}")
                print(f"  Quality: {match['quality']}, Type: {match['type']}")
                print(f"  Strategy: {match.get('search_strategy', 'Unknown')}")
            else:
                print("✗ No match found")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()

def test_scoring_function():
    """Test the scoring function directly"""
    print("\n=== TESTING SCORING FUNCTION ===")
    
    # Mock results to test scoring
    target_artist = "The Beatles"
    target_track = "Yesterday"
    target_album = "Help!"
    
    test_results = [
        {
            'title': 'The Beatles - Yesterday (1965) [FLAC]',
            'quality': 'lossless',
            'type': 'single'
        },
        {
            'title': 'Beatles Yesterday compilation album',
            'quality': 'lossy',
            'type': 'album'
        },
        {
            'title': 'Various Artists - Yesterday covers',
            'quality': 'lossless',
            'type': 'album'
        },
        {
            'title': 'The Beatles - Help! (Complete Album)',
            'quality': 'lossless',
            'type': 'album'
        }
    ]
    
    print(f"Target: {target_artist} - {target_track} from {target_album}")
    print("\nScoring results:")
    
    for result in test_results:
        score = calculate_match_score(result, target_artist, target_track, target_album)
        print(f"Score {score:.3f}: {result['title']}")

if __name__ == "__main__":
    test_scoring_function()
    test_improved_matching()