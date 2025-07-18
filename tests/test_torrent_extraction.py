#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
import os
import subprocess

# Test credentials
RUTRACKER_LOGIN = 'totoskillato'
RUTRACKER_PASSWORD = 'J56ah'

def rutracker_login():
    """Log in to Rutracker and return authenticated session"""
    print("Logging in to Rutracker...")
    session = requests.Session()
    login_url = 'https://rutracker.org/forum/login.php'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://rutracker.org/forum/index.php'
        }
        response = session.get(login_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        login_data = {
            'login_username': RUTRACKER_LOGIN,
            'login_password': RUTRACKER_PASSWORD,
            'login': 'Вход'
        }
        
        for hidden in soup.select('input[type=hidden]'):
            if hidden.get('name') and hidden.get('value'):
                login_data[hidden['name']] = hidden['value']
        
        response = session.post(login_url, data=login_data, headers=headers)
        
        if RUTRACKER_LOGIN in response.text:
            print("Login successful")
            return session
        else:
            print("Login failed")
            return None
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return None

def extract_torrent_download_url(session, torrent_page_url):
    """Extract the torrent download URL from a RuTracker page"""
    print(f"Analyzing torrent page: {torrent_page_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://rutracker.org/forum/index.php'
        }
        
        response = session.get(torrent_page_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page: HTTP {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the page for analysis
        with open('debug_torrent_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved torrent page to debug_torrent_page.html")
        
        # Look for the specific download link pattern used by RuTracker
        # The link is usually in the format: dl.php?t=TOPIC_ID
        
        # Method 1: Find the download link using CSS selectors
        download_link = soup.find('a', {'class': 'dl-link'})
        if download_link:
            href = download_link.get('href')
            if href:
                if not href.startswith('http'):
                    href = 'https://rutracker.org/forum/' + href
                print(f"Found download link: {href}")
                return href
        
        # Method 2: Look for dl.php links in the HTML
        dl_links = soup.find_all('a', href=re.compile(r'dl\.php\?t=\d+'))
        if dl_links:
            href = dl_links[0].get('href')
            if not href.startswith('http'):
                href = 'https://rutracker.org/forum/' + href
            print(f"Found dl.php link: {href}")
            return href
        
        # Method 3: Extract topic ID from URL and construct download link
        topic_id_match = re.search(r't=(\d+)', torrent_page_url)
        if topic_id_match:
            topic_id = topic_id_match.group(1)
            constructed_url = f'https://rutracker.org/forum/dl.php?t={topic_id}'
            print(f"Constructed download link: {constructed_url}")
            return constructed_url
        
        print("No download links found")
        return None
            
    except Exception as e:
        print(f"Error extracting download URL: {str(e)}")
        return None

def download_torrent_file(session, download_url, filename):
    """Download a torrent file"""
    print(f"Downloading torrent: {download_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://rutracker.org/forum/index.php'
        }
        
        response = session.get(download_url, headers=headers)
        
        if response.status_code == 200:
            # Check if it's actually a torrent file
            if response.headers.get('content-type') == 'application/x-bittorrent' or filename.endswith('.torrent'):
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded torrent file: {filename}")
                return filename
            else:
                print(f"Response doesn't appear to be a torrent file")
                print(f"Content-Type: {response.headers.get('content-type')}")
                return None
        else:
            print(f"Download failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error downloading torrent: {str(e)}")
        return None

def open_with_transmission(torrent_file):
    """Open torrent file with Transmission on macOS"""
    print(f"Opening {torrent_file} with Transmission...")
    
    try:
        # Check if Transmission is installed
        transmission_paths = [
            '/Applications/Transmission.app/Contents/MacOS/Transmission',
            '/usr/local/bin/transmission-gtk',
            '/opt/homebrew/bin/transmission-gtk'
        ]
        
        transmission_cmd = None
        for path in transmission_paths:
            if os.path.exists(path):
                transmission_cmd = path
                break
        
        if transmission_cmd:
            subprocess.run([transmission_cmd, torrent_file])
            print(f"Opened {torrent_file} with Transmission")
            return True
        else:
            # Try using open command (macOS default)
            subprocess.run(['open', torrent_file])
            print(f"Opened {torrent_file} with default application")
            return True
            
    except Exception as e:
        print(f"Error opening with Transmission: {str(e)}")
        return False

def test_torrent_extraction():
    """Test the torrent extraction workflow"""
    session = rutracker_login()
    if not session:
        return
    
    # Use a sample torrent page URL (you can get this from previous search results)
    test_url = "https://rutracker.org/forum/viewtopic.php?t=6627272"  # John Lennon - Imagine
    
    print(f"\n=== TESTING TORRENT EXTRACTION ===")
    print(f"Test URL: {test_url}")
    
    # Extract download URL
    download_url = extract_torrent_download_url(session, test_url)
    
    if download_url:
        print(f"✓ Found download URL: {download_url}")
        
        # Download the torrent file
        torrent_filename = "test_torrent.torrent"
        downloaded_file = download_torrent_file(session, download_url, torrent_filename)
        
        if downloaded_file:
            print(f"✓ Downloaded: {downloaded_file}")
            
            # Test opening with Transmission
            if open_with_transmission(downloaded_file):
                print("✓ Successfully opened with Transmission")
            else:
                print("✗ Failed to open with Transmission")
        else:
            print("✗ Failed to download torrent file")
    else:
        print("✗ No download URL found")

if __name__ == "__main__":
    test_torrent_extraction()