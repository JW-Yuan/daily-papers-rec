/**
 * Daily Papers - GitHub Pages App
 * 动态加载并展示每日论文推荐
 */

// 配置
const CONFIG = {
    papersDir: 'papers/',
    defaultFilter: 'all'
};

// 全局状态
let allPapers = [];
let currentFilter = CONFIG.defaultFilter;

/**
 * 初始化应用
 */
document.addEventListener('DOMContentLoaded', () => {
    initFilterButtons();
    loadPapers();
});

/**
 * 初始化筛选按钮
 */
function initFilterButtons() {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // 更新按钮状态
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 更新筛选条件
            currentFilter = btn.dataset.filter;
            renderPapers();
        });
    });
}

/**
 * 加载论文列表
 * 扫描 papers/ 目录下的所有 Markdown 文件
 */
async function loadPapers() {
    const listContainer = document.getElementById('papers-list');

    try {
        // 尝试获取 papers 目录下的文件列表
        // 由于 GitHub Pages 是静态托管，我们需要一个文件索引
        // 这里使用一个约定：papers/index.json 包含所有文件列表
        const response = await fetch(`${CONFIG.papersDir}index.json`);

        if (!response.ok) {
            // 如果没有 index.json，尝试加载最新的几个文件
            await loadPapersFallback();
            return;
        }

        const files = await response.json();
        allPapers = await Promise.all(
            files.map(file => parsePaperFile(file))
        );

        // 按日期排序（最新的在前）
        allPapers.sort((a, b) => new Date(b.date) - new Date(a.date));

        renderPapers();
    } catch (error) {
        console.error('Failed to load papers:', error);
        listContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>暂无论文数据</h3>
                <p>论文列表正在准备中，请稍后再来查看。</p>
            </div>
        `;
    }
}

/**
 * 备用加载方式：尝试加载最近几天的文件
 */
async function loadPapersFallback() {
    const dates = getRecentDates(30); // 尝试最近30天
    const papers = [];

    for (const date of dates) {
        try {
            const response = await fetch(`${CONFIG.papersDir}${date}.md`);
            if (response.ok) {
                const content = await response.text();
                const parsed = parseMarkdown(content, date);
                if (parsed && parsed.papers.length > 0) {
                    papers.push(parsed);
                }
            }
        } catch (e) {
            // 忽略不存在的文件
        }
    }

    allPapers = papers;
    renderPapers();
}

/**
 * 获取最近 N 天的日期列表
 */
function getRecentDates(days) {
    const dates = [];
    const today = new Date();

    for (let i = 0; i < days; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        dates.push(dateStr);
    }

    return dates;
}

/**
 * 解析单个论文文件
 */
async function parsePaperFile(filename) {
    const response = await fetch(`${CONFIG.papersDir}${filename}`);
    const content = await response.text();
    const date = filename.replace('.md', '');
    return parseMarkdown(content, date);
}

/**
 * 解析 Markdown 内容
 */
function parseMarkdown(content, date) {
    const papers = [];
    const sections = content.split(/##\s+/);

    sections.forEach(section => {
        if (!section.trim()) return;

        // 识别来源类型
        let sourceType = 'arxiv';
        if (section.includes('顶会')) sourceType = 'conference';
        else if (section.includes('顶刊')) sourceType = 'journal';

        // 提取论文条目（以 ### 开头）
        const paperMatches = section.match(/###\s+\d+\.\s+[^]+?(?=###|\n##|$)/g);

        if (paperMatches) {
            paperMatches.forEach(paperText => {
                const paper = parsePaperEntry(paperText, sourceType);
                if (paper) papers.push(paper);
            });
        }
    });

    return {
        date,
        papers
    };
}

/**
 * 解析单篇论文条目
 */
function parsePaperEntry(text, defaultSourceType) {
    const lines = text.split('\n');
    const titleMatch = lines[0].match(/###\s+\d+\.\s+(.+)/);

    if (!titleMatch) return null;

    const title = titleMatch[1].trim();
    let source = '';
    let sourceType = defaultSourceType;
    let authors = '';
    let code = '';
    let contribution = '';
    let methodology = '';
    let results = '';
    let limitations = '';
    let abstractOriginal = '';
    let abstractTranslated = '';

    // 提取表格信息
    const tableMatch = text.match(/\|[^|]+\|[^|]+\|/g);
    if (tableMatch) {
        tableMatch.forEach(row => {
            if (row.includes('作者')) {
                authors = row.split('|')[2]?.trim() || '';
            }
            if (row.includes('来源')) {
                source = row.split('|')[2]?.trim() || '';
                // 根据来源判断类型
                if (/CVPR|ECCV|ICCV|ICML|ICLR|MICCAI|AAAI|NeurIPS/i.test(source)) {
                    sourceType = 'conference';
                } else if (/TPAMI|IJCV|TIP|TMI|MIA|JSHI|Nature|Science/i.test(source)) {
                    sourceType = 'journal';
                }
            }
            if (row.includes('代码')) {
                code = row.split('|')[2]?.trim() || '';
            }
        });
    }

    // 提取各章节内容
    const sections = {
        '核心贡献': 'contribution',
        '方法论': 'methodology',
        '实验结果': 'results',
        '局限性': 'limitations',
        'Abstract（原文）': 'abstractOriginal',
        '摘要（中文翻译）': 'abstractTranslated'
    };

    for (const [cnName, key] of Object.entries(sections)) {
        const regex = new RegExp(`####\\s+🔑?\s*${cnName}\\s*\\n([^#]+)`, 'i');
        const match = text.match(regex);
        if (match) {
            const value = match[1].trim();
            if (key === 'abstractOriginal') {
                // 移除引用符号
                abstractOriginal = value.replace(/^>\s*/gm, '').trim();
            } else {
                eval(`${key} = value`);
            }
        }
    }

    return {
        title,
        source,
        sourceType,
        authors,
        code,
        contribution,
        methodology,
        results,
        limitations,
        abstractOriginal,
        abstractTranslated
    };
}

/**
 * 渲染论文列表
 */
function renderPapers() {
    const container = document.getElementById('papers-list');

    if (allPapers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>暂无论文数据</h3>
            </div>
        `;
        return;
    }

    let html = '';

    allPapers.forEach(dayData => {
        // 筛选当天的论文
        const filteredPapers = currentFilter === 'all'
            ? dayData.papers
            : dayData.papers.filter(p => p.sourceType === currentFilter);

        if (filteredPapers.length === 0) return;

        html += `
            <div class="date-section">
                <div class="date-header">
                    <h2>${formatDate(dayData.date)}</h2>
                    <span class="date-badge">${filteredPapers.length} 篇</span>
                </div>
        `;

        filteredPapers.forEach(paper => {
            html += renderPaperCard(paper);
        });

        html += '</div>';
    });

    if (html === '') {
        html = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>该分类下暂无论文</h3>
                <p>尝试切换到其他分类查看。</p>
            </div>
        `;
    }

    container.innerHTML = html;

    // 绑定摘要展开/收起事件
    bindAbstractToggles();
}

/**
 * 渲染单篇论文卡片
 */
function renderPaperCard(paper) {
    const sourceClass = `source-${paper.sourceType}`;
    const sourceLabel = {
        'conference': '🏆 顶会',
        'journal': '📘 顶刊',
        'arxiv': '📄 arXiv'
    }[paper.sourceType] || '📄';

    return `
        <div class="paper-card" data-source="${paper.sourceType}">
            <div class="paper-header">
                <h3 class="paper-title">${escapeHtml(paper.title)}</h3>
                <div class="paper-meta">
                    <span class="source-badge ${sourceClass}">${sourceLabel}</span>
                    <span>📄 ${escapeHtml(paper.source)}</span>
                    ${paper.authors ? `<span>👤 ${escapeHtml(paper.authors)}</span>` : ''}
                    ${paper.code && paper.code !== '-' ? `<span>💻 <a href="${paper.code}" target="_blank">代码</a></span>` : ''}
                </div>
            </div>
            <div class="paper-content">
                ${paper.contribution ? `
                    <div class="paper-section">
                        <div class="section-title">核心贡献</div>
                        <div class="section-content">${escapeHtml(paper.contribution)}</div>
                    </div>
                ` : ''}
                ${paper.methodology ? `
                    <div class="paper-section">
                        <div class="section-title">方法论</div>
                        <div class="section-content">${escapeHtml(paper.methodology)}</div>
                    </div>
                ` : ''}
            </div>
            ${paper.abstractOriginal ? `
                <div class="abstract-section">
                    <div class="abstract-toggle" onclick="toggleAbstract(this)">
                        <span>📝 查看 Abstract</span>
                        <span>▼</span>
                    </div>
                    <div class="abstract-content">
                        <div class="abstract-original">${escapeHtml(paper.abstractOriginal)}</div>
                        ${paper.abstractTranslated ? `
                            <div class="abstract-translated">${escapeHtml(paper.abstractTranslated)}</div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 切换摘要显示/隐藏
 */
function toggleAbstract(element) {
    const content = element.nextElementSibling;
    const arrow = element.querySelector('span:last-child');

    if (content.classList.contains('show')) {
        content.classList.remove('show');
        arrow.textContent = '▼';
    } else {
        content.classList.add('show');
        arrow.textContent = '▲';
    }
}

/**
 * 绑定摘要切换事件
 */
function bindAbstractToggles() {
    // 事件已在 HTML 中通过 onclick 绑定
}

/**
 * 格式化日期显示
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekday = weekdays[date.getDay()];

    return `${dateStr} ${weekday}`;
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
