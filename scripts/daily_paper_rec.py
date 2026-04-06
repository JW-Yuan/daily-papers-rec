"""
每日论文推荐主脚本
- 搜索arXiv最新论文(CV/VLM/MedAI方向)
- 生成三分类笔记(conference/journal/arxiv)
- 下载架构图并验证
- Git提交推送

用法:
    python daily_paper_rec.py [YYYY-MM-DD]    # 指定日期或默认今天
"""

import os
import sys
import json
import re
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 配置
BASE_DIR = Path(r"D:\BLTM\daily-paper-rec")
PAPERS_DIR = BASE_DIR / "papers"
IMGS_DIR = PAPERS_DIR / "imgs"
SCRIPTS_DIR = BASE_DIR / "scripts"
GIT_REMOTE = "https://github.com/JW-Yuan/daily-papers-rec.git"

# 研究方向关键词
KEYWORDS = {
    "cv": ["computer vision", "image classification", "object detection", "segmentation", "visual recognition"],
    "vlm": ["vision language model", "multimodal", "visual question answering", "image captioning", "clip"],
    "medical": ["medical image", "healthcare", "clinical", "radiology", "pathology", "medical segmentation"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}

def get_date_arg():
    """获取日期参数"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return datetime.now().strftime("%Y-%m-%d")

def search_arxiv_papers(start_date, end_date, max_results=20):
    """
    搜索arXiv指定日期范围内的论文
    使用arXiv API: http://export.arxiv.org/api/query
    """
    print(f"搜索arXiv论文: {start_date} 至 {end_date}")
    
    # 构建查询
    categories = "cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:eess.IV"
    date_filter = f"submittedDate:[{start_date.replace('-', '')}0000 TO {end_date.replace('-', '')}2359]"
    
    query = f"({categories}) AND ({date_filter})"
    
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return parse_arxiv_atom(resp.text)
    except Exception as e:
        print(f"arXiv搜索失败: {e}")
        return []

def parse_arxiv_atom(xml_content):
    """解析arXiv Atom响应"""
    import xml.etree.ElementTree as ET
    
    papers = []
    try:
        root = ET.fromstring(xml_content.encode('utf-8'))
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for entry in root.findall('atom:entry', ns):
            paper = {}
            
            # 标题
            title_elem = entry.find('atom:title', ns)
            paper['title'] = title_elem.text.strip() if title_elem is not None else "Unknown"
            
            # arXiv ID
            id_elem = entry.find('atom:id', ns)
            if id_elem is not None:
                arxiv_id = id_elem.text.split('/')[-1]
                paper['arxiv_id'] = arxiv_id.replace('v1', '').replace('v2', '')
            
            # 摘要
            summary_elem = entry.find('atom:summary', ns)
            paper['abstract'] = summary_elem.text.strip() if summary_elem is not None else ""
            
            # 作者
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text)
            paper['authors'] = authors
            
            # 发布日期
            published_elem = entry.find('atom:published', ns)
            if published_elem is not None:
                paper['published'] = published_elem.text[:10]
            
            # 分类
            categories = []
            for cat in entry.findall('atom:category', ns):
                term = cat.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories
            
            papers.append(paper)
    except Exception as e:
        print(f"解析arXiv响应失败: {e}")
    
    return papers

def score_paper_relevance(paper):
    """
    评分论文与研究方向的相关性
    返回: (score, matched_keywords, category)
    """
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    best_score = 0
    best_category = None
    best_keywords = []
    
    for category, keywords in KEYWORDS.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw.lower() in text:
                score += 1
                matched.append(kw)
        if score > best_score:
            best_score = score
            best_category = category
            best_keywords = matched
    
    return best_score, best_keywords, best_category

def get_github_repo(paper):
    """尝试从arXiv页面获取GitHub链接"""
    arxiv_id = paper.get('arxiv_id')
    if not arxiv_id:
        return None
    
    try:
        # 尝试arXiv abstract页面
        url = f"https://arxiv.org/abs/{arxiv_id}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        # 查找GitHub链接
        github_pattern = r'https?://github\.com/[\w.-]+/[\w.-]+'
        matches = re.findall(github_pattern, resp.text)
        
        if matches:
            # 返回最短的链接（通常是主仓库链接）
            return min(matches, key=len)
    except Exception as e:
        print(f"获取GitHub链接失败 {arxiv_id}: {e}")
    
    return None

def classify_paper(paper):
    """
    分类论文到: conference, journal, arxiv
    基于发布渠道和类型
    """
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()
    text = title + " " + abstract
    
    # 会议论文特征
    conference_signs = ['conference', 'proceedings', 'cvpr', 'iccv', 'eccv', 'icml', 'iclr', 'neurips', 'aaai', 'mm', 'miccai']
    for sign in conference_signs:
        if sign in text:
            return 'conference'
    
    # 期刊论文特征
    journal_signs = ['journal', 'transactions', 'ieee', 'springer', 'elsevier', 'arxiv preprint']
    for sign in journal_signs:
        if sign in text:
            return 'journal'
    
    # 默认arXiv
    return 'arxiv'

def translate_abstract(abstract):
    """
    调用翻译API翻译摘要
    这里使用简单的占位符，实际可以接入翻译服务
    """
    # 简化处理：返回提示
    return "[中文翻译需接入翻译API]"

def generate_paper_note(paper, category):
    """生成单篇论文的Markdown笔记"""
    title = paper.get('title', 'Unknown')
    authors = paper.get('authors', [])
    arxiv_id = paper.get('arxiv_id', '')
    abstract = paper.get('abstract', '')
    published = paper.get('published', '')
    github = paper.get('github', '')
    
    # 提取模型名称（通常是标题中的缩写）
    model_name = extract_model_name(title)
    
    # 架构图路径
    img_path = f"papers/imgs/{published}/{model_name}.png" if published else f"papers/imgs/{model_name}.png"
    
    note = f"""### {title}

| 项目 | 内容 |
|------|------|
| **作者** | {', '.join(authors[:6])}{' et al.' if len(authors) > 6 else ''} |
| **来源** | arXiv:{arxiv_id} ({published})
| **代码** | [{github or 'N/A'}]({github or '#'}) |
| **架构图** | `{img_path}` |

#### 🔑 核心贡献
- [待补充]

#### 🔬 方法论
- [待补充]

#### 📊 实验结果
- [待补充]

#### ⚠️ 局限性
- [待补充]

#### 📝 Abstract（原文）
> {abstract}

#### 📝 摘要（中文翻译）
[待翻译]

---

"""
    return note, model_name

def extract_model_name(title):
    """从标题提取模型名称（通常是冒号前的缩写）"""
    # 尝试匹配 "Name: Description" 格式
    match = re.match(r'^([A-Za-z0-9\-]+):', title)
    if match:
        return match.group(1)
    
    # 尝试匹配大写字母缩写
    words = title.split()
    for word in words[:3]:
        if word.isupper() and len(word) >= 2:
            return word
        if re.match(r'^[A-Z][a-zA-Z0-9]*$', word) and len(word) >= 2:
            return word
    
    # 返回前15个字符
    return title[:15].replace(' ', '_')

def generate_daily_notes(date, papers_by_category):
    """生成每日笔记文件"""
    category_names = {
        'conference': ('🏆 顶会论文', '计算机视觉 · 多模态大模型 · 医疗影像 AI'),
        'journal': ('📘 顶刊论文', 'TPAMI · IJCV · TIP · TMI · MIA'),
        'arxiv': ('📄 arXiv 最新', 'cs.CV · cs.AI · eess.IV')
    }
    
    for category, papers in papers_by_category.items():
        if not papers:
            continue
        
        name_zh, subtitle = category_names.get(category, ('📄 论文推荐', ''))
        
        content = f"# {name_zh}推荐 - {date}\n\n> {subtitle}\n\n---\n\n"
        
        model_names = []
        for i, paper in enumerate(papers, 1):
            note, model_name = generate_paper_note(paper, category)
            content += note
            model_names.append(model_name)
        
        content += f"*Generated by WorkBuddy · {date}*\n"
        
        # 保存文件
        output_dir = PAPERS_DIR / category
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{date}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ 生成: {output_file}")
    
    return model_names

def download_architecture_images(date, papers):
    """调用下载脚本获取架构图"""
    print(f"\n下载架构图 ({date})...")
    
    script_path = SCRIPTS_DIR / "download_arch_imgs.py"
    
    try:
        result = subprocess.run(
            ["python", str(script_path), date],
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print(f"  警告: {result.stderr[:200]}")
        return result.returncode == 0
    except Exception as e:
        print(f"  ✗ 下载架构图失败: {e}")
        return False

def git_commit_and_push(date):
    """Git提交并推送"""
    print(f"\nGit提交 ({date})...")
    
    try:
        os.chdir(BASE_DIR)
        
        # 添加文件
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # 提交
        result = subprocess.run(
            ["git", "commit", "-m", f"Add paper recommendations for {date}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and "nothing to commit" not in result.stderr.lower():
            print(f"  提交警告: {result.stderr[:200]}")
        else:
            print(f"  ✓ 提交成功")
        
        # 推送
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ 推送成功")
            return True
        else:
            print(f"  ✗ 推送失败: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Git操作失败: {e}")
        return False

def main():
    date = get_date_arg()
    print(f"=== 每日论文推荐 ({date}) ===\n")
    
    # 1. 搜索论文
    # 默认搜索最近3天的论文
    end_date = date
    start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    
    papers = search_arxiv_papers(start_date, end_date, max_results=50)
    print(f"找到 {len(papers)} 篇论文\n")
    
    if not papers:
        print("未找到论文，跳过")
        return
    
    # 2. 评分和筛选
    scored_papers = []
    for paper in papers:
        score, keywords, category = score_paper_relevance(paper)
        if score > 0:  # 只保留相关的
            paper['relevance_score'] = score
            paper['matched_keywords'] = keywords
            paper['research_category'] = category
            paper['github'] = get_github_repo(paper)
            scored_papers.append(paper)
    
    # 按相关性和日期排序
    scored_papers.sort(key=lambda x: (x['relevance_score'], x.get('published', '')), reverse=True)
    
    # 取前N篇
    selected_papers = scored_papers[:10]
    print(f"筛选出 {len(selected_papers)} 篇相关论文\n")
    
    # 3. 分类
    papers_by_category = {'conference': [], 'journal': [], 'arxiv': []}
    for paper in selected_papers:
        cat = classify_paper(paper)
        papers_by_category[cat].append(paper)
    
    for cat, plist in papers_by_category.items():
        print(f"  {cat}: {len(plist)} 篇")
    
    # 4. 生成笔记
    print("\n生成笔记文件...")
    generate_daily_notes(date, papers_by_category)
    
    # 5. 下载架构图
    download_architecture_images(date, selected_papers)
    
    # 6. Git提交
    git_commit_and_push(date)
    
    print(f"\n=== 完成 ({date}) ===")

if __name__ == "__main__":
    main()
