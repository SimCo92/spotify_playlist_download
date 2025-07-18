#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import quote

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

def test_encoding_issue():
    """Test different encoding approaches"""
    session = rutracker_login()
    if not session:
        return
    
    # Test queries with different characters
    test_queries = [
        "Beatles Yesterday",
        "Жуки",  # Russian characters
        "Beyoncé",  # Accented characters
        "한국어",  # Korean characters
        "Pokémon"  # Mixed characters
    ]
    
    search_url = 'https://rutracker.org/forum/search.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://rutracker.org/forum/index.php'
    }
    
    for query in test_queries:
        print(f"\n=== TESTING ENCODING FOR: {query} ===")
        
        try:
            # Try different encoding methods
            methods = [
                ("windows-1251", lambda q: quote(q.encode('windows-1251'), safe='')),
                ("utf-8", lambda q: quote(q.encode('utf-8'), safe='')),
                ("utf-8 (simple)", lambda q: quote(q, safe=''))
            ]
            
            for method_name, encode_func in methods:
                try:
                    encoded_query = encode_func(query)
                    params = {'nm': encoded_query}
                    
                    response = session.get(search_url, params=params, headers=headers)
                    
                    if response.status_code == 200:
                        # Simple check - look for results table
                        if 'forumline' in response.text and 'tablesorter' in response.text:
                            print(f"  ✓ {method_name}: Success (has results table)")
                        else:
                            print(f"  ✗ {method_name}: No results table found")
                    else:
                        print(f"  ✗ {method_name}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  ✗ {method_name}: Error - {str(e)}")
                    
        except Exception as e:
            print(f"  ERROR: {str(e)}")

if __name__ == "__main__":
    test_encoding_issue()