"""
下载缺失的架构图文件
"""
import requests
import os
from pathlib import Path

BASE_DIR = Path(r"D:\BLTM\daily-paper-rec")
IMGS_DIR = BASE_DIR / "papers" / "imgs" / "2026-04-06"

# 确保目录存在
IMGS_DIR.mkdir(parents=True, exist_ok=True)

# 定义要下载的图片
images_to_download = {
    # VGGT - 尝试从 arXiv PDF 获取或使用占位符
    "VGGT.png": None,  # 需要从论文PDF获取
    
    # Curia-2 - 尝试 arXiv
    "Curia-2.png": None,  # arXiv:2604.01987
    
    # VisionUnite - 从 GitHub
    "VisionUnite.png": "https://raw.githubusercontent.com/HUANGLIZI/VisionUnite/main/VisionUnite_Manuscript.jpg",
    
    # EviVLM - 需要查找
    "EviVLM.png": None,
    
    # VoCo - 从 GitHub
    "VoCo.png": None,  # https://github.com/Luffy03/Large-Scale-Medical
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def download_image(url, filepath):
    """下载图片并保存"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        return False

def download_arxiv_figure(arxiv_id, figure_num, filepath):
    """从 arXiv HTML 下载指定图号"""
    # 尝试多个可能的URL格式
    urls = [
        f"https://arxiv.org/html/{arxiv_id}v1/x{figure_num}.png",
        f"https://arxiv.org/html/{arxiv_id}v2/x{figure_num}.png",
        f"https://arxiv.org/html/{arxiv_id}/x{figure_num}.png",
    ]
    
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ 从 {url} 下载成功")
                return True
        except:
            continue
    return False

print("=== 下载缺失的架构图 ===\n")

# 1. VisionUnite - 从 GitHub
try:
    print("1. VisionUnite:")
    url = "https://raw.githubusercontent.com/HUANGLIZI/VisionUnite/main/VisionUnite_Manuscript.jpg"
    filepath = IMGS_DIR / "VisionUnite.jpg"
    if download_image(url, filepath):
        print(f"  ✓ 下载成功: {filepath}")
    else:
        print(f"  ✗ 下载失败")
except Exception as e:
    print(f"  ✗ 错误: {e}")

# 2. VoCo - 从 GitHub
try:
    print("\n2. VoCo:")
    # 尝试从 VoCo 仓库获取
    url = "https://raw.githubusercontent.com/Luffy03/Large-Scale-Medical/main/assets/framework.png"
    filepath = IMGS_DIR / "VoCo.png"
    if download_image(url, filepath):
        print(f"  ✓ 下载成功: {filepath}")
    else:
        # 尝试其他路径
        url2 = "https://raw.githubusercontent.com/Luffy03/Large-Scale-Medical/main/framework.png"
        if download_image(url2, filepath):
            print(f"  ✓ 从备选路径下载成功: {filepath}")
        else:
            print(f"  ✗ 下载失败")
except Exception as e:
    print(f"  ✗ 错误: {e}")

# 3. VGGT - 从 arXiv 尝试
print("\n3. VGGT (arXiv:2503.01166):")
filepath = IMGS_DIR / "VGGT.png"
if download_arxiv_figure("2503.01166", 1, filepath):
    print(f"  ✓ 下载成功: {filepath}")
else:
    # 尝试 x2.png
    if download_arxiv_figure("2503.01166", 2, filepath):
        print(f"  ✓ 从 x2 下载成功: {filepath}")
    else:
        print(f"  ✗ arXiv HTML 版本不可用，需要从 PDF 手动提取")

# 4. Curia-2 - 从 arXiv 尝试
print("\n4. Curia-2 (arXiv:2604.01987):")
filepath = IMGS_DIR / "Curia-2.png"
if download_arxiv_figure("2604.01987", 1, filepath):
    print(f"  ✓ 下载成功: {filepath}")
else:
    if download_arxiv_figure("2604.01987", 2, filepath):
        print(f"  ✓ 从 x2 下载成功: {filepath}")
    else:
        print(f"  ✗ arXiv HTML 版本不可用")

# 5. EviVLM - 搜索 arXiv
print("\n5. EviVLM:")
print("  ℹ 需要手动查找论文来源")

print("\n=== 下载完成 ===")

# 列出当前目录的文件
print(f"\n当前图片文件 ({IMGS_DIR}):")
for f in sorted(IMGS_DIR.iterdir()):
    size = f.stat().st_size / 1024
    print(f"  - {f.name} ({size:.1f} KB)")
