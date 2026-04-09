import urllib.request
import os
import re
import time

save_dir = 'D:/BLTM/daily-paper-rec/papers/imgs/2026-04-09'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'}

for v in ['v2', 'v1', '']:
    ver = v if v else ''
    url = f'https://arxiv.org/html/2604.04470{ver}'
    print(f'Trying {url}...')
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        pattern = r'src=["\']([^"\']+\.(png|jpg|jpeg))["\']'
        imgs = re.findall(pattern, html, re.IGNORECASE)
        print(f'  Found {len(imgs)} images')
        for img, _ in imgs[:5]:
            print(f'    {img}')
        if imgs:
            # Try to download first one
            img_url = imgs[0][0]
            if not img_url.startswith('http'):
                base = 'https://arxiv.org/html/2604.04470/'
                img_url = base + img_url
            req2 = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=20) as resp2:
                data = resp2.read()
            if len(data) > 15000:
                save_path = os.path.join(save_dir, 'MC-GenRef.png')
                with open(save_path, 'wb') as f:
                    f.write(data)
                print(f'  Downloaded MC-GenRef.png ({len(data)//1024}KB)')
            break
    except Exception as e:
        print(f'  Error: {e}')
    time.sleep(1)
