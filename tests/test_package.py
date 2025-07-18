"""
Test package imports and basic functionality
"""

import pytest
from spotify_downloader.utils.config import Config
from spotify_downloader.utils.matching import MatchingEngine
from spotify_downloader.utils.torrent import TorrentAnalyzer


def test_config_creation():
    """Test that Config can be created"""
    config = Config(
        spotify_client_id="test_id",
        spotify_client_secret="test_secret",
        rutracker_login="test_login",
        rutracker_password="test_password",
        spotify_playlist_id="test_playlist_id"
    )
    
    assert config.spotify_client_id == "test_id"
    assert config.spotify_client_secret == "test_secret"
    assert config.rutracker_login == "test_login"


def test_config_validation():
    """Test that Config validation works"""
    config = Config(
        spotify_client_id="",
        spotify_client_secret="test_secret",
        rutracker_login="test_login",
        rutracker_password="test_password",
        spotify_playlist_id="test_playlist_id"
    )
    
    with pytest.raises(ValueError, match="Spotify client ID is required"):
        config.validate()


def test_matching_engine():
    """Test that MatchingEngine works"""
    engine = MatchingEngine()
    
    # Test similarity calculation
    similarity = engine.calculate_similarity("hello world", "hello world")
    assert similarity == 1.0
    
    similarity = engine.calculate_similarity("hello", "world")
    assert similarity < 1.0


def test_torrent_analyzer():
    """Test that TorrentAnalyzer can be created"""
    analyzer = TorrentAnalyzer()
    assert analyzer is not None