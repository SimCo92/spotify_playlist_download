"""
Torrent file analysis utilities
"""

import bencodepy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TorrentAnalyzer:
    """Analyzer for torrent file contents"""
    
    def analyze_torrent_contents(self, torrent_file: str) -> List[Dict[str, Any]]:
        """Analyze torrent file contents and return file list"""
        try:
            with open(torrent_file, 'rb') as f:
                torrent_data = bencodepy.decode(f.read())
            
            files = []
            
            # Handle single file torrents
            if b'files' not in torrent_data[b'info']:
                # Single file torrent
                name = torrent_data[b'info'][b'name'].decode('utf-8')
                length = torrent_data[b'info'][b'length']
                files.append({
                    'index': 0,
                    'path': name,
                    'length': length,
                    'name': name
                })
            else:
                # Multi-file torrent
                for index, file_info in enumerate(torrent_data[b'info'][b'files']):
                    # Build file path
                    path_parts = [part.decode('utf-8') for part in file_info[b'path']]
                    full_path = '/'.join(path_parts)
                    filename = path_parts[-1]
                    length = file_info[b'length']
                    
                    files.append({
                        'index': index,
                        'path': full_path,
                        'length': length,
                        'name': filename
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Error analyzing torrent contents: {str(e)}")
            return []
    
    def get_torrent_info(self, torrent_file: str) -> Dict[str, Any]:
        """Get basic torrent information"""
        try:
            with open(torrent_file, 'rb') as f:
                torrent_data = bencodepy.decode(f.read())
            
            info = {
                'name': torrent_data[b'info'][b'name'].decode('utf-8'),
                'announce': torrent_data.get(b'announce', b'').decode('utf-8'),
                'comment': torrent_data.get(b'comment', b'').decode('utf-8'),
                'created_by': torrent_data.get(b'created by', b'').decode('utf-8'),
                'creation_date': torrent_data.get(b'creation date', 0),
                'is_private': torrent_data[b'info'].get(b'private', 0) == 1,
                'piece_length': torrent_data[b'info'].get(b'piece length', 0),
            }
            
            # Calculate total size
            if b'files' in torrent_data[b'info']:
                total_size = sum(file_info[b'length'] for file_info in torrent_data[b'info'][b'files'])
            else:
                total_size = torrent_data[b'info'][b'length']
            
            info['total_size'] = total_size
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting torrent info: {str(e)}")
            return {}