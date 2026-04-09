import urllib.request
import os
import re
import time

save_dir = 'D:/BLTM/daily-paper-rec/papers/imgs/2026-04-09'
os.makedirs(save_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'
}

def fetch_html(arxiv_id):
    url = f'https://arxiv.org/html/{arxiv_id}v1'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='ignore'), url
    except Exception as e:
        print(f'Error fetching {arxiv_id}: {e}')
        return '', ''

def find_figure_imgs(html, base_page_url):
    # Find image src attributes - relative and absolute
    pattern = r'<img[^>]+src=["\']([^"\']+\.(png|jpg|jpeg))["\']'
    imgs = re.findall(pattern, html, re.IGNORECASE)
    results = []
    for img_url, ext in imgs:
        if any(x in img_url.lower() for x in ['icon', 'logo', 'avatar', 'button', 'favicon']):
            continue
        # Build absolute URL
        if img_url.startswith('http'):
            abs_url = img_url
        elif img_url.startswith('//'):
            abs_url = 'https:' + img_url
        elif img_url.startswith('/'):
            abs_url = 'https://arxiv.org' + img_url
        else:
            # Relative to page URL base dir
            base_dir = base_page_url.rsplit('/', 1)[0] + '/'
            abs_url = base_dir + img_url
        results.append(abs_url)
    return results

def download_img(img_url, save_path):
    req = urllib.request.Request(img_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) > 15000:  # At least 15KB for a real figure
            with open(save_path, 'wb') as f:
                f.write(data)
            print(f'  Downloaded: {os.path.basename(save_path)} ({len(data)//1024}KB)')
            return True
        else:
            print(f'  Too small ({len(data)} bytes), skipped: {img_url[-60:]}')
            return False
    except Exception as e:
        print(f'  Error: {str(e)[:80]}')
        return False

# Papers to process
papers = [
    ('GCNV-Net', '2604.05515'),
    ('MuPAD', '2604.03635'),
    ('CardiacAgent', '2604.04078'),
    ('TAPE', '2604.04571'),
    ('MEDIC-AD', '2603.27176'),
    ('CARE', '2603.01607'),
    ('SPEGC', '2603.11492'),
    ('PathChat-SegR1', ''),  # ICLR - no arxiv HTML
]

results = {}

for name, arxiv_id in papers:
    if not arxiv_id:
        print(f'\n{name}: No arXiv ID, skipping')
        results[name] = 'no_arxiv'
        continue
    
    print(f'\nProcessing {name} ({arxiv_id})...')
    html, page_url = fetch_html(arxiv_id)
    if not html:
        results[name] = 'fetch_failed'
        continue
    
    imgs = find_figure_imgs(html, page_url)
    print(f'  Found {len(imgs)} candidate images')
    for u in imgs[:3]:
        print(f'    {u[-80:]}')
    
    if not imgs:
        results[name] = 'no_images'
        continue
    
    save_path = os.path.join(save_dir, f'{name}.png')
    
    downloaded = False
    for img_url in imgs[:8]:
        if download_img(img_url, save_path):
            results[name] = 'success'
            downloaded = True
            break
        time.sleep(0.3)
    
    if not downloaded:
        results[name] = 'download_failed'
    
    time.sleep(1.5)

# MC-GenRef special case - 2604.04470 which had HTTP error earlier
print(f'\nProcessing MC-GenRef (2604.04470)...')
html, page_url = fetch_html('2604.04470')
if html:
    imgs = find_figure_imgs(html, page_url)
    print(f'  Found {len(imgs)} images')
    save_path = os.path.join(save_dir, 'MC-GenRef.png')
    downloaded = False
    for img_url in imgs[:8]:
        if download_img(img_url, save_path):
            results['MC-GenRef'] = 'success'
            downloaded = True
            break
        time.sleep(0.3)
    if not downloaded:
        results['MC-GenRef'] = 'download_failed'
else:
    results['MC-GenRef'] = 'fetch_failed'

print('\n=== Summary ===')
for name, status in results.items():
    print(f'{name}: {status}')
