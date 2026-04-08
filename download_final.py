# -*- coding: utf-8 -*-
"""
Final download with correct URL construction
"""
import os
import requests
from bs4 import BeautifulSoup
import re
import time

output_dir = r"D:\BLTM\daily-paper-rec\papers\imgs\2026-04-08"

def get_and_download_figures(arxiv_id, name):
    """Get and download figures with correct URL construction"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for version in ['v1', '']:
        html_url = f"https://arxiv.org/html/{arxiv_id}{version}"
        try:
            print(f"  Fetching: {html_url}")
            response = requests.get(html_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Build the correct base URL manually
            base_url = html_url.rstrip('/') + '/'
            
            figures = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt_text = img.get('alt', '').lower()
                
                if re.match(r'x\d+\.(png|jpg|jpeg|gif)', src, re.IGNORECASE):
                    # Construct full URL manually
                    full_url = base_url + src
                    figures.append({
                        'url': full_url,
                        'alt': alt_text,
                        'src': src
                    })
            
            if figures:
                print(f"    Found {len(figures)} figures")
                
                # Download the first figure
                best_fig = figures[0]
                ext = os.path.splitext(best_fig['url'])[1] or '.png'
                output_file = os.path.join(output_dir, f"{name}{ext}")
                
                print(f"    Downloading: {best_fig['url']}")
                
                img_response = requests.get(best_fig['url'], headers=headers, timeout=30)
                img_response.raise_for_status()
                
                with open(output_file, 'wb') as f:
                    f.write(img_response.content)
                
                file_size = os.path.getsize(output_file) / 1024
                print(f"    ✓ Saved: {os.path.basename(output_file)} ({file_size:.1f} KB)")
                return True
                
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    return False

def main():
    print("=" * 60)
    print("Final download with correct URL construction")
    print("=" * 60)
    
    papers = [
        {"name": "C-Graph", "arxiv_id": "2512.21683"},
        {"name": "UnCoL", "arxiv_id": "2512.13101"},
        {"name": "PGVMS", "arxiv_id": "2602.23292"},
        {"name": "STGR", "arxiv_id": "2604.05620"},
    ]
    
    success_count = 0
    
    for paper in papers:
        name = paper['name']
        arxiv_id = paper['arxiv_id']
        
        print(f"\n[{name}] - {arxiv_id}")
        print("-" * 40)
        
        if get_and_download_figures(arxiv_id, name):
            success_count += 1
        else:
            print(f"    ✗ Failed - no figures available")
        
        time.sleep(0.5)
    
    print(f"\n{'=' * 60}")
    print(f"Additional downloads: {success_count}/4")

if __name__ == "__main__":
    main()
