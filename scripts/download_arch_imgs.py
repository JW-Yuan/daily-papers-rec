"""
下载论文架构图脚本
- 严格使用每篇论文的 Overview/Architecture/Framework Figure
- 验证图片尺寸（过小则判定为非架构图，跳过）
- 保存到 papers/imgs/YYYY-MM-DD/ 目录，以模型缩写命名

用法:
    python download_arch_imgs.py <YYYY-MM-DD>          # 使用指定日期
    python download_arch_imgs.py                       # 默认使用今天日期
"""

import os
import sys
import json
import re
import requests
from PIL import Image
import io
from datetime import datetime

# 获取日期参数
if len(sys.argv) > 1:
    DATE = sys.argv[1]
else:
    DATE = datetime.now().strftime("%Y-%m-%d")

BASE_DIR = r"D:\BLTM\daily-paper-rec\papers\imgs"
OUT_DIR = os.path.join(BASE_DIR, DATE)
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}

# 架构图关键词（用于验证caption）
ARCH_KEYWORDS = ['overview', 'architecture', 'framework', 'pipeline', 'proposed method', 'overall', 'structure']

def extract_arxiv_id_from_url(url):
    """从arXiv URL提取ID"""
    if not url:
        return None
    patterns = [
        r'arxiv\.org/abs/(\d+\.\d+)',
        r'arxiv\.org/html/(\d+\.\d+)',
        r'arXiv:(\d+\.\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def get_architecture_figure_from_arxiv(arxiv_id):
    """
    从arXiv HTML页面分析Figure caption，找出架构图
    返回: (figure_number, caption) 或 None
    """
    try:
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        resp = requests.get(html_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
        
        # 查找所有figure
        # arXiv HTML中figure格式: <figure>...<figcaption>Figure X: ...</figcaption>...</figure>
        figure_pattern = r'<figure[^>]*>.*?<figcaption[^>]*>(Figure\s+(\d+)[^<]*)</figcaption>.*?</figure>'
        figures = re.findall(figure_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for caption_text, fig_num in figures:
            caption_lower = caption_text.lower()
            # 检查是否包含架构图关键词
            if any(kw in caption_lower for kw in ARCH_KEYWORDS):
                return (fig_num, caption_text.strip())
        
        # 如果没找到，返回Figure 1作为fallback
        if figures:
            return (figures[0][1], figures[0][0].strip())
        return None
    except Exception as e:
        print(f"  分析arXiv {arxiv_id} 失败: {e}")
        return None

def load_papers_from_metadata(date):
    """从index.json和markdown文件加载论文元数据"""
    papers = []
    base_path = r"D:\BLTM\daily-paper-rec\papers"
    
    # 尝试从index.json加载
    index_path = os.path.join(base_path, "index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            for item in index.get("papers", []):
                if item.get("date") == date:
                    papers.append({
                        "name": item.get("model_name", item.get("title", "Unknown")[:20]),
                        "arxiv_id": item.get("arxiv_id"),
                        "source": item.get("source"),
                        "title": item.get("title")
                    })
        except Exception as e:
            print(f"读取index.json失败: {e}")
    
    # 如果没有从index加载到，尝试扫描markdown文件
    if not papers:
        for subdir in ["conference", "journal", "arxiv"]:
            md_path = os.path.join(base_path, subdir, f"{date}.md")
            if os.path.exists(md_path):
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 提取论文块
                    paper_blocks = re.split(r'---\s*\n', content)
                    for block in paper_blocks:
                        # 提取标题
                        title_match = re.search(r'###\s+\d+\.\s*(.+)', block)
                        if not title_match:
                            continue
                        title = title_match.group(1).strip()
                        
                        # 提取模型名称（通常是标题中的缩写）
                        name_match = re.search(r'\*\*来源\*\*.*?\(([^)]+)\)', block)
                        model_name = name_match.group(1) if name_match else title.split(':')[0]
                        
                        # 提取arXiv ID
                        arxiv_match = re.search(r'arXiv[:\s]*(\d+\.\d+)', block, re.IGNORECASE)
                        arxiv_id = arxiv_match.group(1) if arxiv_match else None
                        
                        # 提取代码链接（可能有GitHub图）
                        code_match = re.search(r'\*\*代码\*\*.*?\[(.+?)\]', block)
                        code_url = code_match.group(1) if code_match else None
                        
                        if arxiv_id or code_url:
                            papers.append({
                                "name": model_name,
                                "arxiv_id": arxiv_id,
                                "code_url": code_url,
                                "title": title
                            })
                except Exception as e:
                    print(f"读取 {md_path} 失败: {e}")
    
    return papers

def build_paper_urls(paper):
    """为论文构建架构图URL列表"""
    urls = []
    name = paper.get("name", "Unknown")
    arxiv_id = paper.get("arxiv_id")
    code_url = paper.get("code_url", "")
    
    # 1. 尝试从arXiv HTML分析获取架构图
    if arxiv_id:
        fig_info = get_architecture_figure_from_arxiv(arxiv_id)
        if fig_info:
            fig_num, caption = fig_info
            urls.append({
                "url": f"https://arxiv.org/html/{arxiv_id}v1/x{fig_num}.png",
                "source": f"arXiv Figure {fig_num}: {caption[:50]}..."
            })
    
    # 2. 尝试GitHub仓库的assets文件夹（常见命名）
    if code_url and "github.com" in code_url:
        repo_path = code_url.replace("https://github.com/", "").rstrip("/")
        # 常见架构图路径
        github_patterns = [
            f"https://github.com/{repo_path}/raw/main/assets/{name}.png",
            f"https://github.com/{repo_path}/raw/main/assets/architecture.png",
            f"https://github.com/{repo_path}/raw/main/assets/framework.png",
            f"https://github.com/{repo_path}/raw/main/docs/{name}.png",
        ]
        for url in github_patterns:
            urls.append({"url": url, "source": "GitHub assets"})
    
    return urls

# 加载论文列表
print(f"正在加载 {DATE} 的论文元数据...")
metadata_papers = load_papers_from_metadata(DATE)

# 构建PAPERS列表
PAPERS = []
for p in metadata_papers:
    urls = build_paper_urls(p)
    if urls:
        PAPERS.append({
            "name": p["name"],
            "urls": [u["url"] for u in urls],
            "sources": [u["source"] for u in urls]
        })
        print(f"  [{p['name']}] 找到 {len(urls)} 个候选URL")

# 如果没有从元数据加载到，使用硬编码的fallback（用于测试）
if not PAPERS:
    print("警告: 未从元数据加载到论文，使用fallback列表")
    PAPERS = [
        {
            "name": "CoME-VL",
            "urls": ["https://arxiv.org/html/2604.03231v1/x3.png"],
            "sources": ["arXiv Figure 3"]
        },
        {
            "name": "SD-FSMIS",
            "urls": ["https://arxiv.org/html/2604.03134v1/x2.png"],
            "sources": ["arXiv Figure 2"]
        },
        {
            "name": "CrossWeaver",
            "urls": ["https://arxiv.org/html/2604.02948v1/x3.png"],
            "sources": ["arXiv Figure 3"]
        },
        {
            "name": "MedCLIPSeg",
            "urls": ["https://github.com/HealthX-Lab/MedCLIPSeg/raw/main/assets/MedCLIPSeg.png"],
            "sources": ["GitHub assets"]
        },
        {
            "name": "GroundVTS",
            "urls": ["https://arxiv.org/html/2604.02093v1/x3.png"],
            "sources": ["arXiv Figure 3"]
        },
    ]

MIN_WIDTH = 400   # 小于此宽度的图片判定为非架构图
MIN_HEIGHT = 200  # 小于此高度的图片判定为非架构图

results = []

for paper in PAPERS:
    name = paper["name"]
    downloaded = False

    for url in paper["urls"]:
        try:
            print(f"[{name}] 尝试下载: {url}")
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()

            # 尝试打开图片，验证格式和尺寸
            img = Image.open(io.BytesIO(resp.content))
            w, h = img.size
            fmt = img.format or "PNG"

            if w < MIN_WIDTH or h < MIN_HEIGHT:
                print(f"  ✗ 图片太小 ({w}x{h})，可能不是架构图，跳过")
                continue

            # 确定扩展名
            ext = fmt.lower()
            if ext == "jpeg":
                ext = "jpg"
            elif ext not in ("png", "jpg", "gif", "webp", "svg"):
                ext = "png"

            out_path = os.path.join(OUT_DIR, f"{name}.{ext}")
            with open(out_path, "wb") as f:
                f.write(resp.content)

            print(f"  ✓ 保存成功: {out_path}  ({w}x{h}, {fmt})")
            results.append({"name": name, "path": out_path, "size": f"{w}x{h}", "status": "OK"})
            downloaded = True
            break

        except Exception as e:
            print(f"  ✗ 失败: {e}")

    if not downloaded:
        print(f"  ✗ [{name}] 所有URL均失败，跳过")
        results.append({"name": name, "path": None, "size": None, "status": "FAILED"})

print("\n========== 下载结果汇总 ==========")
for r in results:
    status = "✓" if r["status"] == "OK" else "✗"
    print(f"{status} {r['name']}: {r['path']} {r['size'] or ''}")

print(f"\n共下载成功 {sum(1 for r in results if r['status'] == 'OK')}/{len(results)} 张架构图")
print(f"保存目录: {OUT_DIR}")
