#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import os

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
        if response.status_code != 200:
            print(f"Login page failed: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        login_data = {
            'login_username': RUTRACKER_LOGIN,
            'login_password': RUTRACKER_PASSWORD,
            'login': 'Вход'
        }
        
        # Find all hidden input fields
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

def parse_rutracker_results(html):
    """Parse Rutracker search results from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Find results table - correct selector based on actual HTML structure
    table = soup.find('table', class_=lambda c: c and 'forumline' in c and 'tablesorter' in c)
    if not table:
        print("No results table found")
        return results
    
    # Process each result row
    tbody = table.find('tbody')
    if not tbody:
        print("No tbody found in results table")
        return results
        
    for row in tbody.find_all('tr', class_=lambda c: c and 'tCenter' in c):
        try:
            # Find the title cell (3rd column, index 2)
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
                
            title_cell = cells[2]  # Third column contains the title
            
            # Find the topic link inside the topictitle div
            topictitle_div = title_cell.find('div', class_='topictitle')
            if not topictitle_div:
                continue
                
            # Find the anchor tag with the topic link
            title_tag = topictitle_div.find('a', class_='topictitle')
            if not title_tag:
                continue
                    
            title = title_tag.get_text(strip=True)
            relative_link = title_tag.get('href')
            
            # Handle relative URLs
            if relative_link.startswith('viewtopic.php'):
                link = 'https://rutracker.org/forum/' + relative_link
            elif relative_link.startswith('/forum/viewtopic.php'):
                link = 'https://rutracker.org' + relative_link
            else:
                link = relative_link
            
            # Determine quality
            quality = 'lossy'
            if re.search(r'\b(FLAC|APE|WAV|24bit|lossless|无损)\b', title, re.IGNORECASE):
                quality = 'lossless'
            
            # Determine type
            result_type = 'single'
            if re.search(r'\b(album|дискография|сборник|collection|disc|LP|EP|CD|box)\b', title, re.IGNORECASE):
                result_type = 'album'
                
            # Calculate priority
            priority = 1
            if quality == 'lossless' and result_type == 'single':
                priority = 4
            elif quality == 'lossless' and result_type == 'album':
                priority = 3
            elif quality == 'lossy' and result_type == 'single':
                priority = 2
                
            results.append({
                'title': title,
                'link': link,
                'quality': quality,
                'type': result_type,
                'priority': priority
            })
        except Exception as e:
            print(f"Error parsing result row: {str(e)}")
            continue
    
    return results

def test_fixed_parsing():
    """Test the fixed parsing function"""
    session = rutracker_login()
    if not session:
        return
    
    # Test with a simple query
    test_query = "Beatles"
    print(f"\n=== TESTING FIXED PARSING WITH QUERY: {test_query} ===")
    
    search_url = 'https://rutracker.org/forum/search.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://rutracker.org/forum/index.php'
    }
    
    try:
        from urllib.parse import quote
        encoded_query = quote(test_query.encode('windows-1251'), safe='')
        params = {'nm': encoded_query}
        
        response = session.get(search_url, params=params, headers=headers)
        
        if response.status_code == 200:
            print(f"Search successful")
            
            # Parse results
            results = parse_rutracker_results(response.text)
            
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results[:5]):  # Show first 5 results
                print(f"\n{i+1}. {result['title']}")
                print(f"   Link: {result['link']}")
                print(f"   Quality: {result['quality']}, Type: {result['type']}, Priority: {result['priority']}")
                
        else:
            print(f"Search failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Search error: {str(e)}")

if __name__ == "__main__":
    test_fixed_parsing()