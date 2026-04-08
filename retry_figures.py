# -*- coding: utf-8 -*-
"""
Retry downloading architecture diagrams for failed papers
"""
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

# Papers that failed or had no figures
papers = [
    {"name": "PGVMS", "arxiv_id": "2602.23292", "url": "https://arxiv.org/abs/2602.23292"},
    {"name": "C-Graph", "arxiv_id": "2512.21683", "url": "https://arxiv.org/abs/2512.21683"},
    {"name": "UnCoL", "arxiv_id": "2512.13101", "url": "https://arxiv.org/abs/2512.13101"},
    {"name": "STGR", "arxiv_id": "2604.05620", "url": "https://arxiv.org/abs/2604.05620"},
]

output_dir = r"D:\BLTM\daily-paper-rec\papers\imgs\2026-04-08"

def get_figure_urls_v2(arxiv_id, url):
    """Try multiple approaches to get figure URLs"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Try multiple URL patterns
    url_patterns = [
        f"https://arxiv.org/html/{arxiv_id}v1",
        f"https://arxiv.org/html/{arxiv_id}",
    ]
    
    for html_page_url in url_patterns:
        try:
            print(f"  Trying: {html_page_url}")
            response = requests.get(html_page_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"    Status: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            figure_urls = []
            
            # Find all figure images with various patterns
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt_text = img.get('alt', '').lower()
                
                # Check for x1.png, x2.png etc patterns
                if re.match(r'.*x\d+\.(png|jpg|jpeg|gif)', src, re.IGNORECASE):
                    full_url = urljoin(html_page_url, src)
                    figure_urls.append({
                        'url': full_url,
                        'alt': alt_text,
                        'src': src
                    })
            
            if figure_urls:
                print(f"    Found {len(figure_urls)} figure(s)")
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
        print(f"  Error downloading {url}: {e}")
        return False

def main():
    print("=" * 60)
    print("Retrying failed downloads...")
    print("=" * 60)
    
    for paper in papers:
        name = paper['name']
        arxiv_id = paper['arxiv_id']
        url = paper['url']
        
        print(f"\n[{name}] - {arxiv_id}")
        print("-" * 40)
        
        figures = get_figure_urls_v2(arxiv_id, url)
        
        if not figures:
            print(f"  No figures found with multiple attempts")
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
            print(f"  ✗ Failed to download")
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()
