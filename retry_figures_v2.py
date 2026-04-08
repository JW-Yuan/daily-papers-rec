# -*- coding: utf-8 -*-
"""
Final retry with proper URL resolution
"""
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

output_dir = r"D:\BLTM\daily-paper-rec\papers\imgs\2026-04-08"

def get_figure_urls_fixed(arxiv_id):
    """Get figure URLs with proper base URL resolution"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Try different versions
    for version in ['', 'v1']:
        html_url = f"https://arxiv.org/html/{arxiv_id}{version}"
        try:
            print(f"  Fetching: {html_url}")
            response = requests.get(html_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                continue
            
            # Get the base URL from the current page for resolving relative URLs
            base_url = response.url  # This handles redirects
            soup = BeautifulSoup(response.text, 'html.parser')
            figure_urls = []
            
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt_text = img.get('alt', '').lower()
                
                # Match x1.png, x2.png etc
                if re.match(r'.*x\d+\.(png|jpg|jpeg|gif)', src, re.IGNORECASE):
                    # Resolve relative URLs properly
                    full_url = urljoin(base_url, src)
                    figure_urls.append({
                        'url': full_url,
                        'alt': alt_text,
                        'src': src
                    })
            
            if figure_urls:
                print(f"    Found {len(figure_urls)} figures, base_url={base_url}")
                return figure_urls
                
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    return []

def download_image(url, output_path):
    """Download an image from URL to output path"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixed retry with proper URL resolution")
    print("=" * 60)
    
    papers = [
        {"name": "C-Graph", "arxiv_id": "2512.21683"},
        {"name": "UnCoL", "arxiv_id": "2512.13101"},
    ]
    
    for paper in papers:
        name = paper['name']
        arxiv_id = paper['arxiv_id']
        
        print(f"\n[{name}] - {arxiv_id}")
        print("-" * 40)
        
        figures = get_figure_urls_fixed(arxiv_id)
        
        if not figures:
            print(f"  No figures found")
            continue
        
        # Download the first figure
        best_fig = figures[0]
        ext = os.path.splitext(best_fig['url'])[1] or '.png'
        output_file = os.path.join(output_dir, f"{name}{ext}")
        
        print(f"  Downloading: {best_fig['url']}")
        
        if download_image(best_fig['url'], output_file):
            file_size = os.path.getsize(output_file) / 1024
            print(f"  ✓ Saved: {os.path.basename(output_file)} ({file_size:.1f} KB)")
        else:
            print(f"  ✗ Failed")
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()
