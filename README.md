# 每日论文推荐任务规范（CV/VLM/医疗AI）

面向 `computational pathology / WSI / histopathology` 的高质量论文日更仓库。

在线浏览：<https://jw-yuan.github.io/daily-papers-rec/>

---

## 1) 每日推荐目标

每日固定产出 3 类论文（每类 3 篇）：

- 顶会论文（3 篇）
- 顶刊论文（3 篇）
- arXiv 论文（3 篇）

优先原则：病理方向强优先，强调新近性、有效性和可复现性，不为凑数降低标准。

---

## 2) 数据源与筛选规则

### 顶会来源

CVPR / ICCV / ECCV / ICML / ICLR / MICCAI / AAAI / NeurIPS / ISBI

筛选规则：

- 优先最新年份（强约束）
- 同会议 recent > classic
- 优先病理影像与医学基础模型方向

### 顶刊来源

Nature / The Lancet Digital Health / TMI / TPAMI / IJCV / TIP / MIA

筛选规则：

- 优先最新发表（强约束）
- 同期论文优先高影响力工作（例如高引用、强机构、权威团队）
- 优先病理相关临床可落地研究

### arXiv 来源

cs.CV / cs.AI / eess.IV

arXiv 强约束优先级：

1. 最近 7 天提交优先  
2. 与病理关键词语义高度匹配  
3. 高质量机构优先（Google/Meta/Microsoft/Stanford/MIT/Oxford 等）  
4. `computational pathology / WSI / histopathology` 最高优先

---

## 3) 关键词体系（病理优先）

### 核心优先：病理基础模型与多模态

- computational pathology foundation model
- pathology vision language model
- pathology multimodal learning
- whole slide image foundation model
- histopathology image representation learning
- image-text alignment pathology

### 最高优先：病理核心任务

- whole slide image analysis
- histopathology image segmentation
- nucleus segmentation histopathology
- cell detection histopathology
- weakly supervised pathology learning
- self-supervised pathology learning
- few-shot pathology segmentation

### 重要：学习范式

- self-supervised learning medical imaging pathology
- weakly supervised learning histopathology
- prompt learning pathology images
- contrastive learning pathology images

### 安全性/可解释性/泛化

- uncertainty modeling pathology AI
- robust pathology image analysis
- interpretable pathology deep learning
- safe medical AI pathology

### Agent/推理（仅病理相关）

- medical agentic AI pathology
- multimodal reasoning pathology images
- LLM for pathology image analysis

### 临床评估与 benchmark

- pathology benchmark datasets
- whole slide image evaluation protocols
- clinical validation pathology AI

---

## 4) 去重规则（必做）

执行每日更新前，扫描 `papers/` 下全部历史文件，按以下规则去重：

- 标题相同或高度近似视为已推荐
- arXiv ID 相同视为已推荐
- 已推荐论文不重复入选

---

## 5) 文件组织与命名

目录：

- `papers/conference/`：顶会
- `papers/journal/`：顶刊
- `papers/arxiv/`：arXiv
- `papers/imgs/YYYY-MM-DD/`：当日架构图

文件命名：

- 每个分类每天一个文件：`YYYY-MM-DD.md`
- 架构图命名使用模型缩写，例如 `MASS.png`、`MedCBR.png`

---

## 6) Markdown 输出模板（必须统一）

文件开头：

`# 每日论文推荐 - XX | YYYY-MM-DD`

其中 `XX` 取值为：顶会 / 顶刊 / arXiv。

每篇论文结构：

`## X. 论文原名`

然后是表格（按需字段）：

| 项目 | 内容 |
|------|------|
| **作者** | xxx |
| **来源** | 会议/期刊 + 年份 |
| **关键词** | 关键词1, 关键词2, 关键词3（中文） |
| **原文** | https://... |
| **代码** | https://github.com/...（仅确认官方仓库时出现） |
| **架构图** | `papers/imgs/YYYY-MM-DD/xxx.png`（仅成功下载时出现） |

正文小节（全部三级标题）：

- `### 核心贡献`（1-2 句）
- `### 方法论`（3-4 点）
- `### 实验结果`（3-4 点）
- `### 局限性`（2-3 点）
- `### Abstract`
- `### 摘要（中文）`

---

## 7) 架构图下载规则（严格）

下载范围：所有入选论文（顶会+顶刊+arXiv）

保存路径：`papers/imgs/YYYY-MM-DD/[model_abbreviation].png`

只允许下载：

- 架构图
- 方法流程图
- pipeline 图

禁止下载：

- accuracy/loss 曲线
- confusion matrix
- scatter plot
- 表格截图
- 用途不明确图

获取顺序：

1. 优先 arXiv HTML：`https://arxiv.org/html/{arxiv_id}v1`
2. 若无可用图，再看 GitHub/project page
3. 无法确认则跳过

最终处理原则：

- 成功确认并下载后，才写 `架构图` 字段
- 未找到/不确定/下载失败：不写该字段（不允许占位）

---

## 8) 本地预览

```bash
python -m http.server 8000
```

访问：<http://localhost:8000>

---

## 9) 质量底线

- 优先真正有价值、可复现、与病理语义强相关的论文
- 不因数量要求引入低相关或弱质量工作
