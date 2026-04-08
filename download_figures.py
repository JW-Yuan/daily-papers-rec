# -*- coding: utf-8 -*-
"""
Download architecture diagrams for CV/VLM/Medical AI papers
"""
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time

# Paper list with arXiv IDs and model abbreviations
papers = [
    # Conference papers
    {"name": "MASS", "arxiv_id": "2603.13660", "url": "https://arxiv.org/abs/2603.13660"},
    {"name": "MedCBR", "arxiv_id": "2603.08921", "url": "https://arxiv.org/abs/2603.08921"},
    {"name": "LUMOS", "arxiv_id": "2604.05388", "url": "https://arxiv.org/abs/2604.05388"},
    # Journal papers
    {"name": "PGVMS", "arxiv_id": "2602.23292", "url": "https://arxiv.org/abs/2602.23292"},
    {"name": "C-Graph", "arxiv_id": "2512.21683", "url": "https://arxiv.org/abs/2512.21683"},
    {"name": "UnCoL", "arxiv_id": "2512.13101", "url": "https://arxiv.org/abs/2512.13101"},
    # arXiv papers
    {"name": "HaloProbe", "arxiv_id": "2604.06165", "url": "https://arxiv.org/abs/2604.06165"},
    {"name": "STGR", "arxiv_id": "2604.05620", "url": "https://arxiv.org/abs/2604.05620"},
    {"name": "CRISP", "arxiv_id": "2604.05409", "url": "https://arxiv.org/abs/2604.05409"},
]

output_dir = r"D:\BLTM\daily-paper-rec\papers\imgs\2026-04-08"

def sanitize_filename(name):
    """Sanitize filename to remove invalid characters"""
    return re.sub(r'[<>:"/\\|?*]', '-', name)

def get_figure_urls(html_url):
    """Extract figure URLs from arXiv HTML page"""
    try:
        # Get the HTML version of the paper
        html_page_url = html_url.replace("/abs/", "/html/") + "v1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(html_page_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        figure_urls = []
        
        # Find all figure images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            # Look for figure images (x1.png, x2.png, etc.)
            if re.match(r'.*x\d+\.(png|jpg|jpeg|gif)', src, re.IGNORECASE):
                full_url = urljoin(html_page_url, src)
                alt_text = img.get('alt', '').lower()
                figure_urls.append({
                    'url': full_url,
                    'alt': alt_text,
                    'src': src
                })
        
        return figure_urls
    except Exception as e:
        print(f"  Error fetching {html_page_url}: {e}")
        return []

def is_architecture_diagram(alt_text, src):
    """Check if the figure is likely an architecture diagram (not a chart/statistic)"""
    alt_lower = alt_text.lower()
    src_lower = src.lower()
    
    # Keywords suggesting it's an architecture/method diagram
    arch_keywords = [
        'architecture', 'framework', 'pipeline', 'overview', 'structure',
        'model', 'method', 'approach', 'diagram', 'system', 'workflow',
        'block', 'module', 'network', 'architecture', 'schematic',
        'figure', 'illustration', 'architecture'
    ]
    
    # Keywords suggesting it's a statistical chart (to exclude)
    stat_keywords = [
        'accuracy', 'precision', 'recall', 'f1', 'score', 'curve',
        'plot', 'chart', 'graph', 'distribution', 'histogram', 'bar',
        'box', 'confusion', 'matrix', 'heatmap', 'roc', 'auc',
        'loss', 'training', 'validation', 'test', 'comparison',
        'result', 'performance', 'baseline', 'benchmark',
        'dice', 'iou', 'hausdorff', 'sensitivity', 'specificity'
    ]
    
    # Check for architecture indicators
    has_arch_keyword = any(kw in alt_lower for kw in arch_keywords)
    
    # Check for statistical indicators
    has_stat_keyword = any(kw in alt_lower for kw in stat_keywords)
    
    # Also check src for clues
    src_has_arch = any(kw in src_lower for kw in ['arch', 'framework', 'pipeline', 'model', 'method'])
    src_has_stat = any(kw in src_lower for kw in ['acc', 'loss', 'curve', 'plot'])
    
    # Logic: If it has arch keywords and no stat keywords, it's likely an architecture diagram
    # If it has stat keywords, it's likely a chart (exclude)
    # Priority: architecture diagrams > charts
    
    # Exclude if it's clearly a statistical chart
    if has_stat_keyword and not has_arch_keyword:
        return False
    
    # Prefer if it has architecture keywords
    if has_arch_keyword:
        return True
    
    # Default: include (download and let user decide)
    return True

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
    print("Downloading architecture diagrams for 2026-04-08 papers")
    print("=" * 60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for paper in papers:
        name = paper['name']
        arxiv_id = paper['arxiv_id']
        url = paper['url']
        
        print(f"\n[{name}] - {arxiv_id}")
        print("-" * 40)
        
        # Get figure URLs from arXiv HTML
        figures = get_figure_urls(url)
        
        if not figures:
            print(f"  No figures found on arXiv page")
            results.append({"name": name, "status": "no_figures", "file": None})
            continue
        
        print(f"  Found {len(figures)} figure(s)")
        
        # Filter for architecture diagrams (not statistical charts)
        arch_figures = [f for f in figures if is_architecture_diagram(f['alt'], f['src'])]
        
        if not arch_figures:
            print(f"  All figures appear to be statistical charts (excluding)")
            results.append({"name": name, "status": "charts_only", "file": None})
            continue
        
        print(f"  Found {len(arch_figures)} potential architecture diagram(s)")
        
        # Download the first architecture diagram
        best_fig = arch_figures[0]
        ext = os.path.splitext(best_fig['url'])[1] or '.png'
        output_file = os.path.join(output_dir, f"{name}{ext}")
        
        print(f"  Downloading: {best_fig['url']}")
        print(f"  Alt text: {best_fig['alt'][:80] if best_fig['alt'] else 'N/A'}...")
        
        if download_image(best_fig['url'], output_file):
            file_size = os.path.getsize(output_file) / 1024
            print(f"  ✓ Saved: {os.path.basename(output_file)} ({file_size:.1f} KB)")
            results.append({"name": name, "status": "success", "file": output_file})
        else:
            results.append({"name": name, "status": "failed", "file": None})
        
        time.sleep(0.5)  # Be polite to arXiv
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    success = sum(1 for r in results if r['status'] == 'success')
    no_fig = sum(1 for r in results if r['status'] in ['no_figures', 'charts_only'])
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"✓ Success: {success}/9")
    print(f"✗ No architecture diagram: {no_fig}/9")
    print(f"✗ Failed: {failed}/9")
    
    print("\nDownloaded files:")
    for r in results:
        if r['file']:
            print(f"  - {os.path.basename(r['file'])}")
    
    print(f"\nOutput directory: {output_dir}")

if __name__ == "__main__":
    main()
