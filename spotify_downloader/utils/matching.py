"""
Matching engine for finding the best torrent matches
"""

import re
from typing import List, Dict, Any
from difflib import SequenceMatcher


class MatchingEngine:
    """Engine for matching Spotify tracks with torrent results"""
    
    def __init__(self):
        self.audio_extensions = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize both strings
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Use difflib for similarity calculation
        return SequenceMatcher(None, text1, text2).ratio()
    
    def calculate_match_score(self, result: Dict[str, Any], target_artist: str, 
                            target_track: str, target_album: str) -> float:
        """Calculate a comprehensive match score for a result"""
        title = result['title'].lower()
        
        # Calculate individual similarity scores
        artist_score = self.calculate_similarity(target_artist.lower(), title)
        track_score = self.calculate_similarity(target_track.lower(), title)
        album_score = self.calculate_similarity(target_album.lower(), title)
        
        # Check for exact word matches (higher weight)
        artist_words = set(target_artist.lower().split())
        track_words = set(target_track.lower().split())
        album_words = set(target_album.lower().split())
        title_words = set(title.split())
        
        artist_word_matches = len(artist_words.intersection(title_words)) / max(len(artist_words), 1)
        track_word_matches = len(track_words.intersection(title_words)) / max(len(track_words), 1)
        album_word_matches = len(album_words.intersection(title_words)) / max(len(album_words), 1)
        
        # Combined score with weights
        # Artist and track are most important, album is secondary
        combined_score = (
            artist_score * 0.3 +
            track_score * 0.3 +
            album_score * 0.2 +
            artist_word_matches * 0.1 +
            track_word_matches * 0.1
        )
        
        # Bonus for quality and type
        quality_bonus = 0.1 if result['quality'] == 'lossless' else 0
        type_bonus = 0.05 if result['type'] == 'single' else 0
        
        final_score = combined_score + quality_bonus + type_bonus
        
        return final_score
    
    def find_matching_files(self, files: List[Dict[str, Any]], target_track: str, 
                          target_artist: str) -> List[Dict[str, Any]]:
        """Find files that match the target track and artist"""
        matching_files = []
        
        for file_info in files:
            filename = file_info['name'].lower()
            filepath = file_info['path'].lower()
            
            # Skip non-audio files
            if not any(filename.endswith(ext) for ext in self.audio_extensions):
                continue
            
            # Calculate similarity scores
            track_score = self.calculate_similarity(target_track.lower(), filename)
            artist_score = self.calculate_similarity(target_artist.lower(), filename)
            
            # Also check the full path for matches
            path_track_score = self.calculate_similarity(target_track.lower(), filepath)
            path_artist_score = self.calculate_similarity(target_artist.lower(), filepath)
            
            # Use the best scores
            best_track_score = max(track_score, path_track_score)
            best_artist_score = max(artist_score, path_artist_score)
            
            # Check for exact word matches
            track_words = set(target_track.lower().split())
            artist_words = set(target_artist.lower().split())
            file_words = set(filename.replace('.', ' ').replace('_', ' ').replace('-', ' ').split())
            
            track_word_matches = len(track_words.intersection(file_words))
            artist_word_matches = len(artist_words.intersection(file_words))
            
            # Combined score
            combined_score = (
                best_track_score * 0.4 +
                best_artist_score * 0.3 +
                (track_word_matches / max(len(track_words), 1)) * 0.2 +
                (artist_word_matches / max(len(artist_words), 1)) * 0.1
            )
            
            file_info['match_score'] = combined_score
            
            # Consider it a match if score is above threshold
            if combined_score > 0.3:  # Adjustable threshold
                matching_files.append(file_info)
        
        # Sort by match score (highest first)
        matching_files.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matching_files