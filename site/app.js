/**
 * PromoZart - Frontend App
 * Fetches ofertas_encontradas from Supabase REST API
 * Supports filtering, searching, sorting, and discount thresholds
 */

// ========================================
// CONFIGURATION
// ========================================
// Config is injected by Cloudflare Pages via inline script in index.html
// using %%SUPABASE_ANON_KEY%% environment variable substitution
const SUPABASE_CONFIG = window.SUPABASE_CONFIG || {
    url: 'https://innyohbvgtsoihooykxp.supabase.co',
    anonKey: '',
    table: 'ofertas_encontradas',
    select: 'produto_id,titulo,preco_anterior,preco_novo,queda_pct,link,criado_em,plataforma,imagem',
    order: 'criado_em.desc',
    limit: 200
};

// ========================================
// STATE
// ========================================
let allOffers = [];
let filteredOffers = [];
let currentFilters = {
    search: '',
    platform: '',
    discountMin: '',
    timeRange: '',
    sort: 'discount-desc'
};

// ========================================
// DOM Elements
// ========================================
const elements = {
    loading: document.getElementById('loading'),
    empty: document.getElementById('empty'),
    offers: document.getElementById('offers'),
    resultsInfo: document.getElementById('resultsInfo'),
    resultsCount: document.getElementById('resultsCount'),
    lastUpdate: document.getElementById('lastUpdate'),

    searchInput: document.getElementById('searchInput'),
    platformFilter: document.getElementById('platformFilter'),
    discountFilter: document.getElementById('discountFilter'),
    timeFilter: document.getElementById('timeFilter'),
    sortFilter: document.getElementById('sortFilter'),
    clearFilters: document.getElementById('clearFilters'),
    filtersBar: document.getElementById('filtersBar'),

    trustBanner: document.getElementById('trustBanner'),
    trustDismiss: document.getElementById('trustDismiss'),
    bookmarkBanner: document.getElementById('bookmarkBanner'),
    bookmarkDismiss: document.getElementById('bookmarkDismiss')
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
    if (value === null || value === undefined || Number(value) === 0) return '';
    return `${Number(value).toFixed(1).replace(/\.0$/, '')}% OFF`;
}

function formatRelativeTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'agora mesmo';
    if (diffMins < 60) return `${diffMins} min atrás`;
    if (diffHours < 24) return `${diffHours}h atrás`;
    if (diffDays < 7) return `${diffDays}d atrás`;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconPath = type === 'error'
        ? '<path d="M10 15h4M9 9h6v4H9z"/>'
        : '<path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"/><path d="M9 9h.01M9 13h.01M13 13h.01M13 13v4"/>';

    const closePath = '<path d="M18 6 6 18M6 6l12 12"/>';

    toast.innerHTML = `
        <svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">${iconPath}</svg>
        <span class="toast-message">${escapeHtml(message)}</span>
        <button class="toast-close" aria-label="Fechar">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, 5000);
}

// ========================================
// Local Storage Helpers
// ========================================
function saveFilters() {
    localStorage.setItem('promozart-filters', JSON.stringify(currentFilters));
}

function loadFilters() {
    const saved = localStorage.getItem('promozart-filters');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            return { ...currentFilters, ...parsed };
        } catch { return null; }
    }
    return null;
}

function saveBannerDismissed(key) {
    localStorage.setItem(key, 'dismissed');
}

function isBannerDismissed(key) {
    return localStorage.getItem(key) === 'dismissed';
}

// ========================================
// State Management
// ========================================
function showLoading() {
    if (elements.loading) elements.loading.classList.remove('hidden');
    if (elements.empty) elements.empty.classList.add('hidden');
    if (elements.offers) elements.offers.classList.add('hidden');
    if (elements.resultsInfo) elements.resultsInfo.classList.add('hidden');
}

function hideLoading() {
    if (elements.loading) elements.loading.classList.add('hidden');
}

function showEmpty() {
    if (elements.empty) elements.empty.classList.remove('hidden');
    if (elements.offers) elements.offers.classList.add('hidden');
    if (elements.resultsInfo) elements.resultsInfo.classList.add('hidden');
}

function showOffers() {
    if (elements.offers) elements.offers.classList.remove('hidden');
    if (elements.empty) elements.empty.classList.add('hidden');
    if (elements.resultsInfo) elements.resultsInfo.classList.remove('hidden');
}

// ========================================
// Filtering & Sorting Logic
// ========================================
function applyFilters() {
    let result = [...allOffers];

    // Search filter (title)
    if (currentFilters.search) {
        const term = currentFilters.search.toLowerCase();
        result = result.filter(o =>
            (o.titulo || '').toLowerCase().includes(term)
        );
    }

    // Platform filter
    if (currentFilters.platform) {
        result = result.filter(o => o.plataforma === currentFilters.platform);
    }

    // Discount minimum filter
    if (currentFilters.discountMin) {
        const minDiscount = Number(currentFilters.discountMin);
        result = result.filter(o => Number(o.queda_pct) >= minDiscount);
    }

    // Time range filter
    if (currentFilters.timeRange) {
        const hours = Number(currentFilters.timeRange);
        const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
        result = result.filter(o => new Date(o.criado_em) >= cutoff);
    }

    // Sorting
    switch (currentFilters.sort) {
        case 'discount-desc':
            result.sort((a, b) => (Number(b.queda_pct) || 0) - (Number(a.queda_pct) || 0));
            break;
        case 'recent-desc':
            result.sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em));
            break;
        case 'price-asc':
            result.sort((a, b) => (Number(a.preco_novo) || 0) - (Number(b.preco_novo) || 0));
            break;
        case 'price-desc':
            result.sort((a, b) => (Number(b.preco_novo) || 0) - (Number(a.preco_novo) || 0));
            break;
        case 'title-asc':
            result.sort((a, b) => (a.titulo || '').localeCompare(b.titulo || ''));
            break;
    }

    filteredOffers = result;
    saveFilters();
    updateResultsInfo();
    renderOffers(filteredOffers);
}

function updateFiltersFromUI() {
    currentFilters.search = elements.searchInput?.value.trim() || '';
    currentFilters.platform = elements.platformFilter?.value || '';
    currentFilters.discountMin = elements.discountFilter?.value || '';
    currentFilters.timeRange = elements.timeFilter?.value || '';
    currentFilters.sort = elements.sortFilter?.value || 'discount-desc';
}

function updateUIFromFilters() {
    if (elements.searchInput) elements.searchInput.value = currentFilters.search;
    if (elements.platformFilter) elements.platformFilter.value = currentFilters.platform;
    if (elements.discountFilter) elements.discountFilter.value = currentFilters.discountMin;
    if (elements.timeFilter) elements.timeFilter.value = currentFilters.timeRange;
    if (elements.sortFilter) elements.sortFilter.value = currentFilters.sort;
}

function clearAllFilters() {
    currentFilters = {
        search: '',
        platform: '',
        discountMin: '',
        timeRange: '',
        sort: 'discount-desc'
    };
    updateUIFromFilters();
    applyFilters();
}

function updateResultsInfo() {
    const count = filteredOffers.length;
    const total = allOffers.length;

    if (elements.resultsCount) {
        elements.resultsCount.textContent = count === total
            ? `${count} ofertas encontradas`
            : `${count} de ${total} ofertas`;
    }

    if (elements.lastUpdate) {
        if (allOffers.length > 0) {
            elements.lastUpdate.textContent = `Atualizado ${formatRelativeTime(allOffers[0].criado_em)}`;
        } else {
            elements.lastUpdate.textContent = '';
        }
    }
}

// ========================================
// Render Functions
// ========================================
function getPlatformTag(platform) {
    const tags = {
        mercado_livre: '<span class="platform-tag ml" aria-label="Mercado Livre">ML</span>',
        shopee: '<span class="platform-tag shopee" aria-label="Shopee">Shopee</span>'
    };
    return tags[platform] || '';
}

function getPlatformBadge(platform) {
    const badges = {
        mercado_livre: '<span class="platform-badge ml">ML</span>',
        shopee: '<span class="platform-badge shopee">Shopee</span>'
    };
    return badges[platform] || '';
}

function createOfferCard(offer) {
    const article = document.createElement('article');
    article.className = 'offer-card';
    article.setAttribute('role', 'listitem');

    const discount = Number(offer.queda_pct) || 0;
    const hasDiscount = discount > 0;

    const title = escapeHtml(offer.titulo || 'Produto sem título');
    const link = offer.link || '#';
    const priceNew = formatPrice(offer.preco_novo);
    const priceOld = formatPrice(offer.preco_anterior);
    const discountText = hasDiscount ? formatDiscount(offer.queda_pct) : '';
    const createdAt = formatRelativeTime(offer.criado_em);
    const platformTag = getPlatformTag(offer.plataforma);
    const imageUrl = offer.imagem || '';

    let discountOverlay = '';
    if (discountText) {
        discountOverlay = `<div class="discount-overlay">${discountText}</div>`;
    }

    const imgHtml = imageUrl
        ? `<img src="${escapeHtml(imageUrl)}" alt="${title}" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">`
        : `<div class="image-fallback-wrapper" style="display:${imageUrl ? 'none' : 'block'};"><svg class="image-fallback" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/><path d="M21 3l-7 7m-5 5l-7 7"/></svg></div>`;

    article.innerHTML = `
        <div class="offer-image" aria-hidden="true"         >
            ${discountOverlay}
            ${imgHtml}
        </div>
        <div class="offer-content">
            <div class="offer-header">
                <h3 class="offer-title">${title}</h3>
                ${getPlatformBadge(offer.plataforma)}
            </div>
            <div class="offer-pricing">
                <div class="price-row">
                    <span class="price-current">${priceNew}</span>
                    ${hasDiscount ? `<span class="price-original">${priceOld}</span>` : ''}
                    ${hasDiscount ? `<span class="discount-chip">${discountText}</span>` : ''}
                </div>
            </div>
            <div class="offer-meta">
                <span>Atualizado ${createdAt}</span>
                ${offer.produto_id ? `<span>#${offer.produto_id}</span>` : ''}
            </div>
            <div class="offer-action">
                <a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" aria-label="Ver oferta no ${offer.plataforma === 'mercado_livre' ? 'Mercado Livre' : 'Shopee'}">
                    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                        <polyline points="15 3 21 3 21 9"/>
                        <line x1="10" y1="14" x2="21" y2="3"/>
                    </svg>
                    Ver oferta
                </a>
            </div>
        </div>
    `;

    return article;
}

function renderOffers(offers) {
    if (!elements.offers) return;

    elements.offers.innerHTML = '';

    if (!offers || offers.length === 0) {
        showEmpty();
        return;
    }

    const fragment = document.createDocumentFragment();
    offers.forEach(offer => {
        fragment.appendChild(createOfferCard(offer));
    });

    elements.offers.appendChild(fragment);
    showOffers();
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
                'Accept': 'application/json',
                'Prefer': 'count=exact'
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
        showToast('Falha ao carregar ofertas. Tente recarregar a página.', 'error');
        throw error;
    }
}

// ========================================
// Banner Dismiss Handlers
// ========================================
function setupBannerHandlers() {
    if (elements.trustDismiss && elements.trustBanner) {
        elements.trustDismiss.addEventListener('click', () => {
            elements.trustBanner.style.display = 'none';
            saveBannerDismissed('trust-banner');
        });
    }

    if (elements.bookmarkDismiss && elements.bookmarkBanner) {
        elements.bookmarkDismiss.addEventListener('click', () => {
            elements.bookmarkBanner.style.display = 'none';
            saveBannerDismissed('bookmark-banner');
        });
    }

    // Restore banner state from localStorage
    if (isBannerDismissed('trust-banner') && elements.trustBanner) {
        elements.trustBanner.style.display = 'none';
    }
    if (isBannerDismissed('bookmark-banner') && elements.bookmarkBanner) {
        elements.bookmarkBanner.style.display = 'none';
    }
}

// ========================================
// Event Listeners
// ========================================
function setupEventListeners() {
    let searchTimeout;

    if (elements.searchInput) {
        elements.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                updateFiltersFromUI();
                applyFilters();
            }, 300);
        });
    }

    const filterSelects = ['platformFilter', 'discountFilter', 'timeFilter', 'sortFilter'];
    filterSelects.forEach(id => {
        const el = elements[id];
        if (el) {
            el.addEventListener('change', () => {
                updateFiltersFromUI();
                applyFilters();
            });
        }
    });

    if (elements.clearFilters) {
        elements.clearFilters.addEventListener('click', clearAllFilters);
    }
}

// ========================================
// Main Initialization
// ========================================
async function init() {
    // Fetch dynamic config from Pages Function
    // Check if config has valid anonKey (after Cloudflare Pages env var substitution)
    if (!SUPABASE_CONFIG.anonKey || SUPABASE_CONFIG.anonKey === '%%SUPABASE_ANON_KEY%%') {
        hideLoading();
        const offersEl = document.getElementById('offers');
        if (offersEl) {
            offersEl.innerHTML = `
                <div class="empty">
                    <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                        <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                    <h2>Configuração necessária</h2>
                    <p>A chave Supabase não foi configurada. Configure <code>SUPABASE_ANON_KEY</code> no dashboard do Cloudflare Pages.</p>
                </div>
            `;
            offersEl.classList.remove('hidden');
        }
        return;
    }

    showLoading();
    setupBannerHandlers();
    setupEventListeners();

    // Restore saved filters
    const savedFilters = loadFilters();
    if (savedFilters) {
        currentFilters = { ...currentFilters, ...savedFilters };
    }
    updateUIFromFilters();

    try {
        allOffers = await fetchOffers();
        hideLoading();
        applyFilters();
    } catch (error) {
        hideLoading();
        const offersEl = document.getElementById('offers');
        if (offersEl) {
            offersEl.innerHTML = `
                <div class="empty">
                    <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 8v4M12 16h.01"/>
                    </svg>
                    <h2>Erro ao carregar</h2>
                    <p>${escapeHtml(error.message)}</p>
                    <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 1rem; width: auto;">Tentar novamente</button>
                </div>
            `;
            offersEl.classList.remove('hidden');
        }
    }
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Expose for manual retry from console
window.retryOffers = init;