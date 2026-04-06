"""
下载2026-04-06论文的架构图
"""

import os
import requests
from PIL import Image
import io

DATE = "2026-04-06"
BASE_DIR = r"D:\BLTM\daily-paper-rec\papers\imgs"
OUT_DIR = os.path.join(BASE_DIR, DATE)
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}

MIN_WIDTH = 400
MIN_HEIGHT = 200

# 今天的论文架构图URL（通过分析arXiv HTML和GitHub获取）
PAPERS = [
    {
        "name": "VGGT",
        "urls": [
            "https://arxiv.org/html/2508.12537v1/x1.png",
            "https://arxiv.org/html/2508.12537v1/x2.png",
            "https://arxiv.org/html/2508.12537v1/x3.png",
        ]
    },
    {
        "name": "MIMO",
        "urls": [
            "https://arxiv.org/html/2510.10011v1/x2.png",
        ]
    },
    {
        "name": "ExGra-Med",
        "urls": [
            "https://arxiv.org/html/2502.06154v1/x1.png",
            "https://arxiv.org/html/2502.06154v1/x2.png",
            "https://arxiv.org/html/2502.06154v1/x3.png",
        ]
    },
    {
        "name": "Pancakes",
        "urls": [
            "https://arxiv.org/html/2508.07465v1/x2.png",
        ]
    },
    {
        "name": "Curia-2",
        "urls": [
            "https://arxiv.org/html/2604.01987v1/x1.png",
            "https://arxiv.org/html/2604.01987v1/x2.png",
            "https://arxiv.org/html/2604.01987v1/x3.png",
        ]
    },
    {
        "name": "SPAR",
        "urls": [
            "https://arxiv.org/html/2604.02252v1/x1.png",
            "https://arxiv.org/html/2604.02252v1/x2.png",
            "https://arxiv.org/html/2604.02252v1/x3.png",
        ]
    },
    {
        "name": "VisionUnite",
        "urls": [
            "https://arxiv.org/html/2508.02371v1/x1.png",
            "https://arxiv.org/html/2508.02371v1/x2.png",
            "https://arxiv.org/html/2508.02371v1/x3.png",
        ]
    },
    {
        "name": "EviVLM",
        "urls": [
            "https://arxiv.org/html/2508.02924v1/x1.png",
            "https://arxiv.org/html/2508.02924v1/x2.png",
            "https://arxiv.org/html/2508.02924v1/x3.png",
        ]
    },
    {
        "name": "VoCo",
        "urls": [
            "https://arxiv.org/html/2508.01319v1/x1.png",
            "https://arxiv.org/html/2508.01319v1/x2.png",
            "https://arxiv.org/html/2508.01319v1/x3.png",
        ]
    },
]

results = []

for paper in PAPERS:
    name = paper["name"]
    downloaded = False
    
    for url in paper["urls"]:
        try:
            print(f"[{name}] 尝试下载: {url}")
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            
            # 验证图片
            img = Image.open(io.BytesIO(resp.content))
            w, h = img.size
            fmt = img.format or "PNG"
            
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                print(f"  ✗ 图片太小 ({w}x{h})，跳过")
                continue
            
            # 确定扩展名
            ext = fmt.lower()
            if ext == "jpeg":
                ext = "jpg"
            elif ext not in ("png", "jpg", "gif", "webp"):
                ext = "png"
            
            out_path = os.path.join(OUT_DIR, f"{name}.{ext}")
            with open(out_path, "wb") as f:
                f.write(resp.content)
            
            print(f"  ✓ 保存成功: {out_path} ({w}x{h}, {fmt})")
            results.append({"name": name, "path": out_path, "size": f"{w}x{h}", "status": "OK"})
            downloaded = True
            break
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
    
    if not downloaded:
        print(f"  ✗ [{name}] 所有URL均失败")
        results.append({"name": name, "path": None, "size": None, "status": "FAILED"})

print("\n========== 下载结果汇总 ==========")
for r in results:
    status = "✓" if r["status"] == "OK" else "✗"
    print(f"{status} {r['name']}: {r['path'] or 'FAILED'} {r['size'] or ''}")

print(f"\n共下载成功 {sum(1 for r in results if r['status'] == 'OK')}/{len(results)} 张架构图")
print(f"保存目录: {OUT_DIR}")
