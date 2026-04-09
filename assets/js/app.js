/**
 * Daily Papers - GitHub Pages App
 * 日历（年月范围 + 仅可选有数据日期）、分类筛选、卡片详情弹窗
 */

const CONFIG = {
    papersBasePath: 'papers/',
    categories: ['conference', 'journal', 'arxiv'],
    // 不依赖 index.json：按日期探测真实存在的 md 文件
    scanStartDate: '2024-01-01',
    scanBatchDays: 20,
    categoryNames: {
        conference: '🏆 顶会论文',
        journal: '📘 顶刊论文',
        arxiv: '📄 arXiv 最新'
    }
};

/**
 * 解析论文资源路径。Markdown 里常写 `papers/imgs/...`，若再拼 papersBasePath 会变成 papers/papers/...
 */
function resolvePaperAssetUrl(rel) {
    if (!rel) return '';
    let p = String(rel).trim();
    if (p.startsWith('http://') || p.startsWith('https://')) return p;
    p = p.replace(/^\.\//, '');
    if (p.startsWith('papers/')) return p;
    return `${CONFIG.papersBasePath}${p}`;
}

/** 表格单元格中的链接：纯 URL 或 Markdown [label](url) */
function extractUrlFromTableCell(value) {
    if (!value || value === '-') return '';
    const s = String(value).trim();
    const md = s.match(/\[([^\]]*)\]\((https?:[^)\s]+)\)/);
    if (md) return md[2];
    const plain = s.match(/^(https?:\/\/[^\s<]+)/);
    if (plain) return plain[1];
    return '';
}

let selectedDate = new Date();
let currentFilter = 'all';
const availableDates = new Set();
let calendarOpen = false;
let currentMonth = new Date();

/** 有推荐数据的最早 / 最晚日期（含当月边界） */
let minDate = null;
let maxDate = null;
let lastListScrollY = 0;

const paperDetailStore = new Map();

document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    initFilterButtons();
    initTodayButton();
    initBackButton();
    initScrollTopButton();
    bindPaperCardClicks();
    loadAvailableDates().then(() => {
        loadPapersForDate(selectedDate);
    });
});

function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function isSameDay(date1, date2) {
    return formatDate(date1) === formatDate(date2);
}

function compareMonth(a, b) {
    return (a.getFullYear() - b.getFullYear()) * 12 + (a.getMonth() - b.getMonth());
}

function monthStart(d) {
    return new Date(d.getFullYear(), d.getMonth(), 1);
}

function clampMonthToRange(d) {
    if (!minDate || !maxDate) return monthStart(d);
    const t = monthStart(d);
    const minM = monthStart(minDate);
    const maxM = monthStart(maxDate);
    if (t < minM) return new Date(minM);
    if (t > maxM) return new Date(maxM);
    return t;
}

function computeDateBounds() {
    if (availableDates.size === 0) {
        minDate = null;
        maxDate = null;
        return;
    }
    const sorted = [...availableDates].sort();
    const [y1, m1, d1] = sorted[0].split('-').map(Number);
    const [y2, m2, d2] = sorted[sorted.length - 1].split('-').map(Number);
    minDate = new Date(y1, m1 - 1, d1);
    maxDate = new Date(y2, m2 - 1, d2);
}

function monthsForYear(year) {
    if (!minDate || !maxDate) return [];
    let start = 0;
    let end = 11;
    if (year === minDate.getFullYear()) start = minDate.getMonth();
    if (year === maxDate.getFullYear()) end = maxDate.getMonth();
    const out = [];
    for (let m = start; m <= end; m++) out.push(m);
    return out;
}

function populateYearMonthSelects() {
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    if (!yearSelect || !monthSelect) return;

    const yCur = currentMonth.getFullYear();
    const mCur = currentMonth.getMonth();

    yearSelect.innerHTML = '';
    if (!minDate || !maxDate) {
        yearSelect.disabled = true;
        monthSelect.disabled = true;
        return;
    }
    yearSelect.disabled = false;
    monthSelect.disabled = false;

    const yMin = minDate.getFullYear();
    const yMax = maxDate.getFullYear();
    for (let y = yMin; y <= yMax; y++) {
        const opt = document.createElement('option');
        opt.value = String(y);
        opt.textContent = `${y}`;
        if (y === yCur) opt.selected = true;
        yearSelect.appendChild(opt);
    }

    const validMonths = monthsForYear(yCur);
    monthSelect.innerHTML = '';
    validMonths.forEach((m) => {
        const opt = document.createElement('option');
        opt.value = String(m);
        opt.textContent = `${m + 1}`;
        if (m === mCur) opt.selected = true;
        monthSelect.appendChild(opt);
    });
}

function updateNavDisabled() {
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');
    if (!prevMonth || !nextMonth || !minDate || !maxDate) {
        if (prevMonth) prevMonth.disabled = true;
        if (nextMonth) nextMonth.disabled = true;
        return;
    }
    const minM = monthStart(minDate);
    const maxM = monthStart(maxDate);
    const cur = monthStart(currentMonth);
    prevMonth.disabled = compareMonth(cur, minM) <= 0;
    nextMonth.disabled = compareMonth(cur, maxM) >= 0;
}

function initCalendar() {
    const calendarBtn = document.getElementById('calendarBtn');
    const calendarDropdown = document.getElementById('calendarDropdown');
    const prevMonth = document.getElementById('prevMonth');
    const nextMonth = document.getElementById('nextMonth');
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');

    calendarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        calendarOpen = !calendarOpen;
        calendarDropdown.classList.toggle('show', calendarOpen);
        if (calendarOpen) {
            currentMonth = clampMonthToRange(selectedDate);
            renderCalendar();
        }
    });

    document.addEventListener('click', (e) => {
        if (!calendarDropdown.contains(e.target) && e.target !== calendarBtn) {
            calendarOpen = false;
            calendarDropdown.classList.remove('show');
        }
    });

    prevMonth.addEventListener('click', () => {
        if (!minDate) return;
        const minM = monthStart(minDate);
        if (compareMonth(monthStart(currentMonth), minM) <= 0) return;
        currentMonth.setMonth(currentMonth.getMonth() - 1);
        renderCalendar();
    });

    nextMonth.addEventListener('click', () => {
        if (!maxDate) return;
        const maxM = monthStart(maxDate);
        if (compareMonth(monthStart(currentMonth), maxM) >= 0) return;
        currentMonth.setMonth(currentMonth.getMonth() + 1);
        renderCalendar();
    });

    yearSelect.addEventListener('change', () => {
        const y = parseInt(yearSelect.value, 10);
        let m = currentMonth.getMonth();
        const valid = monthsForYear(y);
        if (!valid.includes(m)) m = valid[0];
        currentMonth = new Date(y, m, 1);
        currentMonth = clampMonthToRange(currentMonth);
        renderCalendar();
    });

    monthSelect.addEventListener('change', () => {
        const m = parseInt(monthSelect.value, 10);
        currentMonth = new Date(currentMonth.getFullYear(), m, 1);
        currentMonth = clampMonthToRange(currentMonth);
        renderCalendar();
    });
}

function renderCalendar() {
    if (minDate && maxDate) {
        const c = clampMonthToRange(currentMonth);
        currentMonth = new Date(c.getFullYear(), c.getMonth(), 1);
    }

    populateYearMonthSelects();
    updateNavDisabled();

    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    const label = document.getElementById('calendarMonth');
    if (label) label.textContent = `${year}年${month + 1}月`;

    const grid = document.getElementById('calendarGrid');
    grid.innerHTML = '';

    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    weekdays.forEach((day) => {
        const el = document.createElement('div');
        el.className = 'cal-weekday';
        el.textContent = day;
        grid.appendChild(el);
    });

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    const prevMonthDays = new Date(year, month, 0).getDate();
    for (let i = startPadding - 1; i >= 0; i--) {
        const day = prevMonthDays - i;
        grid.appendChild(createDayElement(day, { className: 'other-month', disabled: true }));
    }

    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = formatDate(date);
        const isToday = isSameDay(date, today);
        const isSelected = isSameDay(date, selectedDate);
        const hasPapers = availableDates.has(dateStr);

        if (hasPapers) {
            const el = createDayElement(day, { hasPapers: true, isToday, isSelected, disabled: false });
            el.addEventListener('click', () => {
                selectedDate = new Date(date);
                updateDateDisplay();
                loadPapersForDate(selectedDate);
                calendarOpen = false;
                document.getElementById('calendarDropdown').classList.remove('show');
                renderCalendar();
            });
            grid.appendChild(el);
        } else {
            grid.appendChild(
                createDayElement(day, {
                    className: 'cal-day--no-data',
                    isToday,
                    isSelected: false,
                    disabled: true
                })
            );
        }
    }

    const endPadding = (7 - ((startPadding + daysInMonth) % 7)) % 7;
    for (let day = 1; day <= endPadding; day++) {
        grid.appendChild(createDayElement(day, { className: 'other-month', disabled: true }));
    }
}

function createDayElement(day, opts = {}) {
    const { className, hasPapers, isToday, isSelected, disabled } = opts;
    const el = document.createElement('button');
    el.type = 'button';
    el.className = 'cal-day';
    el.textContent = day;

    if (className) el.classList.add(className);
    if (hasPapers) el.classList.add('has-papers');
    if (isToday) el.classList.add('today');
    if (isSelected) el.classList.add('selected');
    if (disabled) el.disabled = true;

    return el;
}

function initTodayButton() {
    document.getElementById('todayBtn').addEventListener('click', () => {
        selectedDate = new Date();
        currentMonth = clampMonthToRange(selectedDate);
        updateDateDisplay();
        loadPapersForDate(selectedDate);
        if (calendarOpen) renderCalendar();
    });
}

function updateDateDisplay() {
    const today = new Date();
    const display = isSameDay(selectedDate, today) ? '今日' : formatDate(selectedDate);
    document.getElementById('currentDate').textContent = display;
}

function initFilterButtons() {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach((btn) => {
        btn.addEventListener('click', () => {
            buttons.forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            loadPapersForDate(selectedDate);
        });
    });
}

async function loadAvailableDates() {
    try {
        availableDates.clear();
        await discoverAvailableDates();

        computeDateBounds();
        if (minDate && maxDate) {
            currentMonth = clampMonthToRange(selectedDate);
        }
    } catch (error) {
        console.error('Failed to load available dates:', error);
    } finally {
        updateHeaderStartFrom();
    }
}

async function discoverAvailableDates() {
    const today = new Date();
    const [sy, sm, sd] = CONFIG.scanStartDate.split('-').map(Number);
    const startDate = new Date(sy, sm - 1, sd);
    if (Number.isNaN(startDate.getTime()) || startDate > today) return;

    const dateStrings = [];
    const cursor = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    while (cursor >= startDate) {
        dateStrings.push(formatDate(cursor));
        cursor.setDate(cursor.getDate() - 1);
    }

    const batchSize = Math.max(1, Number(CONFIG.scanBatchDays) || 20);
    for (let i = 0; i < dateStrings.length; i += batchSize) {
        const chunk = dateStrings.slice(i, i + batchSize);
        const checks = await Promise.all(
            chunk.map(async (dateStr) => {
                const exists = await hasAnyCategoryFileForDate(dateStr);
                return { dateStr, exists };
            })
        );
        checks.forEach(({ dateStr, exists }) => {
            if (exists) availableDates.add(dateStr);
        });
    }
}

async function hasAnyCategoryFileForDate(dateStr) {
    const checks = await Promise.all(
        CONFIG.categories.map(async (category) => {
            try {
                const resp = await fetch(`${CONFIG.papersBasePath}${category}/${dateStr}.md`, {
                    method: 'HEAD'
                });
                if (resp.ok) return true;
                // 某些静态服务不支持 HEAD，回退到 GET 检查
                if (resp.status === 405) {
                    const fallback = await fetch(`${CONFIG.papersBasePath}${category}/${dateStr}.md`);
                    return fallback.ok;
                }
            } catch (_) {
                return false;
            }
            return false;
        })
    );
    return checks.some(Boolean);
}

function updateHeaderStartFrom() {
    const el = document.getElementById('headerStartFrom');
    if (!el) return;
    if (minDate) {
        el.textContent = `Start from ${formatDate(minDate)} · Updated daily at 07:00.`;
    } else {
        el.textContent = 'Updated daily at 07:00.';
    }
}

function paperKey(dateStr, category, index) {
    return `${dateStr}|${category}|${index}`;
}

async function loadPapersForDate(date) {
    const container = document.getElementById('papers-list-view');
    const dateStr = formatDate(date);

    // 确保列表页显示，详情页隐藏
    showListView();

    container.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <p>正在加载 ${dateStr} 的论文...</p>
        </div>
    `;

    updateDateDisplay();

    const categoriesToLoad =
        currentFilter === 'all' ? CONFIG.categories : [currentFilter];

    let hasAnyPapers = false;
    let html = '';

    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    html += `
        <div class="date-display">
            <h2>${dateStr}</h2>
            <span class="weekday">${weekdays[date.getDay()]}</span>
        </div>
    `;

    paperDetailStore.clear();

    const results = await Promise.all(
        categoriesToLoad.map((category) =>
            loadCategoryPapers(category, dateStr).then((papers) => ({
                category,
                papers: papers || []
            }))
        )
    );

    for (const { category, papers } of results) {
        if (papers.length > 0) {
            hasAnyPapers = true;
            html += renderCategorySection(category, papers, dateStr);
        }
    }

    if (!hasAnyPapers) {
        html += `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3>暂无 ${dateStr} 的论文推荐</h3>
                <p>该日期暂时没有论文数据，请在日历中选择有推荐的日期。</p>
            </div>
        `;
    }

    container.innerHTML = html;
}

function showListView() {
    showListViewWithOptions({ preserveScroll: false });
}

function showListViewWithOptions(options = {}) {
    const { preserveScroll = false } = options;
    document.getElementById('papers-list-view').style.display = 'block';
    document.getElementById('paper-detail-view').style.display = 'none';
    document.querySelector('.nav-bar').style.display = 'block';
    if (preserveScroll) {
        window.scrollTo(0, Math.max(0, lastListScrollY));
    } else {
        window.scrollTo(0, 0);
    }
}

function showDetailView() {
    lastListScrollY = window.scrollY || window.pageYOffset || 0;
    document.getElementById('papers-list-view').style.display = 'none';
    document.getElementById('paper-detail-view').style.display = 'block';
    document.querySelector('.nav-bar').style.display = 'none';
    window.scrollTo(0, 0);
}

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

function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** 去掉文末误收录的 Markdown 分隔线（如论文之间的 ---） */
function stripTrailingMarkdownHr(text) {
    if (!text) return '';
    return text.replace(/\r?\n\s*---+[\s\r\n]*$/g, '').trim();
}

function parseMarkdownPapers(markdown) {
    const papers = [];
    const sections = markdown.split(/###\s+\d+\.\s+/);

    sections.forEach((section, index) => {
        if (index === 0) return;
        const paper = parsePaperSection(section);
        if (paper) papers.push(paper);
    });

    return papers;
}

function parsePaperSection(section) {
    const lines = section.trim().split('\n');
    const title = lines[0] ? lines[0].trim() : '';

    const paper = {
        title,
        authors: '',
        source: '',
        originalUrl: '',
        keywords: '',
        code: '',
        archImage: '',
        contribution: '',
        methodology: '',
        results: '',
        limitations: '',
        abstractOriginal: '',
        abstractTranslated: ''
    };

    const tableMatch = section.match(/\|[^|]+\|[^|]+\|/g);
    if (tableMatch) {
        tableMatch.forEach((row) => {
            const cells = row.split('|').map((c) => c.trim());
            if (cells[1] && cells[2]) {
                const key = cells[1].replace(/\*\*/g, '');
                const value = cells[2];
                if (key.includes('作者')) paper.authors = value;
                if (key.includes('来源')) paper.source = value;
                if (key.includes('原文')) {
                    const u = extractUrlFromTableCell(value);
                    if (u) paper.originalUrl = u;
                }
                if (key.includes('关键词')) paper.keywords = value;
                if (key.includes('代码')) paper.code = value;
                if (key.includes('架构图')) paper.archImage = value.replace(/`/g, '');
            }
        });
    }

    const emojiHeader = '(?:🔑|🔬|📊|⚠️|📝)?';
    const sectionMap = {
        核心贡献: 'contribution',
        方法论: 'methodology',
        实验结果: 'results',
        局限性: 'limitations',
        'Abstract（原文）': 'abstractOriginal',
        '摘要（中文翻译）': 'abstractTranslated'
    };

    for (const [cnName, key] of Object.entries(sectionMap)) {
        const er = escapeRegex(cnName);
        const regex = new RegExp(
            `####\\s+${emojiHeader}\\s*${er}\\s*\\n([\\s\\S]*?)(?=####|\\*\\*Generated|$)`,
            'i'
        );
        const match = section.match(regex);
        if (match) {
            let value = match[1].trim();
            if (key === 'abstractOriginal') {
                value = value.replace(/^>\s*/gm, '').trim();
            }
            paper[key] = stripTrailingMarkdownHr(value);
        }
    }

    return paper;
}

function renderCategorySection(category, papers, dateStr) {
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
        html += renderPaperCard(paper, index + 1, category, dateStr);
    });

    html += '</div>';
    return html;
}

function buildPreviewText(paper) {
    const raw = (
        paper.contribution ||
        paper.abstractTranslated ||
        paper.methodology ||
        ''
    )
        .replace(/\s+/g, ' ')
        .trim();
    if (raw.length <= 200) return raw;
    return `${raw.slice(0, 200)}…`;
}

function renderPaperCard(paper, index, category, dateStr) {
    const sourceClass = `source-${category}`;
    const key = paperKey(dateStr, category, index);
    paperDetailStore.set(key, { paper, category });

    const preview = buildPreviewText(paper);
    const hasKeywords = paper.keywords && paper.keywords.trim() !== '-';
    const hasCode = paper.code && paper.code !== '-';
    const hasLinkLine = paper.originalUrl || hasCode;

    return `
        <article class="paper-card paper-card--compact" data-paper-key="${key}" tabindex="0" role="button" aria-label="${escapeHtml('查看详情：' + stripInlineMarkdown(paper.title))}">
            <div class="paper-header">
                <h3 class="paper-title md-inline">${index}. ${inlineMarkdownToHtml(paper.title)}</h3>
                <div class="paper-meta paper-meta--stacked">
                    <div class="paper-meta-line">
                        <span class="source-badge ${sourceClass}">${getCategoryLabel(category)}</span>
                        <span class="md-inline">📄 ${inlineMarkdownToHtml(paper.source)}</span>
                    </div>
                    ${paper.authors ? `<div class="paper-meta-line"><span class="md-inline">👤 ${inlineMarkdownToHtml(paper.authors)}</span></div>` : ''}
                    ${hasKeywords ? `<div class="paper-meta-line"><span class="paper-keywords md-inline">🏷️ ${inlineMarkdownToHtml(paper.keywords)}</span></div>` : ''}
                    ${hasLinkLine ? `<div class="paper-meta-line">${paper.originalUrl ? `<span>🔗 <a href="${escapeAttr(paper.originalUrl)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">原文</a></span>` : ''}${hasCode ? `<span>💻 <a href="${escapeAttr(extractUrlFromTableCell(paper.code) || paper.code)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">代码</a></span>` : ''}</div>` : ''}
                </div>
                ${preview ? `<p class="paper-card-preview md-inline">${inlineMarkdownToHtml(preview)}</p>` : ''}
                <p class="paper-card-hint">点击查看完整解读与摘要 →</p>
            </div>
        </article>
    `;
}

function renderPaperDetailHtml(paper, category) {
    const sourceClass = `source-${category}`;
    
    // 架构图HTML
    let archImageHtml = '';
    if (paper.archImage) {
        const imgUrl = resolvePaperAssetUrl(paper.archImage);
        archImageHtml = `
            <div class="paper-arch-image">
                <div class="section-title">🏗️ 模型架构图</div>
                <div class="arch-image-container">
                    <img src="${escapeAttr(imgUrl)}" alt="${escapeAttr(paper.title)} 架构图" 
                         loading="lazy" onclick="window.open('${escapeAttr(imgUrl)}', '_blank')">
                </div>
            </div>
        `;
    }
    
    return `
        <div class="paper-meta">
            <span class="source-badge ${sourceClass}">${getCategoryLabel(category)}</span>
            <span class="md-inline">📄 ${inlineMarkdownToHtml(paper.source)}</span>
            ${paper.authors ? `<span class="md-inline">👤 ${inlineMarkdownToHtml(paper.authors)}</span>` : ''}
            ${paper.originalUrl ? `<span>🔗 <a href="${escapeAttr(paper.originalUrl)}" target="_blank" rel="noopener noreferrer">原文</a></span>` : ''}
            ${paper.code && paper.code !== '-' ? `<span>💻 <a href="${escapeAttr(extractUrlFromTableCell(paper.code) || paper.code)}" target="_blank" rel="noopener noreferrer">代码</a></span>` : ''}
        </div>
        ${archImageHtml}
        <div class="paper-content">
            ${paper.contribution ? `
                <div class="paper-section">
                    <div class="section-title">🔑 核心贡献</div>
                    <div class="section-content md-inline">${nl2brMd(paper.contribution)}</div>
                </div>
            ` : ''}
            ${paper.methodology ? `
                <div class="paper-section">
                    <div class="section-title">🔬 方法论</div>
                    <div class="section-content markdown-like md-inline">${formatBulletLines(paper.methodology)}</div>
                </div>
            ` : ''}
            ${paper.results ? `
                <div class="paper-section">
                    <div class="section-title">📊 实验结果</div>
                    <div class="section-content markdown-like md-inline">${formatBulletLines(paper.results)}</div>
                </div>
            ` : ''}
            ${paper.limitations ? `
                <div class="paper-section">
                    <div class="section-title">⚠️ 局限性</div>
                    <div class="section-content markdown-like md-inline">${formatBulletLines(paper.limitations)}</div>
                </div>
            ` : ''}
        </div>
        ${paper.abstractOriginal || paper.abstractTranslated ? `
            <div class="abstract-section">
                ${paper.abstractOriginal ? `
                    <div class="section-title">📝 Abstract（原文）</div>
                    <div class="abstract-original md-inline">${nl2brMd(paper.abstractOriginal)}</div>
                ` : ''}
                ${paper.abstractTranslated ? `
                    <div class="section-title" style="margin-top:12px;">📝 摘要（中文翻译）</div>
                    <div class="abstract-translated md-inline">${nl2brMd(paper.abstractTranslated)}</div>
                ` : ''}
            </div>
        ` : ''}
    `;
}

function formatBulletLines(text) {
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.every((l) => l.startsWith('- ') || l.startsWith('* '))) {
        const items = lines.map((l) => l.replace(/^[-*]\s+/, ''));
        return `<ul class="detail-list">${items.map((t) => `<li>${inlineMarkdownToHtml(t)}</li>`).join('')}</ul>`;
    }
    return nl2brMd(text);
}

/**
 * 将常见 Markdown 内联语法转为 HTML；纯文本会先转义，避免 XSS。
 * 顺序：`代码` → **加粗** → [链接](url) → *斜体*
 */
function inlineMarkdownToHtml(text) {
    if (!text) return '';
    const placeholders = [];
    const tokenAfterPush = () => `\uE000${placeholders.length - 1}\uE001`;
    let s = text;

    s = s.replace(/`([^`]+)`/g, (_, inner) => {
        placeholders.push('<code class="md-inline-code">' + escapeHtml(inner) + '</code>');
        return tokenAfterPush();
    });

    s = s.replace(/\*\*([^*]+)\*\*/g, (_, inner) => {
        placeholders.push('<strong>' + escapeHtml(inner) + '</strong>');
        return tokenAfterPush();
    });

    s = s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, (_, label, url) => {
        placeholders.push(
            '<a href="' +
                escapeAttr(url) +
                '" target="_blank" rel="noopener noreferrer">' +
                escapeHtml(label) +
                '</a>'
        );
        return tokenAfterPush();
    });

    s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, (_, pre, inner) => {
        placeholders.push('<em>' + escapeHtml(inner) + '</em>');
        return pre + tokenAfterPush();
    });

    s = escapeHtml(s);
    for (let i = 0; i < placeholders.length; i++) {
        s = s.replace(`\uE000${i}\uE001`, placeholders[i]);
    }
    return s;
}

/** 按行做内联 Markdown，再换行转 <br> */
function nl2brMd(s) {
    if (!s) return '';
    return s.split('\n').map((line) => inlineMarkdownToHtml(line)).join('<br>');
}

/** 去掉常见内联 Markdown，用于 aria-label 等纯文本场景 */
function stripInlineMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\*([^*\n]+)\*/g, '$1');
}

function getCategoryLabel(category) {
    const labels = {
        conference: '顶会',
        journal: '顶刊',
        arxiv: 'arXiv'
    };
    return labels[category] || category;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(url) {
    if (!url) return '';
    return String(url)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;');
}

function bindPaperCardClicks() {
    const container = document.getElementById('papers-list-view');
    container.addEventListener('click', (e) => {
        const card = e.target.closest('.paper-card[data-paper-key]');
        if (!card) return;
        if (e.target.closest('a')) return;
        const key = card.dataset.paperKey;
        const entry = paperDetailStore.get(key);
        if (!entry) return;
        openPaperDetail(entry.paper, entry.category);
    });

    container.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        const card = e.target.closest('.paper-card[data-paper-key]');
        if (!card) return;
        e.preventDefault();
        const entry = paperDetailStore.get(card.dataset.paperKey);
        if (!entry) return;
        openPaperDetail(entry.paper, entry.category);
    });
}

function initBackButton() {
    const backBtn = document.getElementById('backToListBtn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            showListViewWithOptions({ preserveScroll: true });
        });
    }

    // 支持键盘返回
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.getElementById('paper-detail-view').style.display !== 'none') {
            showListViewWithOptions({ preserveScroll: true });
        }
    });
}

function initScrollTopButton() {
    const btn = document.getElementById('scrollTopBtn');
    if (!btn) return;

    const toggle = () => {
        const y = window.scrollY || window.pageYOffset || 0;
        btn.classList.toggle('show', y > 260);
    };

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', toggle, { passive: true });
    toggle();
}

function openPaperDetail(paper, category) {
    const titleEl = document.getElementById('detail-page-title');
    const bodyEl = document.getElementById('detail-page-body');

    titleEl.innerHTML = inlineMarkdownToHtml(paper.title || '');
    bodyEl.innerHTML = renderPaperDetailHtml(paper, category);

    showDetailView();
}
