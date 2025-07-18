"""
Transmission client for managing torrent downloads
"""

import subprocess
import time
import os
import logging
from typing import List, Dict, Any, Optional

from ..utils.config import Config
from ..utils.torrent import TorrentAnalyzer
from ..utils.matching import MatchingEngine

logger = logging.getLogger(__name__)


class TransmissionClient:
    """Client for interacting with Transmission"""
    
    def __init__(self, config: Config):
        self.config = config
        self.torrent_analyzer = TorrentAnalyzer()
        self.matching_engine = MatchingEngine()
    
    def add_torrent(self, torrent_file: str, target_track: Optional[str] = None, 
                   target_artist: Optional[str] = None) -> bool:
        """Add torrent to Transmission, optionally with selective download"""
        logger.info(f"Adding {torrent_file} to Transmission...")
        
        # Analyze torrent contents if selective download is enabled
        selected_files = []
        all_files = []
        if self.config.selective_download and target_track and target_artist:
            logger.info(f"Analyzing torrent contents for selective download...")
            all_files = self.torrent_analyzer.analyze_torrent_contents(torrent_file)
            if all_files:
                logger.info(f"Found {len(all_files)} files in torrent")
                matching_files = self.matching_engine.find_matching_files(all_files, target_track, target_artist)
                if matching_files:
                    selected_files = matching_files[:1]  # Take only the best match
                    logger.info(f"Selected {len(selected_files)} matching files:")
                    for file_info in selected_files:
                        logger.info(f"  - {file_info['name']} (score: {file_info['match_score']:.3f})")
                else:
                    logger.info("No matching files found, will download all files")
        
        # Try multiple methods to add torrent
        success = False
        
        # Method 1: Try using transmission-remote (preferred for selective download)
        if self._is_transmission_remote_available():
            success = self._add_torrent_via_remote(torrent_file, selected_files, all_files)
            if success:
                return True
        
        # Method 2: Try using AppleScript
        if not success:
            success = self._add_torrent_via_applescript(torrent_file)
            if success:
                if selected_files:
                    logger.info("Note: Selective download may not work with AppleScript method")
                return True
        
        # Method 3: Use open command (fallback)
        if not success:
            success = self._add_torrent_via_open(torrent_file)
        
        return success
    
    def _is_transmission_remote_available(self) -> bool:
        """Check if transmission-remote is available"""
        try:
            result = subprocess.run(['which', 'transmission-remote'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _add_torrent_via_remote(self, torrent_file: str, selected_files: List[Dict[str, Any]], 
                               all_files: List[Dict[str, Any]]) -> bool:
        """Add torrent via transmission-remote"""
        try:
            # Build transmission-remote command
            cmd = ['transmission-remote', '-a', torrent_file]
            
            # Add download directory if specified
            if self.config.download_folder:
                cmd.extend(['-w', self.config.download_folder])
                logger.info(f"Setting download folder to: {self.config.download_folder}")
            
            # Use transmission-remote to add torrent
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Successfully added {torrent_file} to Transmission via transmission-remote")
                
                # Set file selection if we have selected files
                if selected_files and all_files:
                    self._set_file_selection(torrent_file, selected_files, all_files)
                
                return True
            else:
                logger.debug(f"transmission-remote failed: {result.stderr}")
                return False
        except Exception as e:
            logger.debug(f"transmission-remote error: {str(e)}")
            return False
    
    def _add_torrent_via_applescript(self, torrent_file: str) -> bool:
        """Add torrent via AppleScript"""
        try:
            # Build AppleScript command
            if self.config.download_folder:
                # AppleScript to set download folder
                applescript_cmd = f'''
                tell application "Transmission"
                    if it is running then
                        set newTorrent to open POSIX file "{os.path.abspath(torrent_file)}"
                        set download folder of newTorrent to "{self.config.download_folder}"
                    else
                        activate
                        set newTorrent to open POSIX file "{os.path.abspath(torrent_file)}"
                        set download folder of newTorrent to "{self.config.download_folder}"
                    end if
                end tell
                '''
                logger.info(f"Setting download folder to: {self.config.download_folder}")
            else:
                # Standard AppleScript without custom folder
                applescript_cmd = f'''
                tell application "Transmission"
                    if it is running then
                        open POSIX file "{os.path.abspath(torrent_file)}"
                    else
                        open POSIX file "{os.path.abspath(torrent_file)}"
                        activate
                    end if
                end tell
                '''
            
            result = subprocess.run(['osascript', '-e', applescript_cmd], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Successfully added {torrent_file} to Transmission via AppleScript")
                return True
            else:
                logger.debug(f"AppleScript failed: {result.stderr}")
                return False
        except Exception as e:
            logger.debug(f"AppleScript error: {str(e)}")
            return False
    
    def _add_torrent_via_open(self, torrent_file: str) -> bool:
        """Add torrent via open command"""
        try:
            result = subprocess.run(['open', torrent_file], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Opened {torrent_file} with default application")
                return True
            else:
                logger.debug(f"open command failed: {result.stderr}")
                return False
        except Exception as e:
            logger.debug(f"open command error: {str(e)}")
            return False
    
    def _set_file_selection(self, torrent_file: str, selected_files: List[Dict[str, Any]], 
                           all_files: List[Dict[str, Any]]) -> bool:
        """Set file selection in Transmission using transmission-remote"""
        try:
            # Wait for torrent to be added
            time.sleep(3)
            
            # Get torrent ID
            torrent_id = self._find_torrent_id(selected_files)
            if not torrent_id:
                logger.warning("Could not find torrent ID")
                return False
            
            logger.info(f"Found torrent ID: {torrent_id}")
            
            # Get the selected file indices
            selected_indices = [f['index'] for f in selected_files]
            
            # First, set all files to NOT download
            for file_info in all_files:
                file_index = str(file_info['index'])
                if file_info['index'] not in selected_indices:
                    result = subprocess.run(['transmission-remote', '-t', torrent_id, '--no-get', file_index], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.debug(f"Disabled download for file: {file_info['name']}")
                    else:
                        logger.debug(f"Failed to disable file {file_index}: {result.stderr}")
            
            # Then, ensure selected files are set to download
            for file_info in selected_files:
                file_index = str(file_info['index'])
                result = subprocess.run(['transmission-remote', '-t', torrent_id, '--get', file_index], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"Enabled download for file: {file_info['name']}")
                else:
                    logger.warning(f"Failed to enable file {file_index}: {result.stderr}")
            
            # Set high priority for selected files
            for file_info in selected_files:
                file_index = str(file_info['index'])
                subprocess.run(['transmission-remote', '-t', torrent_id, '--priority-high', file_index], 
                              capture_output=True, text=True, timeout=10)
            
            logger.info(f"Successfully configured selective download for torrent {torrent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting file selection: {str(e)}")
            return False
    
    def _find_torrent_id(self, selected_files: List[Dict[str, Any]]) -> Optional[str]:
        """Find the torrent ID for the most recently added torrent"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                result = subprocess.run(['transmission-remote', '-l'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    logger.warning("Failed to get torrent list from transmission-remote")
                    time.sleep(1)
                    continue
                
                # Find torrent ID by looking for recently added torrents
                lines = result.stdout.strip().split('\n')
                # Skip header line and sum line
                torrent_lines = [line for line in lines if line.strip() and not line.startswith('Sum:') and not line.startswith('ID')]
                
                if torrent_lines:
                    # Take the last torrent (most recently added)
                    last_line = torrent_lines[-1]
                    parts = last_line.strip().split()
                    if parts and parts[0].isdigit():
                        torrent_id = parts[0]
                        logger.info(f"Using most recent torrent ID: {torrent_id}")
                        return torrent_id
                
                time.sleep(1)
                
            except Exception as e:
                logger.debug(f"Error finding torrent ID: {str(e)}")
                time.sleep(1)
                continue
        
        return None