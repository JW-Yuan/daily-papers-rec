/**
 * Daily Papers - GitHub Pages App
 * 支持日历选择、分类筛选和 Markdown 渲染
 */

// 配置
const CONFIG = {
    papersBasePath: 'papers/',
    categories: ['conference', 'journal', 'arxiv'],
    categoryNames: {
        conference: '🏆 顶会论文',
        journal: '📘 顶刊论文',
        arxiv: '📄 arXiv 最新'
    }
};

// 全局状态
let currentDate = new Date();
let selectedDate = new Date();
let currentFilter = 'all';
let availableDates = new Set();
let calendarOpen = false;
let currentMonth = new Date();

/**
 * 初始化应用
 */
document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    initFilterButtons();
    initTodayButton();
    loadAvailableDates().then(() => {
        loadPapersForDate(selectedDate);
    });
});

/**
 * 初始化日历
 */
function initCalendar() {
    const calendarBtn = document.getElementById('calendarBtn');
    const calendarDropdown = document.getElementById('calendarDropdown');
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');

    // 切换日历显示
    calendarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        calendarOpen = !calendarOpen;
        calendarDropdown.classList.toggle('show', calendarOpen);
        if (calendarOpen) {
            renderCalendar();
        }
    });

    // 点击外部关闭日历
    document.addEventListener('click', (e) => {
        if (!calendarDropdown.contains(e.target) && e.target !== calendarBtn) {
            calendarOpen = false;
            calendarDropdown.classList.remove('show');
        }
    });

    // 月份导航
    prevMonth.addEventListener('click', () => {
        currentMonth.setMonth(currentMonth.getMonth() - 1);
        renderCalendar();
    });

    nextMonth.addEventListener('click', () => {
        currentMonth.setMonth(currentMonth.getMonth() + 1);
        renderCalendar();
    });
}

/**
 * 渲染日历
 */
function renderCalendar() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    document.getElementById('calendarMonth').textContent =
        `${year}年${month + 1}月`;

    const grid = document.getElementById('calendarGrid');
    grid.innerHTML = '';

    // 星期标题
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    weekdays.forEach(day => {
        const el = document.createElement('div');
        el.className = 'cal-weekday';
        el.textContent = day;
        grid.appendChild(el);
    });

    // 计算日历天数
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    // 上月填充
    const prevMonthDays = new Date(year, month, 0).getDate();
    for (let i = startPadding - 1; i >= 0; i--) {
        const day = prevMonthDays - i;
        const el = createDayElement(day, 'other-month', false);
        grid.appendChild(el);
    }

    // 当月天数
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = formatDate(date);
        const isToday = isSameDay(date, today);
        const isSelected = isSameDay(date, selectedDate);
        const hasPapers = availableDates.has(dateStr);

        const el = createDayElement(day, '', hasPapers, isToday, isSelected);
        el.addEventListener('click', () => {
            selectedDate = new Date(date);
            updateDateDisplay();
            loadPapersForDate(selectedDate);
            calendarOpen = false;
            document.getElementById('calendarDropdown').classList.remove('show');
            renderCalendar();
        });
        grid.appendChild(el);
    }

    // 下月填充
    const endPadding = (7 - ((startPadding + daysInMonth) % 7)) % 7;
    for (let day = 1; day <= endPadding; day++) {
        const el = createDayElement(day, 'other-month', false);
        grid.appendChild(el);
    }
}

/**
 * 创建日历天数元素
 */
function createDayElement(day, className, hasPapers, isToday = false, isSelected = false) {
    const el = document.createElement('button');
    el.className = 'cal-day';
    el.textContent = day;

    if (className) el.classList.add(className);
    if (hasPapers) el.classList.add('has-papers');
    if (isToday) el.classList.add('today');
    if (isSelected) el.classList.add('selected');

    return el;
}

/**
 * 初始化今日推荐按钮
 */
function initTodayButton() {
    document.getElementById('todayBtn').addEventListener('click', () => {
        selectedDate = new Date();
        currentMonth = new Date();
        updateDateDisplay();
        loadPapersForDate(selectedDate);
        if (calendarOpen) {
            renderCalendar();
        }
    });
}

/**
 * 更新日期显示
 */
function updateDateDisplay() {
    const today = new Date();
    const dateStr = formatDate(selectedDate);
    const display = isSameDay(selectedDate, today) ? '今日' : dateStr;
    document.getElementById('currentDate').textContent = display;
}

/**
 * 初始化筛选按钮
 */
function initFilterButtons() {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            loadPapersForDate(selectedDate);
        });
    });
}

/**
 * 加载可用的日期列表
 */
async function loadAvailableDates() {
    try {
        const response = await fetch(`${CONFIG.papersBasePath}index.json`);
        if (!response.ok) return;

        const data = await response.json();

        // 收集所有可用日期
        CONFIG.categories.forEach(cat => {
            if (data[cat]) {
                data[cat].forEach(file => {
                    const date = file.replace('.md', '');
                    availableDates.add(date);
                });
            }
        });
    } catch (error) {
        console.error('Failed to load available dates:', error);
    }
}

/**
 * 加载指定日期的论文
 */
async function loadPapersForDate(date) {
    const container = document.getElementById('papers-container');
    const dateStr = formatDate(date);

    container.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>正在加载 ${dateStr} 的论文...</p>
        </div>
    `;

    updateDateDisplay();

    const categoriesToLoad = currentFilter === 'all'
        ? CONFIG.categories
        : [currentFilter];

    let hasAnyPapers = false;
    let html = '';

    // 日期标题
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    html += `
        <div class="date-display">
            <h2>${dateStr}</h2>
            <span class="weekday">${weekdays[date.getDay()]}</span>
        </div>
    `;

    for (const category of categoriesToLoad) {
        const papers = await loadCategoryPapers(category, dateStr);

        if (papers && papers.length > 0) {
            hasAnyPapers = true;
            html += renderCategorySection(category, papers);
        }
    }

    if (!hasAnyPapers) {
        html += `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>暂无 ${dateStr} 的论文推荐</h3>
                <p>该日期暂时没有论文数据，请选择其他日期查看。</p>
            </div>
        `;
    }

    container.innerHTML = html;

    // 绑定摘要展开事件
    bindAbstractToggles();
}

/**
 * 加载单个分类的论文
 */
async function loadCategoryPapers(category, dateStr) {
    try {
        const response = await fetch(
            `${CONFIG.papersBasePath}${category}/${dateStr}.md`
        );

        if (!response.ok) return null;

        const markdown = await response.text();
        return parseMarkdownPapers(markdown);
    } catch (error) {
        return null;
    }
}

/**
 * 解析 Markdown 论文列表
 */
function parseMarkdownPapers(markdown) {
    const papers = [];

    // 按 ### 分割论文条目
    const sections = markdown.split(/###\s+\d+\.\s+/);

    sections.forEach((section, index) => {
        if (index === 0) return; // 跳过标题部分

        const paper = parsePaperSection(section);
        if (paper) papers.push(paper);
    });

    return papers;
}

/**
 * 解析单篇论文
 */
function parsePaperSection(section) {
    const lines = section.trim().split('\n');
    const title = lines[0].trim();

    const paper = {
        title,
        authors: '',
        source: '',
        code: '',
        contribution: '',
        methodology: '',
        results: '',
        limitations: '',
        abstractOriginal: '',
        abstractTranslated: ''
    };

    // 提取表格信息
    const tableMatch = section.match(/\|[^|]+\|[^|]+\|/g);
    if (tableMatch) {
        tableMatch.forEach(row => {
            const cells = row.split('|').map(c => c.trim());
            if (cells[1] && cells[2]) {
                const key = cells[1].replace(/\*\*/g, '');
                const value = cells[2];
                if (key.includes('作者')) paper.authors = value;
                if (key.includes('来源')) paper.source = value;
                if (key.includes('代码')) paper.code = value;
            }
        });
    }

    // 提取各章节
    const sections = {
        '核心贡献': 'contribution',
        '方法论': 'methodology',
        '实验结果': 'results',
        '局限性': 'limitations',
        'Abstract（原文）': 'abstractOriginal',
        '摘要（中文翻译）': 'abstractTranslated'
    };

    for (const [cnName, key] of Object.entries(sections)) {
        const regex = new RegExp(`####\\s+🔑?\s*${cnName}\\s*\\n([^#]+?)(?=####|\\*\\*Generated|$)`, 'i');
        const match = section.match(regex);
        if (match) {
            let value = match[1].trim();
            if (key === 'abstractOriginal') {
                value = value.replace(/^>\s*/gm, '').trim();
            }
            paper[key] = value;
        }
    }

    return paper;
}

/**
 * 渲染分类章节
 */
function renderCategorySection(category, papers) {
    const categoryName = CONFIG.categoryNames[category];

    let html = `
        <div class="category-section" data-category="${category}">
            <div class="category-header">
                <span class="category-icon">${categoryName.split(' ')[0]}</span>
                <h2 class="category-title">${categoryName.split(' ')[1]}</h2>
                <span class="category-count">${papers.length} 篇</span>
            </div>
    `;

    papers.forEach((paper, index) => {
        html += renderPaperCard(paper, index + 1, category);
    });

    html += '</div>';
    return html;
}

/**
 * 渲染论文卡片
 */
function renderPaperCard(paper, index, category) {
    const sourceClass = `source-${category}`;

    return `
        <div class="paper-card" data-category="${category}">
            <div class="paper-header">
                <h3 class="paper-title">${index}. ${escapeHtml(paper.title)}</h3>
                <div class="paper-meta">
                    <span class="source-badge ${sourceClass}">${getCategoryLabel(category)}</span>
                    <span>📄 ${escapeHtml(paper.source)}</span>
                    ${paper.authors ? `<span>👤 ${escapeHtml(paper.authors)}</span>` : ''}
                    ${paper.code && paper.code !== '-' ?
                        `<span>💻 <a href="${paper.code}" target="_blank">代码</a></span>` : ''}
                </div>
            </div>
            <div class="paper-content">
                ${paper.contribution ? `
                    <div class="paper-section">
                        <div class="section-title">🔑 核心贡献</div>
                        <div class="section-content">${escapeHtml(paper.contribution)}</div>
                    </div>
                ` : ''}
                ${paper.methodology ? `
                    <div class="paper-section">
                        <div class="section-title">🔬 方法论</div>
                        <div class="section-content">${escapeHtml(paper.methodology)}</div>
                    </div>
                ` : ''}
                ${paper.results ? `
                    <div class="paper-section">
                        <div class="section-title">📊 实验结果</div>
                        <div class="section-content">${escapeHtml(paper.results)}</div>
                    </div>
                ` : ''}
                ${paper.limitations ? `
                    <div class="paper-section">
                        <div class="section-title">⚠️ 局限性</div>
                        <div class="section-content">${escapeHtml(paper.limitations)}</div>
                    </div>
                ` : ''}
            </div>
            ${paper.abstractOriginal ? `
                <div class="abstract-section">
                    <div class="abstract-toggle" onclick="toggleAbstract(this)">
                        <span>📝 查看 Abstract</span>
                        <span class="abstract-toggle-icon">▼</span>
                    </div>
                    <div class="abstract-content">
                        <div class="abstract-original">${escapeHtml(paper.abstractOriginal)}</div>
                        ${paper.abstractTranslated ? `
                            <div class="abstract-translated">
                                <strong>中文翻译：</strong><br>
                                ${escapeHtml(paper.abstractTranslated)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * 获取分类标签
 */
function getCategoryLabel(category) {
    const labels = {
        conference: '顶会',
        journal: '顶刊',
        arxiv: 'arXiv'
    };
    return labels[category] || category;
}

/**
 * 切换摘要显示
 */
function toggleAbstract(element) {
    const content = element.nextElementSibling;
    const isExpanded = content.classList.contains('show');

    content.classList.toggle('show', !isExpanded);
    element.classList.toggle('expanded', !isExpanded);
}

/**
 * 绑定摘要展开事件
 */
function bindAbstractToggles() {
    // 事件已在 HTML 中通过 onclick 绑定
}

/**
 * 工具函数：格式化日期
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 工具函数：判断同一天
 */
function isSameDay(date1, date2) {
    return formatDate(date1) === formatDate(date2);
}

/**
 * 工具函数：HTML 转义
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
