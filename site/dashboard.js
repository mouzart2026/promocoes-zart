/**
 * Promoções Zart - Dashboard
 * Fetches ofertas_encontradas from Supabase REST API and renders charts
 */

// ========================================
// CONFIGURATION
// ========================================
const SUPABASE_CONFIG = {
    url: 'https://innyohbvgtsoihooykxp.supabase.co',
    anonKey: 'sb_publishable_Ryxrj3xL0wShOOwx2vGaRA_QH7SLzRW',
    table: 'ofertas_encontradas',
    select: 'produto_id,titulo,preco_anterior,preco_novo,queda_pct,link,criado_em,plataforma',
    order: 'criado_em.desc',
    limit: 500
};

// ========================================
// DOM Elements
// ========================================
const elements = {
    loading: document.getElementById('loading'),
    error: document.getElementById('error'),
    errorMessage: document.getElementById('error-message'),
    content: document.getElementById('content'),
    statTotal: document.getElementById('stat-total'),
    statML: document.getElementById('stat-ml'),
    statShopee: document.getElementById('stat-shopee'),
    statMaxDiscount: document.getElementById('stat-max-discount'),
    statAvgDiscount: document.getElementById('stat-avg-discount'),
    statLast24h: document.getElementById('stat-last24h'),
    chartDaily: document.getElementById('chart-daily'),
    chartPlatform: document.getElementById('chart-platform'),
    topOffers: document.getElementById('top-offers')
};

// ========================================
// Utility Functions
// ========================================
function formatPrice(value) {
    if (value === null || value === undefined) return '—';
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2
    }).format(Number(value));
}

function formatDiscount(value) {
    if (value === null || value === undefined) return '0%';
    return `${Number(value).toFixed(1)}%`;
}

function formatNumber(value) {
    return new Intl.NumberFormat('pt-BR').format(Number(value));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    elements.loading.classList.remove('hidden');
    elements.error.classList.add('hidden');
    elements.content.classList.add('hidden');
}

function showError(message) {
    elements.loading.classList.add('hidden');
    elements.error.classList.remove('hidden');
    elements.content.classList.add('hidden');
    elements.errorMessage.textContent = message;
}

function showContent() {
    elements.loading.classList.add('hidden');
    elements.error.classList.add('hidden');
    elements.content.classList.remove('hidden');
}

// ========================================
// Data Processing
// ========================================
function processData(offers) {
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const fourteenDaysAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

    // Stats
    const total = offers.length;
    const ml = offers.filter(o => o.plataforma === 'mercado_livre').length;
    const shopee = offers.filter(o => o.plataforma === 'shopee').length;
    const discounts = offers.map(o => Number(o.queda_pct) || 0).filter(d => d > 0);
    const maxDiscount = discounts.length > 0 ? Math.max(...discounts) : 0;
    const avgDiscount = discounts.length > 0
        ? discounts.reduce((a, b) => a + b, 0) / discounts.length
        : 0;
    const last24h = offers.filter(o => new Date(o.criado_em) >= oneDayAgo).length;

    // Daily chart data (last 14 days)
    const dailyData = {};
    for (let i = 13; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        date.setHours(0, 0, 0, 0);
        const key = date.toISOString().split('T')[0];
        dailyData[key] = { ml: 0, shopee: 0, total: 0 };
    }

    offers.forEach(o => {
        const date = new Date(o.criado_em);
        if (date >= fourteenDaysAgo) {
            const key = date.toISOString().split('T')[0];
            if (dailyData[key]) {
                dailyData[key].total++;
                if (o.plataforma === 'mercado_livre') dailyData[key].ml++;
                if (o.plataforma === 'shopee') dailyData[key].shopee++;
            }
        }
    });

    // Platform chart data
    const platformData = { ml, shopee };

    // Top 10 offers by discount
    const topOffers = [...offers]
        .filter(o => (Number(o.queda_pct) || 0) > 0)
        .sort((a, b) => (Number(b.queda_pct) || 0) - (Number(a.queda_pct) || 0))
        .slice(0, 10);

    return {
        stats: { total, ml, shopee, maxDiscount, avgDiscount, last24h },
        dailyData,
        platformData,
        topOffers
    };
}

// ========================================
// Render Functions
// ========================================
function renderStats(stats) {
    elements.statTotal.textContent = formatNumber(stats.total);
    elements.statML.textContent = formatNumber(stats.ml);
    elements.statShopee.textContent = formatNumber(stats.shopee);
    elements.statMaxDiscount.textContent = formatDiscount(stats.maxDiscount);
    elements.statAvgDiscount.textContent = formatDiscount(stats.avgDiscount);
    elements.statLast24h.textContent = formatNumber(stats.last24h);
}

function renderDailyChart(dailyData) {
    const container = elements.chartDaily;
    container.innerHTML = '';

    const maxValue = Math.max(...Object.values(dailyData).map(d => d.total), 1);

    Object.entries(dailyData).forEach(([dateKey, data]) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'chart-bar-wrapper';

        // Stacked bar: ML at bottom, Shopee on top
        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.style.height = `${(data.total / maxValue) * 100}%`;

        const mlPart = document.createElement('div');
        mlPart.style.height = `${(data.ml / maxValue) * 100}%`;
        mlPart.style.background = '#ffcc00';
        mlPart.style.borderRadius = 'var(--radius-sm) var(--radius-sm) 0 0';

        const shopeePart = document.createElement('div');
        shopeePart.style.height = `${(data.shopee / maxValue) * 100}%`;
        shopeePart.style.background = '#ee4d2d';
        shopeePart.style.borderRadius = '0 0 0 0';

        // Stack them
        bar.style.display = 'flex';
        bar.style.flexDirection = 'column-reverse';
        bar.appendChild(mlPart);
        bar.appendChild(shopeePart);

        // Tooltip value
        const value = document.createElement('div');
        value.className = 'chart-bar-value';
        value.textContent = data.total;
        bar.appendChild(value);

        const label = document.createElement('div');
        label.className = 'chart-bar-label';
        const date = new Date(dateKey + 'T00:00:00');
        label.textContent = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });

        wrapper.appendChild(bar);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    });
}

function renderPlatformChart(platformData) {
    const container = elements.chartPlatform;
    container.innerHTML = '';

    const data = [
        { key: 'ml', label: 'Mercado Livre', value: platformData.ml, color: '#ffcc00' },
        { key: 'shopee', label: 'Shopee', value: platformData.shopee, color: '#ee4d2d' }
    ];

    const maxValue = Math.max(...data.map(d => d.value), 1);

    data.forEach(item => {
        const wrapper = document.createElement('div');
        wrapper.className = 'chart-bar-wrapper';
        wrapper.style.flex = '1';
        wrapper.style.maxWidth = '200px';

        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.style.height = `${(item.value / maxValue) * 100}%`;
        bar.style.background = item.color;

        const value = document.createElement('div');
        value.className = 'chart-bar-value';
        value.textContent = formatNumber(item.value);
        bar.appendChild(value);

        const label = document.createElement('div');
        label.className = 'chart-bar-label';
        label.textContent = item.label;

        wrapper.appendChild(bar);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    });
}

function renderTopOffers(topOffers) {
    const container = elements.topOffers;
    container.innerHTML = '';

    if (topOffers.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--color-text-muted);">Nenhuma oferta com desconto</p>';
        return;
    }

    topOffers.forEach((offer, index) => {
        const rank = index + 1;
        const discount = Number(offer.queda_pct) || 0;
        const platform = offer.plataforma || 'mercado_livre';

        const row = document.createElement('div');
        row.className = 'top-offer-row';

        let rankClass = '';
        if (rank === 1) rankClass = 'gold';
        else if (rank === 2) rankClass = 'silver';
        else if (rank === 3) rankClass = 'bronze';

        row.innerHTML = `
            <span class="top-offer-rank ${rankClass}">#${rank}</span>
            <div class="top-offer-info">
                <div class="top-offer-title">${escapeHtml(offer.titulo || 'Produto')}</div>
                <div class="top-offer-meta">
                    <span class="platform-badge ${platform}">${platform === 'mercado_livre' ? 'ML' : 'Shopee'}</span>
                    <span style="margin-left: 0.5rem;">${formatRelativeTime(offer.criado_em)}</span>
                </div>
            </div>
            <div class="top-offer-prices">
                <span class="top-offer-new">${formatPrice(offer.preco_novo)}</span>
                ${offer.preco_anterior ? `<span class="top-offer-old">${formatPrice(offer.preco_anterior)}</span>` : ''}
                <span class="top-offer-discount">${formatDiscount(discount)}</span>
            </div>
        `;

        container.appendChild(row);
    });
}

function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'agora';
    if (diffMins < 60) return `${diffMins}min`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;

    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

// ========================================
// API Functions
// ========================================
async function fetchOffers() {
    const { url, anonKey, table, select, order, limit } = SUPABASE_CONFIG;

    const queryParams = new URLSearchParams({
        select,
        order,
        limit: String(limit)
    });

    const apiUrl = `${url}/rest/v1/${table}?${queryParams.toString()}`;

    try {
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'apikey': anonKey,
                'Authorization': `Bearer ${anonKey}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Erro ao buscar ofertas:', error);
        throw error;
    }
}

// ========================================
// Main Initialization
// ========================================
async function init() {
    // Check if config is still placeholder
    if (SUPABASE_CONFIG.url.includes('SEU_PROJETO') || SUPABASE_CONFIG.anonKey.includes('SEU_ANON_KEY')) {
        showError('Configuração necessária: edite dashboard.js e preencha SUPABASE_CONFIG');
        return;
    }

    showLoading();

    try {
        const offers = await fetchOffers();
        const processed = processData(offers);

        renderStats(processed.stats);
        renderDailyChart(processed.dailyData);
        renderPlatformChart(processed.platformData);
        renderTopOffers(processed.topOffers);

        showContent();
    } catch (error) {
        showError(`Falha ao carregar: ${error.message}`);
    }
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);