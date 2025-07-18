#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import os

# Test credentials (same as main script)
RUTRACKER_LOGIN = 'totoskillato'
RUTRACKER_PASSWORD = 'J56ah'
DEBUG_DIR = 'debug_html'
os.makedirs(DEBUG_DIR, exist_ok=True)

def save_debug_html(content, filename):
    """Save HTML content for debugging"""
    path = os.path.join(DEBUG_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved debug HTML: {path}")

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
            save_debug_html(response.text, 'login_failed.html')
            return None
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return None

def analyze_search_page_structure(html_content):
    """Analyze the structure of search results page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("=== ANALYZING SEARCH PAGE STRUCTURE ===")
    
    # Look for tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} table(s)")
    
    for i, table in enumerate(tables):
        table_id = table.get('id', 'no-id')
        table_class = table.get('class', 'no-class')
        print(f"Table {i}: id='{table_id}', class='{table_class}'")
        
        if table_id == 'tor-tbl' or 'tor' in str(table_class):
            print(f"  -> This might be the results table!")
            
            # Analyze rows
            rows = table.find_all('tr')
            print(f"  -> Found {len(rows)} rows")
            
            for j, row in enumerate(rows[:5]):  # First 5 rows
                row_class = row.get('class', 'no-class')
                print(f"    Row {j}: class='{row_class}'")
                
                # Analyze cells
                cells = row.find_all(['td', 'th'])
                for k, cell in enumerate(cells):
                    cell_class = cell.get('class', 'no-class')
                    cell_text = cell.get_text(strip=True)[:50]  # First 50 chars
                    print(f"      Cell {k}: class='{cell_class}', text='{cell_text}'")
                    
                    # Look for links
                    links = cell.find_all('a')
                    for l, link in enumerate(links):
                        link_class = link.get('class', 'no-class')
                        link_href = link.get('href', 'no-href')
                        link_text = link.get_text(strip=True)[:30]
                        print(f"        Link {l}: class='{link_class}', href='{link_href}', text='{link_text}'")
                
                print()

def test_parsing_with_sample_query():
    """Test parsing with a simple query"""
    session = rutracker_login()
    if not session:
        print("Failed to login")
        return
    
    # Test with a simple query
    test_query = "Beatles"
    print(f"\n=== TESTING WITH QUERY: {test_query} ===")
    
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
            print(f"Search successful, response length: {len(response.text)}")
            save_debug_html(response.text, f'search_{test_query}.html')
            
            # Analyze the structure
            analyze_search_page_structure(response.text)
            
        else:
            print(f"Search failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Search error: {str(e)}")

if __name__ == "__main__":
    test_parsing_with_sample_query()