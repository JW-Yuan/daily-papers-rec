# -*- coding: utf-8 -*-
"""
Debug - print actual figure URLs from HTML
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def debug_figure_urls(arxiv_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for version in ['v1', '']:
        html_url = f"https://arxiv.org/html/{arxiv_id}{version}"
        try:
            print(f"\nFetching: {html_url}")
            response = requests.get(html_url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Final URL (after redirect): {response.url}")
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get base URL for resolving relative paths
            base_url = response.url
            
            print(f"\nAll images found:")
            for i, img in enumerate(soup.find_all('img')[:15]):  # First 15 images
                src = img.get('src', '')
                alt = img.get('alt', '')[:50]
                
                # Check if it's a figure (x1.png, x2.png, etc.)
                if re.match(r'.*x\d+\.(png|jpg|jpeg|gif)', src, re.IGNORECASE):
                    # Resolve relative URL
                    full_url = urljoin(base_url, src)
                    print(f"  [{i}] src='{src}'")
                    print(f"      resolved='{full_url}'")
                    print(f"      alt='{alt}...'")
            
            return
            
        except Exception as e:
            print(f"Error: {e}")
            continue

print("=" * 60)
print("C-Graph Debug")
print("=" * 60)
debug_figure_urls("2512.21683")

print("\n" + "=" * 60)
print("UnCoL Debug")
print("=" * 60)
debug_figure_urls("2512.13101")
