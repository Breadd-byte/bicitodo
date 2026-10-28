// Lexical declarations for window functions to prevent ReferenceErrors
let setCategory, clearFilters, toggleCompare, clearCompare, openCompareModal, closeCompareModal, openProductDetail, openProductStore, openProductAction, closeModal, switchTab, activateExplorar, activateDeals, activateInternationalMode, openNovedadesModal, openProfileModal, openCountryModal, toggleMobileFilters, toggleFavorite, toggleFavoriteDetail, togglePriceAlert, toggleUserDropdown, openAuthModal, closeAuthModal, switchAuthTab, openAuthAlerts, handleAuthSubmit, handleLogout, renderAvatarHTML, selectSignupAvatar, changeAvatar, handleProductImageError, handleGoogleLogin, crearAlertaSupabase, toggleTheme, copyProductLink, scrollToStores, filterByStoreChip, clearBikeTypes, toggleFilterAccordion, toggleSpecChip, openBikeFitModal, updateBikeFitResult, applyBikeFitToCatalog, openBikeAdvisorModal, selectAdvisorOption, runBikeAdvisor, applyAdvisorToCatalog, copyCompareLink, shareCompareWhatsApp, selectInstantSearchItem, applyInstantSearchTerm;

// =============================================
// ANIMAL AVATARS & STYLING SYSTEM
// =============================================
const EMOJI_GRADIENTS = {
    '🦊': 'linear-gradient(135deg, #ef4444, #f97316)', // red to orange
    '🐱': 'linear-gradient(135deg, #f97316, #f43f5e)', // orange to rose
    '🐶': 'linear-gradient(135deg, #eab308, #f97316)', // yellow to orange
    '🐰': 'linear-gradient(135deg, #ec4899, #f43f5e)', // pink to rose
    '🦁': 'linear-gradient(135deg, #eab308, #d97706)', // gold to amber
    '🐼': 'linear-gradient(135deg, #64748b, #94a3b8)', // slate to silver
    '🐨': 'linear-gradient(135deg, #0d9488, #10b981)', // teal to emerald
    '🐸': 'linear-gradient(135deg, #22c55e, #10b981)', // green to emerald
    '🐯': 'linear-gradient(135deg, #f97316, #eab308)', // orange to gold
    '🐻': 'linear-gradient(135deg, #78350f, #a16207)'  // brown to bronze
};

renderAvatarHTML = function(avatar, size = "70px", borderWidth = "2.5px") {
    const isUrl = avatar && (
        avatar.startsWith('http') || 
        avatar.startsWith('assets') || 
        avatar.startsWith('/') || 
        avatar.includes('.jpg') || 
        avatar.includes('.png') || 
        avatar.includes('gravatar.com') ||
        avatar.includes('randomuser.me')
    );
    
    if (isUrl) {
        return `<img src="${avatar}" alt="Avatar" class="avatar-img-dynamic" style="width: ${size}; height: ${size}; border-radius: 50%; border: ${borderWidth} solid var(--primary); box-shadow: 0 0 12px var(--primary-glow); object-fit: cover; display: inline-flex; align-items: center; justify-content: center; vertical-align: middle;">`;
    } else {
        const emoji = avatar || '🦊';
        const gradient = EMOJI_GRADIENTS[emoji] || EMOJI_GRADIENTS['🦊'];
        return `
            <div class="avatar-emoji-dynamic" style="width: ${size}; height: ${size}; border-radius: 50%; border: ${borderWidth} solid var(--primary); box-shadow: 0 0 12px var(--primary-glow); background: ${gradient}; display: inline-flex; align-items: center; justify-content: center; font-size: calc(${size} * 0.55); line-height: 1; user-select: none; vertical-align: middle;">
                ${emoji}
            </div>
        `;
    }
};

selectSignupAvatar = function(emoji) {
    state.selectedSignupAvatar = emoji;
    renderAuthModalContent();
};

changeAvatar = async function(emoji) {
    if (!state.user) return;
    
    state.user.avatar = emoji;
    cacheAuthUserProfile(state.user);
    showToast(`¡Avatar actualizado a ${emoji}!`);
    
    // Save to local storage
    if (localStorage.getItem('bicitodo_mock_user')) {
        localStorage.setItem('bicitodo_mock_user', JSON.stringify(state.user));
    }

    // Repaint immediately; Firebase sync can take a moment on mobile.
    updateUserMenu();
    openProfileModal();
    render(false);
    
    // Save to Firebase/Firestore if enabled
    if (useFirebase && cloudAuth && cloudAuth.currentUser) {
        try {
            await firebasePersistenceReady;
            const uid = cloudAuth.currentUser.uid;
            await cloudAuth.currentUser.updateProfile({ photoURL: emoji });
            await cloudDb.collection('bicitodo_users').doc(uid).set({ avatar: emoji }, { merge: true });
        } catch (e) {
            console.error("Failed to sync avatar update to Firebase:", e);
        }
    }
    
};


// app.js - BiciTodo Logic v4.0 — Mercado Nacional Completo

// =============================================
// FIREBASE INITIALIZATION & FALLBACK
// =============================================
// Puedes reemplazar este objeto con tus credenciales reales obtenidas de la consola de Firebase.
// Si no las configuras, el sistema operará automáticamente en modo localStorage 100% funcional.
const FIREBASE_CONFIG = {
    apiKey: "AIzaSyAMUxP5zCu9T5w8tSJFzk4d008jUtCcpJg",
    authDomain: "bicitodo-7e61b.firebaseapp.com",
    projectId: "bicitodo-7e61b",
    storageBucket: "bicitodo-7e61b.firebasestorage.app",
    messagingSenderId: "1024845688521",
    appId: "1:1024845688521:web:debb6ee6fb4bed87196718"
};

let cloudDb = null;
let cloudAuth = null;
let useFirebase = false;
let firebasePersistenceReady = Promise.resolve();

function ensureFirebaseInitialized() {
    if (useFirebase && cloudAuth) return true;
    try {
        if (typeof firebase !== 'undefined' && FIREBASE_CONFIG.apiKey && FIREBASE_CONFIG.apiKey !== "YOUR_API_KEY") {
            if (!firebase.apps || firebase.apps.length === 0) {
                firebase.initializeApp(FIREBASE_CONFIG);
            }
            cloudAuth = firebase.auth();
            cloudDb = typeof firebase.firestore === 'function' ? firebase.firestore() : null;
            firebasePersistenceReady = cloudAuth.setPersistence(firebase.auth.Auth.Persistence.LOCAL).catch((error) => {
                console.warn("Firebase auth local persistence not enabled:", error);
            });
            if (cloudDb && typeof cloudDb.enablePersistence === 'function') {
                cloudDb.enablePersistence({ synchronizeTabs: true }).catch(() => {});
            }
            useFirebase = true;
            return true;
        }
    } catch (error) {
        console.warn("Failed to initialize Firebase:", error);
    }
    return false;
}

ensureFirebaseInitialized();

// =============================================
// CONFIGURACIÓN DE API
// =============================================
// Detecta automáticamente el entorno: en producción usa el mismo origen,
// en desarrollo local apunta al servidor FastAPI en el puerto 8000.
const API_BASE_URL = (typeof window.API_BASE_URL === 'string' && window.API_BASE_URL.trim() !== '') ? window.API_BASE_URL.trim() : (() => {
    if ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port && window.location.port !== '8000') {
        return 'http://127.0.0.1:8000';
    }
    return '';
})();

// =============================================
// CONFIGURACIÓN DE AFILIADOS Y MONETIZACIÓN
// =============================================
const AFFILIATE_CONFIG = {
    enabled: false,
    soicosId: "YOUR_SOICOS_ID",        // Reemplazar con tu ID de afiliado de Soicos (Chile)
    mercadolibreId: "91175643",        // ID de Mercado Libre Afiliados de Bastián (BASTIANMEDINA002)
    subid: "bicitodo"                  // ID de rastreo para saber que la venta vino de esta web
};

const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches || false;
const prefersReducedTransparency = window.matchMedia?.('(prefers-reduced-transparency: reduce)').matches || false;
const lowPowerDevice = (
    (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) ||
    (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
    prefersReducedMotion ||
    prefersReducedTransparency
);

if (lowPowerDevice) {
    document.documentElement.classList.add('perf-lite');
}

const state = {
    category: 'bicicletas',
    sortBy: 'relevant',
    isInternationalMode: false,
    filters: {
        search: '',
        priceMin: null,
        priceMax: null,
        stores: [],
        types: [],
        wheelSizes: [],
        brands: [],
        budgetRange: null,
        dynTypes: [],
        discountMin: null,
        aliexpressQuickFilter: 'all'
    },
    compare: [],       // IDs de productos en comparador (max 3)
    currentPage: 1,
    totalPages: 1,
    itemsPerPage: lowPowerDevice ? 8 : 12,
    data: {
        bicicletas: [],
        accesorios: [],
        repuestos: []
    },
    user: null,
    favorites: [],
    activeAuthTab: 'login',
    selectedSignupAvatar: '🦊',
    pendingProductId: null,
    pendingProductOpened: false
};

// =============================================
// HELPERS
// =============================================
const GOOGLE_AUTH_LOGO = `
    <svg class="google-auth-logo" width="18" height="18" viewBox="0 0 48 48" aria-hidden="true" style="width:18px;height:18px;min-width:18px;min-height:18px;flex-shrink:0;display:inline-block;">
        <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
        <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 6.1 29.3 4 24 4 16.3 4 9.6 8.3 6.3 14.7z" />
        <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.3C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.6 5.1C9.4 39.6 16.1 44 24 44z" />
        <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.1 5.5l6.2 5.3C36.9 39.3 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
    </svg>
`;

const AUTH_USER_CACHE_KEY = 'bicitodo_auth_user';

function cacheAuthUserProfile(user) {
    if (!user || !user.email) return;
    localStorage.setItem(AUTH_USER_CACHE_KEY, JSON.stringify({
        uid: user.uid || null,
        email: user.email,
        displayName: user.displayName || user.email.split('@')[0],
        avatar: user.avatar || user.photoURL || '🦊'
    }));
}

function getCachedAuthUserProfile() {
    try {
        const raw = localStorage.getItem(AUTH_USER_CACHE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function clearAuthUserProfileCache() {
    localStorage.removeItem(AUTH_USER_CACHE_KEY);
}

const formatCLP = (num) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(num);

function escapeHtml(value = '') {
    return String(value).replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    }[char]));
}

function slugifyProduct(value = '') {
    return String(value)
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 90);
}

function getProductSharePath(product = {}) {
    const slug = slugifyProduct(`${product.brand || ''} ${product.model || ''}`);
    return `?producto=${product.id}${slug ? `-${slug}` : ''}`;
}

function getProductShareUrl(product = {}) {
    return `${window.location.origin}${window.location.pathname}${getProductSharePath(product)}`;
}

function getProductIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('producto') || params.get('product') || '';
    const match = String(raw).match(/^(\d+)/);
    return match ? parseInt(match[1], 10) : null;
}

function ensureMetaTag(name, content, attr = 'name') {
    if (!content) return;
    let tag = document.head.querySelector(`meta[${attr}="${name}"]`);
    if (!tag) {
        tag = document.createElement('meta');
        tag.setAttribute(attr, name);
        document.head.appendChild(tag);
    }
    tag.setAttribute('content', content);
}

function updateProductSeo(product) {
    if (!product) return;
    const bestOffer = getBestProductOffer(product);
    const priceText = bestOffer?.price ? formatCLP(bestOffer.price) : 'mejor precio';
    const title = `${product.brand} ${product.model} desde ${priceText} | BiciTodo`;
    const description = `Compara precios de ${product.brand} ${product.model} en BiciTodo Chile. Revisa tiendas disponibles, historial de precio y enlace directo a la tienda.`;
    const url = getProductShareUrl(product);
    document.title = title;
    ensureMetaTag('description', description);
    ensureMetaTag('og:title', title, 'property');
    ensureMetaTag('og:description', description, 'property');
    ensureMetaTag('og:url', url, 'property');
    if (product.image) ensureMetaTag('og:image', new URL(product.image, window.location.origin).href, 'property');
}

function resetDefaultSeo() {
    document.title = 'BiciTodo | Compara Precios de Bicicletas en Chile — Mercado Completo';
    ensureMetaTag('description', 'Compara precios de bicicletas, accesorios y repuestos de ciclismo en tiendas chilenas. Encuentra el mejor precio y revisa ofertas disponibles por tienda.');
}

function getStoreInitials(offer = {}) {
    const rawName = String(offer.store || offer.storeKey || 'Tienda');
    const cleanedName = rawName
        .replace(/\b(chile|store|bikes?|bike|cl)\b/gi, '')
        .replace(/[^a-z0-9]+/gi, ' ')
        .trim();
    const source = cleanedName || rawName;
    const initials = source
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(word => word.charAt(0))
        .join('')
        .toUpperCase();

    return initials || String(offer.storeKey || 'T').slice(0, 2).toUpperCase();
}

const CYBER_END_TIME = new Date("2026-06-03T23:59:59-04:00");
let isCyberMode = false;

function isCyberActive() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('test_cyber') === 'expired') return false;
    if (urlParams.get('test_cyber') === 'active') return true;
    
    const now = new Date();
    return now < CYBER_END_TIME;
}

function generateRadarData(product) {
    let frameScore = 40;
    let transmissionScore = 40;
    let brakeScore = 40;
    let weightScore = 50;
    let valueScore = calculateValueScore(product) || 50;
    
    const specs = product.fullSpecs || {};
    const specText = (product.specs || '' + ' ' + Object.values(specs).join(' ')).toLowerCase();
    
    // 1. Cuadro
    if (specText.includes('carbon') || specText.includes('carbono')) {
        frameScore = 100;
    } else if (specText.includes('aluminio') || specText.includes('alloy')) {
        frameScore = 70;
    } else if (specText.includes('acero') || specText.includes('steel')) {
        frameScore = 40;
    }
    
    // 2. Transmisión
    if (specText.includes('di2') || specText.includes('axs') || specText.includes('xtr') || specText.includes('dura-ace')) {
        transmissionScore = 100;
    } else if (specText.includes('xt') || specText.includes('ultegra') || specText.includes('gx')) {
        transmissionScore = 85;
    } else if (specText.includes('deore') || specText.includes('105') || specText.includes('slx')) {
        transmissionScore = 75;
    } else if (specText.includes('tiagra') || specText.includes('sora') || specText.includes('alivio')) {
        transmissionScore = 55;
    }
    
    // 3. Frenos
    if (specText.includes('hidráulico') || specText.includes('hidraulico') || specText.includes('hydraulic')) {
        brakeScore = 100;
    } else if (specText.includes('disco mec') || specText.includes('mechanical disc')) {
        brakeScore = 70;
    } else if (specText.includes('v-brake') || specText.includes('freno de llanta')) {
        brakeScore = 50;
    }
    
    // 4. Peso
    let weightKg = null;
    const weightMatch = specText.match(/(\d+(?:\.\d+)?)\s*kg/);
    if (weightMatch) {
        weightKg = parseFloat(weightMatch[1]);
    }
    if (weightKg) {
        if (weightKg < 8.5) weightScore = 100;
        else if (weightKg < 10.5) weightScore = 85;
        else if (weightKg < 12.5) weightScore = 70;
        else if (weightKg < 14.5) weightScore = 55;
        else weightScore = 40;
    }
    
    return [frameScore, transmissionScore, brakeScore, weightScore, valueScore];
}

function renderRadarChart(products) {
    if (products.length < 2) return '';
    if (products.some(p => p.category !== 'bicicletas')) return '';
    
    const dimensions = ["Cuadro", "Transmisión", "Frenos", "Peso", "Calidad-Precio"];
    const centerX = 150;
    const centerY = 150;
    const maxRadius = 100;
    
    const angles = [
        -Math.PI / 2,
        -Math.PI / 2 + (2 * Math.PI / 5),
        -Math.PI / 2 + (4 * Math.PI / 5),
        -Math.PI / 2 + (6 * Math.PI / 5),
        -Math.PI / 2 + (8 * Math.PI / 5)
    ];
    
    let gridHtml = '';
    const gridLevels = [25, 50, 75, 100];
    gridLevels.forEach(level => {
        const radius = maxRadius * (level / 100);
        const points = angles.map(angle => {
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            return `${x},${y}`;
        }).join(' ');
        gridHtml += `<polygon points="${points}" fill="none" stroke="var(--border)" stroke-width="1.2" />`;
    });
    
    let spokeHtml = '';
    angles.forEach((angle, i) => {
        const x = centerX + maxRadius * Math.cos(angle);
        const y = centerY + maxRadius * Math.sin(angle);
        spokeHtml += `<line x1="${centerX}" y1="${centerY}" x2="${x}" y2="${y}" stroke="var(--border)" stroke-width="1.2" />`;
        
        const labelRadius = maxRadius + 20;
        const lx = centerX + labelRadius * Math.cos(angle);
        const ly = centerY + labelRadius * Math.sin(angle);
        
        let textAnchor = "middle";
        if (Math.cos(angle) > 0.1) textAnchor = "start";
        if (Math.cos(angle) < -0.1) textAnchor = "end";
        
        let dy = 4;
        if (i === 0) dy = -6;
        if (i === 2 || i === 3) dy = 10;
        
        spokeHtml += `<text x="${lx}" y="${ly + dy}" text-anchor="${textAnchor}" fill="var(--text-secondary)" font-size="0.65rem" font-family="var(--font-main)" font-weight="600" style="text-transform: uppercase; letter-spacing: 0.06em;">${dimensions[i]}</text>`;
    });
    
    const colors = [
        { stroke: "#20C968", fill: "rgba(32, 201, 104, 0.16)" },
        { stroke: "#0EA5E9", fill: "rgba(14, 165, 233, 0.14)" },
        { stroke: "#F59E0B", fill: "rgba(245, 158, 11, 0.14)" }
    ];
    
    let polygonsHtml = '';
    let legendHtml = '';
    
    products.forEach((p, idx) => {
        const color = colors[idx] || colors[0];
        const scores = generateRadarData(p);
        
        const points = angles.map((angle, i) => {
            const score = scores[i];
            const radius = maxRadius * (score / 100);
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            return `${x},${y}`;
        }).join(' ');
        
        polygonsHtml += `
            <polygon points="${points}" fill="${color.fill}" stroke="${color.stroke}" stroke-width="2.2" />
        `;
        
        legendHtml += `
            <div class="radar-legend-item">
                <span class="radar-legend-dot" style="background: ${color.stroke};"></span>
                <span>${escapeHtml(p.brand)} ${escapeHtml(p.model)}</span>
            </div>
        `;
    });
    
    return `
        <div class="radar-chart-wrapper">
            <span class="radar-chart-kicker"><i class="fa-solid fa-chart-Simple"></i> Análisis Comparativo de Especificaciones</span>
            <svg width="340" height="320" viewBox="0 0 340 320" class="radar-chart-svg">
                <g transform="translate(20, 14)">
                    ${gridHtml}
                    ${spokeHtml}
                    ${polygonsHtml}
                    <circle cx="${centerX}" cy="${centerY}" r="3" fill="var(--text-muted)" opacity="0.6" />
                </g>
            </svg>
            <div class="radar-legend">
                ${legendHtml}
            </div>
        </div>
    `;
}

function injectCyberCSS() {
    const styleId = "cyber-deals-injected-style";
    if (document.getElementById(styleId)) return;
    
    const style = document.createElement("style");
    style.id = styleId;
    style.innerHTML = `
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        body.cyber-theme {
            background-color: #0d061c !important;
            background-image: radial-gradient(circle at 50% 20%, #290833 0%, #0d061c 75%) !important;
            --primary: #ec4899 !important;
            --primary-dark: #be185d !important;
            --primary-glow: rgba(236, 72, 153, 0.25) !important;
            --accent: #a855f7 !important;
            --accent-glow: rgba(168, 85, 247, 0.2) !important;
        }
        
        body.cyber-theme .navbar {
            background: rgba(18, 9, 36, 0.85) !important;
            border-bottom-color: rgba(236, 72, 153, 0.2) !important;
        }
        
        body.cyber-theme .hero-premium h1 em {
            color: #ec4899 !important;
        }
        
        body.cyber-theme .badge-promo {
            background: rgba(236, 72, 153, 0.12) !important;
            border-color: rgba(236, 72, 153, 0.3) !important;
            color: #ec4899 !important;
        }
        
        body.cyber-theme .product-card.elite:hover {
            border-color: rgba(236, 72, 153, 0.35) !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4), 0 0 20px rgba(236, 72, 153, 0.15) !important;
        }
        
        body.cyber-theme .neon-price-pill {
            background: rgba(236, 72, 153, 0.15) !important;
            border-color: #ec4899 !important;
            color: #fff !important;
            box-shadow: 0 0 10px rgba(236, 72, 153, 0.3) !important;
        }
        
        body.cyber-theme .value-score-wrapper span {
            color: #ec4899 !important;
        }
        
        body.cyber-theme .value-score-wrapper div div {
            background: linear-gradient(90deg, #a855f7, #ec4899) !important;
            box-shadow: 0 0 8px rgba(236, 72, 153, 0.5) !important;
        }
    `;
    document.head.appendChild(style);
}

let countdownInterval;
function startCyberCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    
    const clockEl = document.getElementById('cyber-banner-clock');
    if (!clockEl) return;
    
    function updateClock() {
        const now = new Date();
        const diff = CYBER_END_TIME - now;
        
        if (diff <= 0) {
            clearInterval(countdownInterval);
            checkCyberStatus();
            return;
        }
        
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((diff / (1000 * 60)) % 60);
        const seconds = Math.floor((diff / 1000) % 60);
        
        const format = (n) => String(n).padStart(2, '0');
        let clockText = '';
        if (days > 0) {
            clockText = `${days}d : ${format(hours)}h : ${format(minutes)}m : ${format(seconds)}s`;
        } else {
            clockText = `${format(hours)}h : ${format(minutes)}m : ${format(seconds)}s`;
        }
        
        clockEl.innerText = clockText;
    }
    
    updateClock();
    countdownInterval = setInterval(updateClock, 1000);
}

function checkCyberStatus() {
    const navCyber = document.getElementById('nav-cyber');
    const cyberBanner = document.getElementById('cyber-countdown-banner');
    
    if (isCyberActive()) {
        if (navCyber) navCyber.style.display = 'inline-flex';
        if (cyberBanner) cyberBanner.style.display = 'block';
        startCyberCountdown();
    } else {
        if (navCyber) navCyber.style.display = 'none';
        if (cyberBanner) cyberBanner.style.display = 'none';
        if (isCyberMode) {
            isCyberMode = false;
            document.body?.classList.remove('cyber-theme');
            activateExplorar();
        }
    }
}

const STORE_RATINGS = {
    falabella: 4.5,
    ripley: 4.2,
    paris: 4.3,
    lider: 4.0,
    decathlon: 4.7,
    oxford: 4.6,
    trek: 4.8,
    specialized: 4.9,
    sparta: 4.4,
    faucon: 4.8,
    satiro: 4.7,
    totem: 4.3,
    copenhague: 4.6,
    dsbikes: 4.5,
    crossmountain: 4.6,
    fullbike: 4.4,
    vidaurre: 4.5,
    ibikes: 4.3,
    mercadolibre: 4.7,
    aliexpress: 4.8
};

function renderStoreRating(storeKey) {
    const rating = STORE_RATINGS[storeKey] || 4.5;
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 !== 0;
    let starsHtml = '';
    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            starsHtml += `<i class="fa-solid fa-star" style="color: #eab308; font-size: 0.72rem; margin-right: 1px;"></i>`;
        } else if (i === fullStars && hasHalf) {
            starsHtml += `<i class="fa-solid fa-star-half-stroke" style="color: #eab308; font-size: 0.72rem; margin-right: 1px;"></i>`;
        } else {
            starsHtml += `<i class="fa-regular fa-star" style="color: rgba(255,255,255,0.2); font-size: 0.72rem; margin-right: 1px;"></i>`;
        }
    }
    return `
        <div class="store-reputation" style="display: inline-flex; align-items: center; gap: 0.25rem; margin-left: 0.5rem;" title="Reputación de tienda: ${rating} de 5 estrellas">
            <span style="display: flex; align-items: center;">${starsHtml}</span>
            <span style="font-size: 0.72rem; font-weight: 700; color: #eab308; font-family: 'Poppins', sans-serif;">${rating.toFixed(1)}</span>
        </div>
    `;
}

function calculateValueScore(product) {
    if (product.category !== 'bicicletas') return null;
    
    let qualityScore = 55; // base score
    
    const specs = product.fullSpecs || {};
    const specText = (product.specs || '' + ' ' + Object.values(specs).join(' ')).toLowerCase();
    
    // 1. Frame Material (max 25 pts)
    if (specText.includes('carbon') || specText.includes('carbono')) {
        qualityScore += 25;
    } else if (specText.includes('aluminio') || specText.includes('alloy')) {
        qualityScore += 15;
    } else if (specText.includes('acero') || specText.includes('steel')) {
        qualityScore += 5;
    } else {
        qualityScore += 10;
    }
    
    // 2. Drivetrain (max 25 pts)
    if (specText.includes('di2') || specText.includes('axs') || specText.includes('xtr') || specText.includes('dura-ace')) {
        qualityScore += 25;
    } else if (specText.includes('xt') || specText.includes('ultegra') || specText.includes('gx')) {
        qualityScore += 22;
    } else if (specText.includes('deore') || specText.includes('105') || specText.includes('slx')) {
        qualityScore += 18;
    } else if (specText.includes('tiagra') || specText.includes('sora') || specText.includes('alivio')) {
        qualityScore += 12;
    } else if (specText.includes('claris') || specText.includes('acera') || specText.includes('altus')) {
        qualityScore += 8;
    } else {
        qualityScore += 10;
    }
    
    // 3. Brakes (max 20 pts)
    if (specText.includes('hidráulico') || specText.includes('hidraulico') || specText.includes('hydraulic')) {
        qualityScore += 20;
    } else if (specText.includes('disco mec') || specText.includes('mechanical disc')) {
        qualityScore += 12;
    } else if (specText.includes('v-brake') || specText.includes('freno de llanta')) {
        qualityScore += 8;
    } else {
        qualityScore += 10;
    }
    
    // 4. Weight (max 20 pts)
    let weightKg = null;
    const weightMatch = specText.match(/(\d+(?:\.\d+)?)\s*kg/);
    if (weightMatch) {
        weightKg = parseFloat(weightMatch[1]);
    }
    
    if (weightKg) {
        if (weightKg < 9) qualityScore += 20;
        else if (weightKg < 11) qualityScore += 16;
        else if (weightKg < 13) qualityScore += 12;
        else if (weightKg < 15) qualityScore += 8;
        else qualityScore += 4;
    } else {
        qualityScore += 12; // average weight points
    }
    
    // 5. Price factor
    const bestOffer = [...product.offers].sort((a, b) => a.price - b.price)[0];
    const price = bestOffer ? bestOffer.price : 500000;
    
    let expectedPrice = 300000;
    if (qualityScore > 60) expectedPrice = 600000;
    if (qualityScore > 75) expectedPrice = 1200000;
    if (qualityScore > 90) expectedPrice = 2500000;
    if (qualityScore > 105) expectedPrice = 4000000;
    
    let ratio = expectedPrice / price;
    if (ratio > 1.5) ratio = 1.5;
    if (ratio < 0.6) ratio = 0.6;
    
    let finalValueScore = Math.round((qualityScore / 130) * 85 + (ratio - 0.6) * 25);
    if (finalValueScore > 99) finalValueScore = 99;
    if (finalValueScore < 30) finalValueScore = 30;
    
    return finalValueScore;
}

const FALLBACK_PRODUCT_IMAGE = '/static/images/placeholder-bike.webp';

function isPlaceholderImage(src) {
    if (!src || typeof src !== 'string') return true;
    const clean = src.split('?')[0].toLowerCase();
    return clean.endsWith('/bike_0.jpg') ||
        clean.endsWith('/acc_0.jpg') ||
        clean.endsWith('/part_0.jpg') ||
        clean.endsWith('/placeholder-bike.png') ||
        clean.endsWith('/placeholder-bike.webp') ||
        /_[0]\.(jpg|jpeg|png|webp)$/.test(clean);
}

function resolveAssetUrl(src) {
    if (!src || typeof src !== 'string') return '';
    if (src.startsWith('/static/') && API_BASE_URL) {
        return API_BASE_URL + src;
    }
    return src;
}

function getProductFallbackImage() {
    return resolveAssetUrl(FALLBACK_PRODUCT_IMAGE);
}

function getProductImage(product = {}) {
    const offers = Array.isArray(product.offers) ? product.offers : [];
    const candidates = [
        product.image,
        product.original_img_url,
        ...offers.map(offer => offer && offer.imageUrl)
    ].filter(Boolean);

    const preferred = candidates.find(src => !isPlaceholderImage(src));
    return resolveAssetUrl(preferred || candidates[0] || FALLBACK_PRODUCT_IMAGE);
}

function getImageFallbacks(product = {}) {
    const offers = Array.isArray(product.offers) ? product.offers : [];
    const candidates = [
        product.original_img_url,
        ...offers.map(offer => offer && offer.imageUrl)
    ].filter(Boolean);
    // Filter out duplicates, placeholders, and local paths (to prevent redundant local 404 retries)
    const cleanCandidates = [...new Set(candidates)].filter(src => 
        src && 
        typeof src === 'string' && 
        !isPlaceholderImage(src) &&
        !src.startsWith('assets/') &&
        !src.startsWith('/static/')
    );
    cleanCandidates.push(FALLBACK_PRODUCT_IMAGE);
    return cleanCandidates;
}

handleProductImageError = window.handleProductImageError = function(img, fallbackSrc = FALLBACK_PRODUCT_IMAGE) {
    if (!img) return;
    
    const fallbacksAttr = img.getAttribute('data-fallbacks');
    if (fallbacksAttr) {
        const fallbacks = fallbacksAttr.split('|').filter(Boolean);
        if (fallbacks.length > 0) {
            const nextSrc = fallbacks.shift();
            img.setAttribute('data-fallbacks', fallbacks.join('|'));
            img.src = nextSrc;
            return;
        }
    }
    
    img.onerror = () => {
        img.onerror = null;
        img.src = "/static/images/placeholder-bike.webp";
    };
    img.src = fallbackSrc || FALLBACK_PRODUCT_IMAGE;
};

function isInternationalProduct(product = {}) {
    if (product.isInternational) return true;
    const offers = Array.isArray(product.offers) ? product.offers : [];
    return offers.some(offer => {
        const storeKey = (offer.storeKey || '').toLowerCase();
        const storeName = (offer.store || '').toLowerCase();
        return storeKey === 'aliexpress' || storeName.includes('aliexpress');
    });
}

function getCategoryTitle(cat) {
    if (cat === 'accesorios') return 'Catálogo de accesorios';
    if (cat === 'repuestos') return 'Catálogo de repuestos';
    return 'Catálogo de bicicletas';
}

function getCategorySubtitle(cat) {
    if (cat === 'accesorios') return 'Equipamiento, cascos y accesorios al mejor precio en Chile.';
    if (cat === 'repuestos') return 'Transmisiones, frenos y componentes de ciclismo comparados por tienda.';
    return 'Encuentra la bicicleta ideal para tu próxima aventura.';
}

function getInternationalTitle(cat) {
    if (cat === 'repuestos') return 'Componentes internacionales';
    return 'Accesorios internacionales';
}

function syncCatalogUiState() {
    const titleEl = document.getElementById('section-title');
    if (titleEl) {
        titleEl.innerText = state.isInternationalMode ? getInternationalTitle(state.category) : getCategoryTitle(state.category);
    }
    const subtitleEl = document.getElementById('section-subtitle');
    if (subtitleEl) {
        subtitleEl.innerText = state.isInternationalMode
            ? 'Selección de productos internacionales con envío directo a Chile.'
            : getCategorySubtitle(state.category);
    }

    const intlFiltersBar = document.getElementById('aliexpress-quick-filters');
    if (intlFiltersBar) {
        intlFiltersBar.style.display = state.isInternationalMode ? 'flex' : 'none';
    }

    const bikeFilters = document.querySelectorAll('.bike-only-filter');
    bikeFilters.forEach(el => {
        el.style.display = (!state.isInternationalMode && state.category === 'bicicletas') ? 'block' : 'none';
    });

    const bikeCategoryPill = document.getElementById('pill-bicis');
    if (bikeCategoryPill) {
        bikeCategoryPill.style.display = state.isInternationalMode ? 'none' : '';
    }

    const allTypesBtn = document.getElementById('btn-all-bike-types');
    if (allTypesBtn) {
        allTypesBtn.classList.toggle('active', (state.filters.types || []).length === 0);
    }

    if (state.filters.spec) {
            params.append('spec', state.filters.spec);
        }

        if (state.isInternationalMode) {
        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
        const navInt = document.getElementById('nav-internacional');
        if (navInt) navInt.classList.add('active');
    }
}

function applyInitialModeFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const mode = (params.get('mode') || '').toLowerCase();
    const hash = (window.location.hash || '').toLowerCase();
    const wantsInternational = mode === 'international' || mode === 'internacional' || hash === '#internacional';
    if (!wantsInternational) return;

    state.isInternationalMode = true;
    state.category = params.get('categoria') === 'repuestos' ? 'repuestos' : 'accesorios';
    state.filters.aliexpressQuickFilter = params.get('quick_filter') || 'all';
    state.currentPage = 1;

    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    const catPill = document.querySelector(`.pill[onclick="setCategory('${state.category}')"]`);
    if (catPill) catPill.classList.add('active');

    document.querySelectorAll('.quick-pill').forEach(p => {
        p.classList.toggle('active', p.dataset.filter === state.filters.aliexpressQuickFilter);
    });

    syncCatalogUiState();
}

const STORE_COLORS = {
    falabella: '#e73c3c',
    ripley: '#6b2fa0',
    paris:   '#003da5',
    lider:   '#00853e',
    decathlon: '#003DB6',
    oxford:  '#1a56db',
    trek:    '#f05500',
    specialized: '#e81c15',
    sparta:  '#ff6900',
    faucon:  '#0ea5e9',
    satiro:  '#6d28d9',
    totem:   '#059669',
    copenhague: '#14b8a6',
    dsbikes: '#06b6d4',
    mercadolibre: '#ffe600',
    crossmountain: '#16a34a',
    fullbike: '#dc2626',
    vidaurre: '#7c3aed',
    ibikes:  '#f58220',
    aliexpress: '#ff4747',
};

const STORE_DOMAINS = {
    falabella: 'falabella.com',
    ripley: 'simple.ripley.cl',
    paris: 'paris.cl',
    lider: 'lider.cl',
    decathlon: 'decathlon.cl',
    oxford: 'oxfordstore.cl',
    trek: 'trekbikes.com',
    specialized: 'specialized.com',
    sparta: 'sparta.cl',
    faucon: 'fauconbikes.cl',
    satiro: 'satirobikes.cl',
    totem: 'totem.cl',
    copenhague: 'copenhague.cl',
    dsbikes: 'dsbikes.cl',
    mercadolibre: 'mercadolibre.cl',
    crossmountain: 'crossmountain.cl',
    fullbike: 'fullbike.cl',
    vidaurre: 'vidaurrebikes.cl',
    ibikes: 'ibikes.cl',
    aliexpress: 'aliexpress.com'
};

const BLOCKED_SYNTHETIC_MODELS = new Set([
    'Orca M30 Carbon Road 2026',
    'S5 Ultegra Di2 Aero Road 2026',
    'Tarmac SL8 Pro Carbon 2026',
    'Specialissima Dura-Ace UltraLight 2026',
    'Dogma F Dura-Ace Di2 Super Premium 2026',
    'Oiz M30 Carbon Double Susp 2026',
    'Epic EVO Comp Carbon Double 2026',
    'Tallboy R Trail MTB 2026',
    'Nomad C Carbon Enduro Mullet 2026',
    'Rockhopper Comp 29 MTB 2026',
    'Diverge E5 Gravel 2026'
]);

function isBlockedSyntheticProduct(product) {
    return BLOCKED_SYNTHETIC_MODELS.has(product?.model || '');
}

function getStoreDot(storeKey) {
    const color = STORE_COLORS[storeKey] || '#64748b';
    return `<span class="store-dot" style="background:${color};"></span>`;
}

// Theme Toggle System (Zero-Flash Synchronous Theme)
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.documentElement?.classList.add('light-mode');
        document.body?.classList.add('light-mode');
        const themeBtnIcon = document.querySelector('#theme-toggle i');
        if (themeBtnIcon) {
            themeBtnIcon.className = 'fa-solid fa-moon';
        }
    } else {
        document.documentElement?.classList.remove('light-mode');
        document.body?.classList.remove('light-mode');
        const themeBtnIcon = document.querySelector('#theme-toggle i');
        if (themeBtnIcon) {
            themeBtnIcon.className = 'fa-solid fa-sun';
        }
    }
}

toggleTheme = window.toggleTheme = function() {
    const isLight = document.body?.classList.toggle('light-mode');
    document.documentElement?.classList.toggle('light-mode', Boolean(isLight));
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    const themeBtnIcon = document.querySelector('#theme-toggle i');
    if (themeBtnIcon) {
        themeBtnIcon.className = isLight ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        themeBtnIcon.style.transform = 'rotate(180deg)';
        themeBtnIcon.style.transition = 'transform 0.35s ease';
        setTimeout(() => {
            themeBtnIcon.style.transform = '';
            themeBtnIcon.style.transition = '';
        }, 350);
    }
    showToast(`Modo ${isLight ? 'Claro' : 'Oscuro'} activado`);
};

scrollToStores = window.scrollToStores = function(event) {
    if (event) event.preventDefault();
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navTiendas = document.getElementById('nav-tiendas');
    if (navTiendas) navTiendas.classList.add('active');
    openCountryModal();
};

filterByStoreChip = window.filterByStoreChip = function(storeKey) {
    if (!storeKey) return;
    isCyberMode = false;
    state.isInternationalMode = false;
    document.body?.classList.remove('cyber-theme');
    const isSame = state.filters.stores.length === 1 && state.filters.stores[0] === storeKey;
    state.filters.stores = isSame ? [] : [storeKey];
    state.currentPage = 1;
    document.querySelectorAll('.store-chip').forEach(chip => {
        const onclickVal = chip.getAttribute ? (chip.getAttribute('onclick') || '') : '';
        const matches = onclickVal.includes(`'${storeKey}'`);
        chip.classList.toggle('active', !isSame && Boolean(matches));
    });
    const catalogEl = document.getElementById('catalog');
    if (catalogEl && typeof window.scrollTo === 'function') {
        window.scrollTo({ top: (catalogEl.offsetTop || 0) - 72, behavior: 'smooth' });
    }
    render();
};

clearBikeTypes = window.clearBikeTypes = function() {
    state.filters.types = [];
    document.querySelectorAll('#type-filter-list input').forEach(i => { i.checked = false; });
    const allBtn = document.getElementById('btn-all-bike-types');
    if (allBtn) allBtn.classList.add('active');
    state.currentPage = 1;
    render();
};

toggleFilterAccordion = window.toggleFilterAccordion = function(btn) {
    if (!btn || !btn.closest) return;
    const group = btn.closest('.filter-group');
    if (!group) return;
    const isCollapsed = group.classList.toggle('collapsed');
    btn.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
};

// =============================================
// CORE FUNCTIONS
// =============================================
function initHeroVideo() {
    const heroVideo = document.getElementById('hero-bg-video');
    if (heroVideo && heroVideo.style) {
        heroVideo.muted = true;
        heroVideo.defaultMuted = true;
        heroVideo.volume = 0;
        if (typeof heroVideo.play === 'function') {
            const p = heroVideo.play();
            if (p && typeof p.catch === 'function') p.catch(() => {});
        }
    }
}

function init() {
    initTheme();
    initHeroVideo();
    setupEventListeners();
    injectCyberCSS();
    checkCyberStatus();
    state.pendingProductId = getProductIdFromUrl();
    applyInitialModeFromUrl();
    loadRealData();
    setupFirebaseAuthListener();
}

async function loadRealData() {
    if (!state.data.cache) state.data.cache = {};

    // ADVERTENCIA: El archivo data.json (9.3MB) NO debe cargarse como fallback en producción.
    // Su carga bloquearía la red principal del usuario. Úsalo solo como referencia de desarrollo.
    // La app obtiene todos los datos desde la FastAPI (API_BASE_URL).
    
    // Renders static/metadata elements first
    updateStats();
    renderWheelFilter();
    renderBudgetFilter();
    
    // Perform initial dynamic load from the FastAPI server!
    render();
}

async function updateStats() {
    const statBicis = document.querySelector('.stat-bicis');
    const statAcc = document.querySelector('.stat-accesorios');
    const statRep = document.querySelector('.stat-repuestos');
    const statTiendas = document.querySelector('.stat-tiendas');
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`, { cache: 'no-store' });
        if (!response.ok) throw new Error('stats unavailable');
        const stats = await response.json();
        if (statBicis) statBicis.textContent = stats.bicicletas || '0';
        if (statAcc) statAcc.textContent = stats.accesorios || '0';
        if (statRep) statRep.textContent = stats.repuestos || '0';
        if (statTiendas) statTiendas.textContent = stats.tiendas || '0';
    } catch (e) {
        console.warn("Stats API offline, keeping catalog counts");
    }
}

function renderBrandFilter() {
    const counts = state.brandsMetadata || {};
    const sortedBrands = Object.entries(counts)
        .filter(([brand, count]) => count > 0)
        .sort((a, b) => a[0].localeCompare(b[0]));
        
    const container = document.getElementById('brand-filter-list');
    if (!container) return;
    
    const scrollTop = container.scrollTop;
    
    container.innerHTML = sortedBrands.map(([b, count]) => {
        const isChecked = state.filters.brands.includes(b.toLowerCase()) ? 'checked' : '';
        return `
            <label class="filter-option-row">
                <span class="filter-option-left"><input type="checkbox" class="brand-check" value="${b.toLowerCase()}" ${isChecked}> <span>${escapeHtml(b)}</span></span>
                <span class="filter-count">${count}</span>
            </label>
        `;
    }).join('');
    
    container.scrollTop = scrollTop;
    
    container.querySelectorAll('.brand-check').forEach(input => {
        input.addEventListener('change', () => { updateBrandFilters(); state.currentPage = 1; render(); });
    });
}

function renderTypeFilter() {
    const dynContainer = document.getElementById('dynamic-type-filter-group');
    if (!dynContainer) return;

    if (state.category === 'bicicletas') {
        dynContainer.style.display = 'none';
        
        const counts = state.typesMetadata || { 'mtb': 0, 'ruta': 0, 'gravel': 0, 'fixie': 0, 'urbana': 0, 'hibrida': 0, 'infantil': 0, 'electrica': 0 };
        const typeContainer = document.getElementById('type-filter-list');
        const allTypesBtn = document.getElementById('btn-all-bike-types');
        if (allTypesBtn) {
            allTypesBtn.classList.toggle('active', (state.filters.types || []).length === 0);
        }
        if (typeContainer) {
            typeContainer.querySelectorAll('label').forEach(label => {
                const input = label.querySelector('input');
                if (input) {
                    const type = input.value;
                    const count = counts[type] || 0;
                    const isChecked = state.filters.types.includes(type) ? 'checked' : '';
                    
                    const labelText = {
                        'mtb': 'Montaña',
                        'ruta': 'Ruta',
                        'gravel': 'Gravel',
                        'fixie': 'Fixie / Single-speed',
                        'urbana': 'Urbana',
                        'hibrida': 'Híbrida',
                        'infantil': 'Infantil',
                        'electrica': 'Eléctrica'
                    }[type] || type.toUpperCase();

                    label.className = 'filter-option-row';
                    label.innerHTML = `<span class="filter-option-left"><input type="checkbox" class="type-check" value="${type}" ${isChecked}> <span>${labelText}</span></span> <span class="filter-count">${count}</span>`;
                    label.style.display = count === 0 ? 'none' : 'flex';
                }
            });
            typeContainer.querySelectorAll('.type-check').forEach(input => {
                input.addEventListener('change', () => {
                    const checked = typeContainer.querySelectorAll('.type-check:checked');
                    state.filters.types = Array.from(checked).map(i => i.value);
                    if (allTypesBtn) {
                        allTypesBtn.classList.toggle('active', state.filters.types.length === 0);
                    }
                    state.currentPage = 1;
                    render();
                });
            });
        }
        return;
    }
    
    // Accesorios / Repuestos dynamic types from server metadata
    const counts = state.typesMetadata || {};
    const sortedTypes = Object.entries(counts)
        .filter(([t, count]) => t && t !== 'accesorios' && t !== 'repuestos' && count > 0)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
        
    if (sortedTypes.length === 0) {
        dynContainer.style.display = 'none';
        return;
    }

    const dynList = document.getElementById('dyn-type-filter-list');
    const dynScrollTop = dynList ? dynList.scrollTop : 0;

    const label = state.category === 'accesorios' ? 'Tipo de accesorio' : 'Tipo de componente';
    dynContainer.innerHTML = `
        <button type="button" class="filter-accordion-header" onclick="toggleFilterAccordion(this)" aria-expanded="true">
            <span>${label}</span>
            <i class="fa-solid fa-chevron-up"></i>
        </button>
        <div class="filter-group-body">
            <div class="checkbox-list" id="dyn-type-filter-list">
                ${sortedTypes.map(([t, count]) => {
                    const isChecked = state.filters.dynTypes.includes(t.toLowerCase()) ? 'checked' : '';
                    return `
                        <label class="filter-option-row">
                            <span class="filter-option-left"><input type="checkbox" class="dyn-type-check" value="${t.toLowerCase()}" ${isChecked}> <span>${escapeHtml(t)}</span></span>
                            <span class="filter-count">${count}</span>
                        </label>
                    `;
                }).join('')}
            </div>
        </div>
    `;
    dynContainer.style.display = 'block';

    const newDynList = document.getElementById('dyn-type-filter-list');
    if (newDynList) {
        newDynList.scrollTop = dynScrollTop;
    }

    dynContainer.querySelectorAll('.dyn-type-check').forEach(input => {
        input.addEventListener('change', () => { updateDynTypeFilters(); state.currentPage = 1; render(); });
    });
}

function renderWheelFilter() {
    if (state.category !== 'bicicletas') return;
    document.querySelectorAll('.wheel-pill').forEach(pill => {
        const size = pill.dataset.size;
        pill.innerHTML = size.includes('700') ? `700c` : `${size}"`;
        pill.style.display = 'inline-block';
    });
}

function renderBudgetFilter() {
    document.querySelectorAll('.budget-pill').forEach(pill => {
        const range = pill.dataset.range;
        let label = '';
        if (range === 'sub100') label = 'Hasta $100k';
        else if (range === '100-200') label = '$100k – $200k';
        else if (range === '200-400') label = '$200k – $400k';
        else if (range === '400-800') label = '$400k – $800k';
        else if (range === '800plus') label = '$800k+';
        pill.innerHTML = label;
        pill.style.display = 'inline-block';
    });
}


function updateDynTypeFilters() {
    const checked = document.querySelectorAll('.dyn-type-check:checked');
    state.filters.dynTypes = Array.from(checked).map(i => i.value);
}

function updateBrandFilters() {
    const checked = document.querySelectorAll('.brand-check:checked');
    state.filters.brands = Array.from(checked).map(i => i.value);
}

function setupEventListeners() {
    initInstantSearch();
    let searchTimeout;
    document.getElementById('main-search').addEventListener('input', (e) => {
        const val = e.target.value.toLowerCase();
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.filters.search = val;
            state.currentPage = 1;
            render();
        }, 150); // 150ms debounce delay to keep search typing incredibly fluid and lag-free
    });

    let priceTimeout;
    document.getElementById('price-min').addEventListener('input', (e) => {
        const val = e.target.value ? parseInt(e.target.value) : null;
        clearTimeout(priceTimeout);
        priceTimeout = setTimeout(() => {
            state.filters.priceMin = val;
            state.currentPage = 1;
            render();
        }, 300);
    });
    document.getElementById('price-max').addEventListener('input', (e) => {
        const val = e.target.value ? parseInt(e.target.value) : null;
        clearTimeout(priceTimeout);
        priceTimeout = setTimeout(() => {
            state.filters.priceMax = val;
            state.currentPage = 1;
            render();
        }, 300);
    });

    document.querySelectorAll('.checkbox-list input').forEach(input => {
        input.addEventListener('change', () => { updateCheckboxFilters(); state.currentPage = 1; render(); });
    });

    document.querySelector('.sort-dropdown').addEventListener('change', (e) => {
        state.sortBy = e.target.value;
        render();
    });

    // AliExpress quick filter pills
    document.querySelectorAll('.quick-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.quick-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            state.filters.aliexpressQuickFilter = pill.dataset.filter;
            state.currentPage = 1;
            render();
        });
    });

    // Budget range pills
    document.querySelectorAll('.budget-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.budget-pill').forEach(p => p.classList.remove('active'));
            if (state.filters.budgetRange === pill.dataset.range) {
                state.filters.budgetRange = null;
            } else {
                pill.classList.add('active');
                state.filters.budgetRange = pill.dataset.range;
            }
            state.currentPage = 1;
            render();
        });
    });

    // Wheel size pills
    document.querySelectorAll('.wheel-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            pill.classList.toggle('active');
            updateWheelFilters();
            state.currentPage = 1;
            render();
        });
    });

    // Modal close
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target === document.getElementById('modal-overlay')) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Comparator bar
    document.getElementById('compare-clear')?.addEventListener('click', clearCompare);
    document.getElementById('compare-now')?.addEventListener('click', openCompareModal);

    // Compare modal close
    document.getElementById('compare-modal-overlay')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('compare-modal-overlay')) closeCompareModal();
    });

    // Pagination
    document.querySelector('.btn-page.prev')?.addEventListener('click', () => {
        if (state.currentPage > 1) { state.currentPage--; render(); window.scrollTo({top: document.getElementById('catalog').offsetTop - 80, behavior: 'smooth'}); }
    });
    document.querySelector('.btn-page.next')?.addEventListener('click', () => {
        if (state.currentPage < state.totalPages) { state.currentPage++; render(); window.scrollTo({top: document.getElementById('catalog').offsetTop - 80, behavior: 'smooth'}); }
    });

    // Navbar scroll state
    if (typeof window.addEventListener === 'function') {
        window.addEventListener('scroll', () => {
            const nav = document.querySelector('.navbar');
            if (nav) {
                nav.classList.toggle('scrolled', (window.scrollY || 0) > 24);
            }
        }, { passive: true });
    }
}

function updateCheckboxFilters() {
    const typeInputs = document.querySelectorAll('#type-filter-list input:checked');
    state.filters.types = Array.from(typeInputs).map(i => i.value);
}

function updateWheelFilters() {
    state.filters.wheelSizes = Array.from(document.querySelectorAll('.wheel-pill.active')).map(p => p.dataset.size);
}

setCategory = window.setCategory = function(cat) {
    state.category = cat;
    state.currentPage = 1;
    
    if (cat === 'bicicletas') {
        state.isInternationalMode = false;
        document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
        const navExplorar = document.getElementById('nav-catalogo');
        if (navExplorar) navExplorar.classList.add('active');
    }
    
    const preservedDiscountMin = state.filters.discountMin;
    // Reset filters on category changes so each section starts clean and predictable.
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: preservedDiscountMin, aliexpressQuickFilter: 'all', spec: null }; document.querySelectorAll('.component-tier-pill').forEach(p => p.classList.remove('active'));
    
    // Reset quick pills active state in UI
    document.querySelectorAll('.quick-pill').forEach(p => {
        if (p.dataset.filter === 'all') p.classList.add('active');
        else p.classList.remove('active');
    });
    
    // Reset UI states for filters
    document.getElementById('main-search').value = '';
    document.getElementById('price-min').value = '';
    document.getElementById('price-max').value = '';
    document.querySelectorAll('#type-filter-list input').forEach(i => i.checked = false);
    document.querySelectorAll('.checkbox-list input, .brand-check, .dyn-type-check').forEach(i => i.checked = false);
    document.querySelectorAll('.wheel-pill, .budget-pill').forEach(p => p.classList.remove('active'));
    
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    document.querySelector(`.pill[onclick="setCategory('${cat}')"]`).classList.add('active');
    
    let title = 'Catálogo de Bicicletas';
    if (cat === 'accesorios') title = 'Accesorios y Equipamiento';
    else if (cat === 'repuestos') title = 'Componentes y Repuestos';
    
    document.getElementById('section-title').innerText = title;
    
    // Show/hide bicycle-specific filters
    const bikeFilters = document.querySelectorAll('.bike-only-filter');
    if (cat === 'bicicletas') {
        bikeFilters.forEach(el => el.style.display = 'block');
    } else {
        bikeFilters.forEach(el => el.style.display = 'none');
    }
    
    syncCatalogUiState();

    // Dynamically update brand + type + wheel + budget filters for the new category
    renderBrandFilter();
    renderTypeFilter();
    renderWheelFilter();
    renderBudgetFilter();
    
    render();
};

clearFilters = window.clearFilters = function() {
    isCyberMode = false;
    state.isInternationalMode = false;
    document.body?.classList.remove('cyber-theme');
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: null, aliexpressQuickFilter: 'all', spec: null }; document.querySelectorAll('.component-tier-pill').forEach(p => p.classList.remove('active'));
    state.currentPage = 1;
    document.getElementById('main-search').value = '';
    document.getElementById('price-min').value = '';
    document.getElementById('price-max').value = '';
    document.querySelectorAll('.checkbox-list input, .brand-check, .dyn-type-check').forEach(i => i.checked = false);
    document.querySelectorAll('.wheel-pill, .budget-pill').forEach(p => p.classList.remove('active'));
    
    // Reset quick pills active state in UI
    document.querySelectorAll('.quick-pill').forEach(p => {
        if (p.dataset.filter === 'all') p.classList.add('active');
        else p.classList.remove('active');
    });
    syncCatalogUiState();
    
    render();
};

// =============================================
// COMPARATOR
// =============================================
toggleCompare = window.toggleCompare = function(productId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const idx = state.compare.indexOf(productId);
    if (idx > -1) {
        state.compare.splice(idx, 1);
        showToast(`Producto quitado del comparador (${state.compare.length}/3).`);
    } else {
        if (state.compare.length >= 3) {
            showToast('Puedes comparar hasta 3 productos a la vez.');
            return;
        }
        state.compare.push(productId);
        if (state.compare.length === 1) {
            showToast('Agregado al comparador (1/3). Selecciona al menos 1 más para comparar.');
        } else {
            showToast(`Agregado al comparador (${state.compare.length}/3). Pulsa "Comparar ahora" abajo.`);
        }
    }
    updateCompareBar();
    render(false);
};

function updateCompareBar() {
    const bar = document.getElementById('compare-bar');
    const countEl = document.getElementById('compare-count');
    if (!bar) return;
    if (state.compare.length > 0) {
        bar.classList.add('visible');
        bar.classList.add('active');
        if (countEl) countEl.textContent = state.compare.length;
    } else {
        bar.classList.remove('visible');
        bar.classList.remove('active');
        if (countEl) countEl.textContent = '0';
    }
}

clearCompare = window.clearCompare = function() {
    state.compare = [];
    updateCompareBar();
    render(false);
};

openCompareModal = window.openCompareModal = function() {
    const products = state.compare.map(id => findProductById(id)).filter(Boolean);
    if (products.length < 2) {
        showToast('Selecciona al menos 2 productos usando el icono de balanza en cada tarjeta.');
        return;
    }

    // Build all unique spec keys + core summary rows
    const allKeys = [...new Set(products.flatMap(p => Object.keys(p.fullSpecs || {})))];

    const parsedWeights = products.map(p => {
        const wStr = String(p.fullSpecs?.["Peso Aproximado"] || p.fullSpecs?.["Peso"] || '');
        const m = wStr.match(/(\d+(?:\.\d+)?)/);
        return m ? parseFloat(m[1]) : Infinity;
    });
    const minWeight = Math.min(...parsedWeights);

    const parsedPrices = products.map(p => Math.min(...(p.offers || []).map(o => o.price)));
    const minPrice = Math.min(...parsedPrices);

    const parsedFrames = products.map(p => {
        const fStr = String(p.fullSpecs?.["Cuadro"] || '').toLowerCase();
        if (fStr.includes('carbon')) return 3;
        if (fStr.includes('aluminio') || fStr.includes('alloy')) return 2;
        if (fStr.includes('acero') || fStr.includes('steel')) return 1;
        return 0;
    });
    const maxFrameTier = Math.max(...parsedFrames);

    const parsedBrakes = products.map(p => {
        const bStr = String(p.fullSpecs?.["Frenos"] || '').toLowerCase();
        if (bStr.includes('hidráulico') || bStr.includes('hidraulico') || bStr.includes('hydraulic')) return 2;
        if (bStr.includes('disco') || bStr.includes('disc')) return 1;
        return 0;
    });
    const maxBrakeTier = Math.max(...parsedBrakes);

    const colsHtml = products.map(p => {
        const bestOffer = getBestProductOffer(p) || { price: 0, store: 'Tienda' };
        const bestPrice = bestOffer.price || 0;
        const isCheapest = bestPrice === minPrice && products.length > 1 && products.some(p2 => (getBestProductOffer(p2)?.price || 0) > minPrice);
        const valScore = calculateValueScore(p);
        
        return `
            <div class="compare-col ${isCheapest ? 'is-cheapest' : ''}">
                ${isCheapest ? `<span class="compare-best-badge">Mejor Precio</span>` : ''}
                <div class="compare-img-wrap">
                    <img src="${getProductImage(p)}" alt="${escapeHtml(p.model)}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)">
                </div>
                <span class="compare-brand">${escapeHtml(p.brand)}</span>
                <h4 class="compare-model">${escapeHtml(p.model)}</h4>
                ${valScore ? `
                    <div class="compare-score-chip">
                        <span>Calidad-Precio:</span>
                        <strong>${valScore}/100</strong>
                    </div>
                ` : ''}
                <div class="compare-best-price">
                    <span class="compare-price-label">Desde</span>
                    <span class="compare-price-val">${formatCLP(bestPrice)}</span>
                    <span class="compare-store-note">en ${escapeHtml(bestOffer.store || 'Tienda')}</span>
                </div>
                <div class="compare-col-actions">
                    <a href="${getProductUrl(bestOffer)}" target="_blank" rel="noopener" class="btn-minimal-primary btn-compare-buy">
                        Ver oferta <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    </a>
                </div>
            </div>
        `;
    }).join('');

    const rowsHtml = allKeys.length > 0 ? allKeys.map(key => {
        const cells = products.map(p => {
            let val = p.fullSpecs?.[key] || '—';
            let isSuperior = false;
            
            if (key === "Cuadro" && maxFrameTier > 0) {
                const tier = String(val).toLowerCase().includes('carbon') ? 3 : (String(val).toLowerCase().includes('aluminio') || String(val).toLowerCase().includes('alloy') ? 2 : 1);
                if (tier === maxFrameTier && products.some(p2 => {
                    const f2 = String(p2.fullSpecs?.["Cuadro"] || '').toLowerCase();
                    const t2 = f2.includes('carbon') ? 3 : (f2.includes('aluminio') || f2.includes('alloy') ? 2 : 1);
                    return t2 < maxFrameTier;
                })) {
                    isSuperior = true;
                }
            }
            
            if ((key === "Peso Aproximado" || key === "Peso") && minWeight !== Infinity) {
                const wStr = String(val);
                const m = wStr.match(/(\d+(?:\.\d+)?)/);
                const w = m ? parseFloat(m[1]) : Infinity;
                if (w === minWeight && products.some(p2 => {
                    const wStr2 = String(p2.fullSpecs?.[key] || '');
                    const m2 = wStr2.match(/(\d+(?:\.\d+)?)/);
                    const w2 = m2 ? parseFloat(m2[1]) : Infinity;
                    return w2 > minWeight;
                })) {
                    isSuperior = true;
                }
            }
            
            if ((key === "Frenos" || key === "Freno") && maxBrakeTier > 0) {
                const bStr = String(val).toLowerCase();
                const tier = bStr.includes('hidráulico') || bStr.includes('hidraulico') || bStr.includes('hydraulic') ? 2 : (bStr.includes('disco') || bStr.includes('disc') ? 1 : 0);
                if (tier === maxBrakeTier && products.some(p2 => {
                    const b2 = String(p2.fullSpecs?.[key] || '').toLowerCase();
                    const t2 = b2.includes('hidráulico') || b2.includes('hidraulico') || b2.includes('hydraulic') ? 2 : (b2.includes('disco') || b2.includes('disc') ? 1 : 0);
                    return t2 < maxBrakeTier;
                })) {
                    isSuperior = true;
                }
            }
            
            const cellClass = isSuperior ? 'class="compare-cell-superior"' : '';
            const checkIcon = isSuperior ? `<i class="fa-solid fa-circle-check"></i> ` : '';
            
            return `<td ${cellClass}>${checkIcon}${escapeHtml(String(val))}</td>`;
        }).join('');
        
        return `<tr><th>${escapeHtml(key)}</th>${cells}</tr>`;
    }).join('') : `
        <tr>
            <th>Resumen</th>
            ${products.map(p => `<td>${escapeHtml(getProductSummary(p))}</td>`).join('')}
        </tr>
        <tr>
            <th>Tiendas con stock</th>
            ${products.map(p => `<td>${(p.offers || []).length} tienda(s)</td>`).join('')}
        </tr>
    `;

    const radarChartHtml = renderRadarChart(products);

    document.getElementById('compare-modal-overlay').innerHTML = `
        <div class="compare-modal-content">
            <button class="modal-close" onclick="closeCompareModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
            <div class="modal-minimal-header" style="margin-bottom: 1.5rem;">
                <span class="modal-minimal-eyebrow">Comparador BiciTodo</span>
                <div class="compare-header-top-row">
                    <div>
                        <h2 class="modal-minimal-title">Comparación de Modelos (${products.length})</h2>
                        <p class="modal-minimal-subtitle">Compara precios, tiendas y especificaciones técnicas lado a lado.</p>
                    </div>
                    <div class="compare-share-actions">
                        <button type="button" class="modal-share-link" style="margin-bottom:0;" onclick="copyCompareLink()">
                            <i class="fa-solid fa-link"></i> Copiar enlace
                        </button>
                        <button type="button" class="modal-share-link btn-whatsapp-share" style="margin-bottom:0;" onclick="shareCompareWhatsApp()">
                            <i class="fa-brands fa-whatsapp"></i> Compartir en WhatsApp
                        </button>
                    </div>
                </div>
            </div>
            <div class="compare-cols">${colsHtml}</div>
            ${radarChartHtml}
            <div class="compare-table-wrap">
                <table class="compare-table">
                    <thead><tr><th>Especificación</th>${products.map(p => `<th>${escapeHtml(p.brand)} ${escapeHtml(p.model)}</th>`).join('')}</tr></thead>
                    <tbody>${rowsHtml}</tbody>
                </table>
            </div>
        </div>
    `;
    document.getElementById('compare-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
};

closeCompareModal = window.closeCompareModal = function() {
    document.getElementById('compare-modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
};

// =============================================
// PRODUCT DETAIL MODAL
// =============================================
function getRawProductUrl(offer) {
    if (offer.url && offer.url !== '#' && offer.url.startsWith('http')) {
        if (offer.storeKey === 'aliexpress') {
            try {
                const target = new URL(offer.url);
                if (!target.hostname.toLowerCase().includes('aliexpress.') || target.pathname.includes('1005001234')) return '#';
            } catch (_) {
                return '#';
            }
        }
        return offer.url;
    }
    return getStoreSearchUrl(offer.storeKey, '', '', '#');
}

function getProductUrl(offer) {
    const rawUrl = getRawProductUrl(offer);
    if (!rawUrl || rawUrl === '#') return '#';
    if (!AFFILIATE_CONFIG.enabled) return rawUrl;

    // Prioritize the store's real product page unless affiliate credentials are
    // truly configured. This keeps "Ver en tienda" reliable for users.
    const hasRealSoicos = AFFILIATE_CONFIG.soicosId && AFFILIATE_CONFIG.soicosId !== "YOUR_SOICOS_ID";
    const hasRealMeli = AFFILIATE_CONFIG.mercadolibreId && AFFILIATE_CONFIG.mercadolibreId !== "YOUR_MELI_ID";
    if (offer.storeKey !== 'mercadolibre' && !hasRealSoicos) return rawUrl;
    if (offer.storeKey === 'mercadolibre' && !hasRealMeli) return rawUrl;

    const encodedUrl = encodeURIComponent(rawUrl);

    // Enrutador inteligente de Redes de Afiliados por tienda en Chile
    switch(offer.storeKey) {
        case 'mercadolibre':
            if (AFFILIATE_CONFIG.mercadolibreId && AFFILIATE_CONFIG.mercadolibreId !== "YOUR_MELI_ID") {
                // Formato oficial de redirección de afiliados de Mercado Libre
                return `https://click.mercadolibre.cl/ms/api/v1/redirect?link=${encodedUrl}&id=${AFFILIATE_CONFIG.mercadolibreId}`;
            }
            break;
            
        case 'falabella':
        case 'ripley':
        case 'paris':
        case 'lider':
        case 'decathlon':
        case 'sparta':
            if (AFFILIATE_CONFIG.soicosId && AFFILIATE_CONFIG.soicosId !== "YOUR_SOICOS_ID") {
                // Mapeo inteligente de IDs de campaña en la red Soicos (Chile)
                const campaignIds = {
                    falabella: "10542", // Campaña Falabella en Soicos
                    ripley: "11231",    // Campaña Ripley en Soicos
                    paris: "10984",     // Campaña Paris en Soicos
                    lider: "12456",     // Campaña Lider en Soicos
                    decathlon: "11582", // Campaña Decathlon en Soicos
                    sparta: "10874"     // Campaña Sparta en Soicos
                };
                const cId = campaignIds[offer.storeKey] || "general";
                return `https://t.soicos.com/c/${cId}/${AFFILIATE_CONFIG.soicosId}/?deeplink=${encodedUrl}&subid=${AFFILIATE_CONFIG.subid}`;
            }
            break;
    }

    // Retornar la URL original si no hay credenciales configuradas aún
    return rawUrl;
}

function getStoreSearchUrl(storeKey, brand, model, fallbackUrl) {
    // Solo se usa si no hay URL directa del producto
    if (fallbackUrl && fallbackUrl !== '#' && fallbackUrl.startsWith('http')) {
        return fallbackUrl;
    }
    const q = encodeURIComponent(((brand || '') + ' ' + (model || '')).trim());
    switch(storeKey) {
        case 'falabella':   return `https://www.falabella.com/falabella-cl/search?Ntt=${q}`;
        case 'ripley':      return `https://simple.ripley.cl/buscar?query=${q}`;
        case 'paris':       return `https://www.paris.cl/search?q=${q}`;
        case 'decathlon':   return `https://www.decathlon.cl/search?q=${q}`;
        case 'oxford':      return `https://www.oxfordstore.cl/catalogsearch/result/?q=${q}`;
        case 'sparta':      return `https://sparta.cl/catalogsearch/result/?q=${q}`;
        case 'satiro':      return `https://satirobikes.cl/search?q=${q}`;
        case 'faucon':      return `https://fauconbikes.cl/search?q=${q}`;
        case 'copenhague':  return `https://www.copenhague.cl/buscar?q=${q}`;
        case 'dsbikes':     return `https://www.dsbikes.cl/search?q=${q}`;
        case 'trek':        return `https://www.trek.cl/search?q=${q}`;
        case 'mercadolibre': return `https://listado.mercadolibre.cl/${q}`;
        case 'ibikes':      return `https://ibikes.cl/?s=${q}&post_type=product`;
        default: return fallbackUrl || '#';
    }
}

function findProductById(productId) {
    const allProducts = [...state.data.bicicletas, ...state.data.accesorios, ...state.data.repuestos];
    return allProducts.find(p => p.id === productId) || (state.data.cache && state.data.cache[productId]);
}

function getBestProductOffer(product = {}) {
    const offers = Array.isArray(product.offers) ? product.offers : [];
    return [...offers].sort((a, b) => (a.price || 0) - (b.price || 0))[0];
}

function getOfferHistoryPoints(offer = {}) {
    const history = Array.isArray(offer.history) ? offer.history : [];
    const points = history
        .map(item => ({
            price: Number(item?.price || item),
            timestamp: item?.timestamp || offer.lastUpdated || null
        }))
        .filter(item => Number.isFinite(item.price) && item.price > 0);

    if (!points.length && offer.price) {
        points.push({ price: Number(offer.price), timestamp: offer.lastUpdated || null });
    }
    return points.slice(-8);
}

function formatHistoryDate(value) {
    if (!value) return 'Actual';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Actual';
    return date.toLocaleDateString('es-CL', { day: '2-digit', month: 'short' });
}

function renderStoreHistory(product = {}) {
    const offers = Array.isArray(product.offers) ? product.offers : [];
    if (!offers.length) return '';

    return `
        <div class="store-history-list">
            ${[...offers].sort((a, b) => (a.price || 0) - (b.price || 0)).map(offer => {
                const points = getOfferHistoryPoints(offer);
                const first = points[0]?.price || offer.price || 0;
                const last = points[points.length - 1]?.price || offer.price || 0;
                const diff = last - first;
                const trendClass = diff < 0 ? 'down' : diff > 0 ? 'up' : 'flat';
                const trendLabel = diff < 0 ? `Bajo ${formatCLP(Math.abs(diff))}` : diff > 0 ? `Subio ${formatCLP(diff)}` : 'Sin cambios';
                const min = Math.min(...points.map(p => p.price), last);
                const max = Math.max(...points.map(p => p.price), last);
                const range = max - min || 1;
                const bars = points.map(point => {
                    const height = 26 + Math.round(((point.price - min) / range) * 34);
                    return `<span class="store-history-bar" style="height:${height}px" title="${formatCLP(point.price)} - ${formatHistoryDate(point.timestamp)}"></span>`;
                }).join('');

                return `
                    <div class="store-history-card">
                        <div class="store-history-head">
                            <span class="store-history-name">${getStoreDot(offer.storeKey)} ${escapeHtml(offer.store || 'Tienda')}</span>
                            <span class="store-history-price">${formatCLP(last)}</span>
                        </div>
                        <div class="store-history-bars">${bars}</div>
                        <div class="store-history-foot">
                            <span>${points.length} registro${points.length === 1 ? '' : 's'}</span>
                            <span class="store-history-trend ${trendClass}">${trendLabel}</span>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

copyProductLink = window.copyProductLink = async function(productId) {
    const product = findProductById(productId);
    if (!product) return;
    const url = getProductShareUrl(product);
    try {
        await navigator.clipboard.writeText(url);
        showToast('Enlace del producto copiado.');
    } catch (e) {
        window.prompt('Copia el enlace del producto:', url);
    }
};

openProductStore = window.openProductStore = function(productId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const product = findProductById(productId);
    const offer = getBestProductOffer(product);
    let url = getProductUrl(offer || {});
    if ((!url || url === '#') && product) {
        const q = encodeURIComponent(((product.brand || '') + ' ' + (product.model || '')).trim());
        url = isInternationalProduct(product) ? ('https://es.aliexpress.com/wholesale?SearchText=' + q) : getStoreSearchUrl(offer?.storeKey, product.brand, product.model, '#');
    }
    if (!url || url === '#') {
        showToast('No hay enlace disponible para este producto.');
        return;
    }

    window.open(url, '_blank', 'noopener,noreferrer');
};

openProductAction = window.openProductAction = function(productId, event) {
    const product = findProductById(productId);
    if (!product) return;

    if (isInternationalProduct(product)) {
        openProductStore(productId, event);
        return;
    }

    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    openProductDetail(productId);
};

function getProductSummary(product) {
    const raw = String(product?.specs || '').trim();
    if (raw && !raw.startsWith('{') && !raw.startsWith('[')) {
        return raw;
    }

    const parts = [];
    if (product?.type) parts.push(String(product.type).toUpperCase());
    if (product?.frameType) parts.push(product.frameType);
    if (product?.wheelSize) {
        const wheel = String(product.wheelSize);
        parts.push(wheel.toLowerCase().startsWith('aro') ? wheel : `Aro ${wheel}`);
    }

    return parts.join(' • ') || `${product?.brand || ''} ${product?.model || ''}`.trim();
}

function getProductSpecText(product) {
    const specs = product?.fullSpecs || {};
    return [
        product?.specs || '',
        ...Object.values(specs).map(value => String(value || ''))
    ].join(' ').toLowerCase();
}

openProductDetail = window.openProductDetail = function(productId) {
    const product = findProductById(productId);
    if (!product) return;

    const bestOffer = getBestProductOffer(product);
    updateProductSeo(product);
    const sharePath = getProductSharePath(product);
    if (window.location.search !== sharePath) {
        window.history.replaceState({ productId }, '', sharePath);
    }
    const discount = bestOffer.oldPrice ? Math.round((1 - bestOffer.price / bestOffer.oldPrice) * 100) : 0;

    const activeFav = state.favorites.find(f => f.id === productId);
    let alertHtml = '';
    if (activeFav) {
        const hasAlert = activeFav.alertPrice !== null && activeFav.alertPrice !== undefined;
        const currentAlertVal = hasAlert ? activeFav.alertPrice : bestOffer.price;
        alertHtml = `
            <div class="price-alert-panel">
                <div class="price-alert-header">
                    <i class="fa-solid fa-bell" style="color:var(--primary);"></i>
                    <span>Configurar Alerta de Correo para este Producto</span>
                </div>
                <p style="font-size:0.75rem; color:var(--text-dim); margin:0;">
                    Te enviaremos un correo electrónico inmediato en cuanto el precio de este artículo baje de tu objetivo.
                </p>
                <div class="price-alert-inputs">
                    <span style="font-size:0.8rem; color:var(--text-main); font-weight:600;">Avisarme si baja de:</span>
                    <input type="number" id="alert-price-input" value="${currentAlertVal}" step="1000" style="font-weight:700; text-align:center; width:130px; background:var(--bg-card); border:1px solid var(--border); border-radius:4px; color:var(--text-main); padding:0.38rem 0.5rem; outline:none;">
                    <button type="button" id="btn-alerta" class="btn-price-alert ${hasAlert ? 'active' : ''}" onclick="crearAlertaSupabase(${productId})">
                        ${hasAlert ? 'Desactivar Alerta' : 'Activar Alerta'}
                    </button>
                </div>
            </div>
        `;
    } else {
        alertHtml = `
            <div class="price-alert-panel" style="border: 1px solid var(--border); background: var(--bg-secondary); padding: 0.9rem 1rem; border-radius: 4px; margin-top: 0.75rem;">
                <div class="price-alert-header" style="color: var(--text-muted); font-size:0.8rem; gap:0.4rem; display:flex; align-items:center;">
                    <i class="fa-solid fa-heart" style="color:var(--text-dim);"></i>
                    <span>Añade este producto a tus favoritos para configurar alertas por correo</span>
                </div>
                <button type="button" class="btn-fav-detail" onclick="toggleFavoriteDetail(${productId})" style="background:var(--primary); color:#000; font-weight:800; border:none; padding:0.45rem 1rem; border-radius:6px; font-size:0.75rem; cursor:pointer; margin-top:0.35rem; display:inline-flex; align-items:center; gap:0.3rem;">
                    <i class="fa-solid fa-heart"></i> Añadir a Favoritos
                </button>
            </div>
        `;
    }

    const specsHtml = Object.entries(product.fullSpecs || {}).map(([key, val]) => `
        <div class="spec-item">
            <span class="spec-label">${key}</span>
            <span class="spec-value">${val}</span>
        </div>
    `).join('');

    const offersHtml = [...product.offers]
        .sort((a, b) => a.price - b.price)
        .map((offer, i) => {
            // Ir DIRECTAMENTE al producto en la tienda
            const storeUrl = getProductUrl(offer);
            return `
        <a href="${storeUrl}" target="_blank" rel="noopener" class="modal-offer-row ${i === 0 ? 'best' : ''}">
            ${i === 0 ? '<span class="best-badge">🏆 Mejor Precio</span>' : ''}
            <span class="modal-store-name" style="display: flex; align-items: center; flex-wrap: wrap;">
                ${getStoreDot(offer.storeKey)} ${offer.store}
                ${renderStoreRating(offer.storeKey)}
            </span>
            <div class="modal-price-col">
                <span class="modal-price-val">${formatCLP(offer.price)}</span>
                ${offer.oldPrice ? `<span class="modal-price-old">${formatCLP(offer.oldPrice)}</span>` : ''}
            </div>
            <span class="btn-goto">Ver en tienda <i class="fa-solid fa-arrow-up-right-from-square"></i></span>
        </a>`;
        }).join('');

    const storeHistoryHtml = renderStoreHistory(product);

    // Price history interactive chart markup
    const histMax = Math.max(...product.history);
    const histMin = Math.min(...product.history);
    const sparkHtml = `
        <div class="price-history-block">
            <span class="history-label">Historial de Precios (Interactivo)</span>
            <div class="chart-container">
                <svg viewBox="0 0 400 150" class="interactive-chart" id="history-chart">
                    <defs>
                        <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.25"/>
                            <stop offset="100%" stop-color="var(--primary)" stop-opacity="0.0"/>
                        </linearGradient>
                        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="var(--primary)" flood-opacity="0.4"/>
                        </filter>
                    </defs>
                    <!-- Grid Lines -->
                    <line x1="40" y1="25" x2="365" y2="25" class="chart-grid-line" />
                    <line x1="40" y1="65" x2="365" y2="65" class="chart-grid-line" />
                    <line x1="40" y1="105" x2="365" y2="105" class="chart-grid-line" />
                    <line x1="40" y1="120" x2="365" y2="120" class="chart-grid-line" style="stroke-width:1.5; stroke:rgba(255,255,255,0.1);" />

                    <!-- Axis Labels -->
                    <text x="35" y="28" text-anchor="end" class="chart-axis-text">${formatCLP(histMax)}</text>
                    <text x="35" y="70" text-anchor="end" class="chart-axis-text">${formatCLP(Math.round((histMax + histMin) / 2))}</text>
                    <text x="35" y="108" text-anchor="end" class="chart-axis-text">${formatCLP(histMin)}</text>

                    <!-- Bottom date labels -->
                    <text x="40" y="140" text-anchor="middle" class="chart-axis-text">Hace 5s</text>
                    <text x="105" y="140" text-anchor="middle" class="chart-axis-text">Hace 4s</text>
                    <text x="170" y="140" text-anchor="middle" class="chart-axis-text">Hace 3s</text>
                    <text x="235" y="140" text-anchor="middle" class="chart-axis-text">Hace 2s</text>
                    <text x="300" y="140" text-anchor="middle" class="chart-axis-text">Hace 1s</text>
                    <text x="365" y="140" text-anchor="middle" class="chart-axis-text">Hoy</text>

                    <!-- Tracker vertical line -->
                    <line id="tracker-line" x1="0" y1="20" x2="0" y2="120" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="3 3" style="opacity: 0; pointer-events: none;" />

                    <!-- Dynamic chart area and line -->
                    <path id="chart-area-path" class="chart-area" d="" />
                    <path id="chart-line-path" class="chart-line" d="" />

                    <!-- Floating tracker dot -->
                    <circle id="tracker-dot" r="6" fill="var(--primary)" stroke="#fff" stroke-width="2.5" style="opacity: 0; pointer-events: none; filter: drop-shadow(0px 0px 4px var(--primary));" />
                </svg>
                <div id="chart-tooltip" class="chart-tooltip"></div>
            </div>
        </div>
    `;


    // Imagen: priorizar local descargada, fallback a URL original de tienda, luego genérico
    const imgSrc = getProductImage(product);
    const fallbackImg = getProductFallbackImage(product);

    const valScore = calculateValueScore(product);
    const modalValueScoreHtml = valScore ? `
        <div class="modal-value-score-block" style="margin-top: 0.75rem; background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.25); padding: 0.75rem 1.25rem; border-radius: 12px; display: flex; align-items: center; gap: 1rem; width: 100%;">
            <div style="text-align: left; flex-grow: 1;">
                <span style="font-size: 0.68rem; font-weight: 800; color: var(--primary); letter-spacing: 1px; text-transform: uppercase; display: block;">Ratio Calidad-Precio (Compra Inteligente)</span>
                <span style="font-size: 0.82rem; color: var(--text-muted);">Este modelo destaca por sus excelentes especificaciones frente a su costo de mercado.</span>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-card); padding: 0.5rem 0.75rem; border-radius: 4px; border: 1px solid var(--border); min-width: 80px;">
                <span style="font-family: var(--font-heading); font-weight: 800; font-size: 1.45rem; color: var(--text-main); line-height: 1.1;">${valScore}</span>
                <span style="font-size: 0.6rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">de 100</span>
            </div>
        </div>
    ` : '';

    const modal = document.getElementById('modal-overlay');
    document.getElementById('modal-content').innerHTML = `
        <button class="modal-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-layout">
            <div class="modal-img-side">
                <div class="modal-img-wrapper">
                    <img src="${imgSrc}" alt="${product.model}"
                         data-fallbacks="${getImageFallbacks(product).join('|')}"
                         onerror="handleProductImageError(this, '${fallbackImg}')">
                </div>
                ${discount > 0 ? `<div class="modal-discount-badge">-${discount}% OFF</div>` : ''}
            </div>
            <div class="modal-info-side">
                <div class="modal-header">
                    <span class="modal-brand-badge">${product.brand}</span>
                    <h2 class="modal-title">${product.model}</h2>
                    <p class="modal-specs-summary">${getProductSummary(product)}</p>
                    <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.85rem;">
                        <button type="button" class="modal-share-link" style="margin-bottom:0;" onclick="copyProductLink(${product.id})">
                            <i class="fa-solid fa-link"></i> Copiar enlace
                        </button>
                        <button type="button" class="modal-share-link" style="margin-bottom:0; ${state.compare.includes(product.id) ? 'border-color:var(--primary); color:var(--primary); font-weight:600;' : ''}" onclick="toggleCompare(${product.id}, event); openProductDetail(${product.id});">
                            <i class="fa-solid ${state.compare.includes(product.id) ? 'fa-check' : 'fa-scale-balanced'}"></i> ${state.compare.includes(product.id) ? 'En el comparador' : 'Comparar con otro modelo'}
                        </button>
                    </div>
                    <div class="modal-best-price-hero">
                        <span class="label">Desde</span>
                        <span class="amount">${formatCLP(bestOffer.price)}</span>
                        <span class="stores-count">en ${product.offers.length} tienda${product.offers.length > 1 ? 's' : ''}</span>
                    </div>
                    ${renderHistoricalPriceBanner(product)}
                    ${modalValueScoreHtml}
                    ${(function() {
                        let headerSpecsHtml = '';
                        if (product.fullSpecs && Object.keys(product.fullSpecs).length > 0) {
                            const keySpecs = ['Cuadro', 'Frenos', 'Transmisión', 'Material', 'Capacidad', 'Medida', 'Uso', 'Tipo', 'Peso Aproximado'];
                            const foundSpecs = [];
                            for (const key of keySpecs) {
                                const actualKey = Object.keys(product.fullSpecs).find(k => k.toLowerCase() === key.toLowerCase());
                                if (actualKey && product.fullSpecs[actualKey]) {
                                    let val = product.fullSpecs[actualKey];
                                    if (val.length > 40) val = val.substring(0, 37) + '...';
                                    foundSpecs.push(`
                                        <div style="background: var(--bg-secondary); border: 1px solid var(--border); padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.75rem; min-width: 100px; flex: 1; text-align: left;">
                                            <span style="display: block; font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">${key}</span>
                                            <span style="font-weight: 600; color: var(--text-main); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; display: block;">${val}</span>
                                        </div>
                                    `);
                                }
                                if (foundSpecs.length >= 3) break;
                            }
                            if (foundSpecs.length > 0) {
                                headerSpecsHtml = `
                                    <div class="modal-header-specs" style="display: flex; gap: 0.5rem; width: 100%; margin-top: 0.75rem; flex-wrap: wrap;">
                                        ${foundSpecs.join('')}
                                    </div>
                                `;
                            }
                        }
                        return headerSpecsHtml;
                    })()}
                </div>

                <div class="modal-tabs">
                    <button class="tab-btn active" onclick="switchTab(this, 'tab-precios')">💰 Precios</button>
                    <button class="tab-btn" onclick="switchTab(this, 'tab-specs')">⚙️ Especificaciones</button>
                    <button class="tab-btn" onclick="switchTab(this, 'tab-history')">📈 Historial</button>
                </div>

                <div id="tab-precios" class="tab-panel active">
                    <div class="modal-offers-list">${offersHtml}</div>
                    ${alertHtml}
                </div>
                <div id="tab-specs" class="tab-panel">
                    <div class="specs-grid">${specsHtml}</div>
                </div>
                <div id="tab-history" class="tab-panel">
                    ${sparkHtml}
                    ${storeHistoryHtml}
                </div>
            </div>
        </div>
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    initInteractiveChart(product);
};

closeModal = window.closeModal = function() {
    document.getElementById('modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
    if (new URLSearchParams(window.location.search).has('producto')) {
        window.history.replaceState({}, '', window.location.pathname);
        resetDefaultSeo();
    }
};

switchTab = window.switchTab = function(btn, tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(tabId).classList.add('active');
};

// =============================================
// TOAST NOTIFICATION
// =============================================
function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// =============================================
// NAVBAR BUTTONS INTERACTIVE LOGIC
// =============================================
activateExplorar = window.activateExplorar = function(event) {
    if (event) event.preventDefault();
    isCyberMode = false;
    state.isInternationalMode = false;
    document.body?.classList.remove('cyber-theme');
    clearFilters();
    state.sortBy = 'relevant';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'relevant';
    
    // Update active link in navbar
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navExplorar = document.getElementById('nav-catalogo');
    if (navExplorar) navExplorar.classList.add('active');
    
    window.scrollTo({
        top: document.getElementById('catalog').offsetTop - 80,
        behavior: 'smooth'
    });
    render();
    showToast('Explorando el catálogo completo.');
};

activateDeals = window.activateDeals = function(event) {
    if (event) event.preventDefault();
    isCyberMode = false;
    state.isInternationalMode = false;
    document.body?.classList.remove('cyber-theme');
    
    // Reset filters and apply 5% discount filter for regular Deals
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: 5 };
    state.currentPage = 1;
    
    // Reset UI filter elements
    document.getElementById('main-search').value = '';
    document.getElementById('price-min').value = '';
    document.getElementById('price-max').value = '';
    document.querySelectorAll('.checkbox-list input, .brand-check, .dyn-type-check').forEach(i => i.checked = false);
    document.querySelectorAll('.wheel-pill, .budget-pill').forEach(p => p.classList.remove('active'));
    
    // Set default sorting to relevant so standard deals display popular products on sale
    state.sortBy = 'relevant';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'relevant';
    
    // Update active link in navbar
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navDeals = document.getElementById('nav-ofertas');
    if (navDeals) navDeals.classList.add('active');
    
    window.scrollTo({
        top: document.getElementById('catalog').offsetTop - 80,
        behavior: 'smooth'
    });
    render();
    showToast('Mostrando las ofertas más populares del catálogo (con descuento).');
};

activateCyberMode = window.activateCyberMode = function(event) {
    if (event) event.preventDefault();
    if (!isCyberActive()) {
        showToast("El Cyber 2026 ha finalizado. ¡Nos vemos en el próximo evento!");
        checkCyberStatus();
        return;
    }
    
    // Reset filters and apply 20% discount filter for Cyber Days
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: 20 };
    state.currentPage = 1;
    state.isInternationalMode = false;
    
    // Reset UI filter elements
    document.getElementById('main-search').value = '';
    document.getElementById('price-min').value = '';
    document.getElementById('price-max').value = '';
    document.querySelectorAll('.checkbox-list input, .brand-check, .dyn-type-check').forEach(i => i.checked = false);
    document.querySelectorAll('.wheel-pill, .budget-pill').forEach(p => p.classList.remove('active'));
    
    isCyberMode = true;
    // Set sorting to discount descending so it highlights the absolute highest deals first
    state.sortBy = 'discount';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'discount';
    
    // Update active link in navbar
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navCyber = document.getElementById('nav-cyber');
    if (navCyber) navCyber.classList.add('active');
    
    // Apply Cyber Theme styling to body
    document.body?.classList.add('cyber-theme');
    
    window.scrollTo({
        top: document.getElementById('catalog').offsetTop - 80,
        behavior: 'smooth'
    });
    render();
    
    showToast('⚡ ¡Modo CYBER DAYS activado! Mostrando mega ofertas con descuentos de 20% o más.');
};

activateInternationalMode = window.activateInternationalMode = function(event) {
    if (event) event.preventDefault();
    isCyberMode = false;
    document.body?.classList.remove('cyber-theme');
    
    // Activate international mode
    state.isInternationalMode = true;
    
    // AliExpress has accessories and parts. If current category is bicycles, switch to accesorios
    if (state.category === 'bicicletas') {
        state.category = 'accesorios';
    }
    
    // Reset filters
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: null, aliexpressQuickFilter: 'all', spec: null }; document.querySelectorAll('.component-tier-pill').forEach(p => p.classList.remove('active'));
    state.currentPage = 1;
    
    // Reset quick pills active state in UI
    document.querySelectorAll('.quick-pill').forEach(p => {
        if (p.dataset.filter === 'all') p.classList.add('active');
        else p.classList.remove('active');
    });
    
    // Reset UI filter elements
    document.getElementById('main-search').value = '';
    document.getElementById('price-min').value = '';
    document.getElementById('price-max').value = '';
    document.querySelectorAll('.checkbox-list input, .brand-check, .dyn-type-check').forEach(i => i.checked = false);
    document.querySelectorAll('.wheel-pill, .budget-pill').forEach(p => p.classList.remove('active'));
    
    // Update category tabs active state
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    const catPill = document.querySelector(`.pill[onclick="setCategory('${state.category}')"]`);
    if (catPill) catPill.classList.add('active');
    
    // Update title
    document.getElementById('section-title').innerText = 'AliExpress Ciclismo Internacional';
    
    // Hide bike-only filters since we are in accessories/parts
    document.querySelectorAll('.bike-only-filter').forEach(el => el.style.display = 'none');
    
    // Update active link in navbar
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navInt = document.getElementById('nav-internacional');
    if (navInt) navInt.classList.add('active');
    
    // Set default sorting
    state.sortBy = 'relevant';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'relevant';
    syncCatalogUiState();
    
    window.scrollTo({
        top: document.getElementById('catalog').offsetTop - 80,
        behavior: 'smooth'
    });
    
    render();
    showToast('✈️ Catálogo Internacional Activado. Mostrando productos importados de AliExpress.');
};

openNovedadesModal = window.openNovedadesModal = async function(event) {
    if (event) event.preventDefault();
    
    // Update active link
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navNov = document.getElementById('nav-novedades');
    if (navNov) navNov.classList.add('active');
    
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;
    
    const defaultArticlesHtml = `
        <article class="news-minimal-card">
            <span class="news-minimal-badge">Tendencias</span>
            <h4 class="news-minimal-card-title">Gravel en Chile: La aventura todo terreno</h4>
            <p class="news-minimal-card-desc">
                El gravel sigue creciendo en Chile. Conoce las mejores bicicletas de aventura y cómo equipar tu transmisión para terrenos mixtos y ripio.
            </p>
        </article>
        
        <article class="news-minimal-card">
            <span class="news-minimal-badge">Consejos</span>
            <h4 class="news-minimal-card-title">Mantenimiento de transmisión y cadena</h4>
            <p class="news-minimal-card-desc">
                La humedad y el polvo desgastan los eslabones rápidamente. Aprende cómo limpiar, secar y lubricar tu transmisión para máxima eficiencia.
            </p>
        </article>
        
        <article class="news-minimal-card">
            <span class="news-minimal-badge">Rutas</span>
            <h4 class="news-minimal-card-title">Ascenso a Farellones: Preparación segura</h4>
            <p class="news-minimal-card-desc">
                Subir a la cordillera es un clásico del ciclismo chileno. Revisa el estado de tus frenos, hidratación, luces traseras y vestimenta térmica.
            </p>
        </article>
    `;

    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-minimal-shell">
            <div class="modal-minimal-header">
                <span class="modal-minimal-eyebrow">Comunidad & Actualidad</span>
                <h2 class="modal-minimal-title">Novedades del Pedal</h2>
                <p class="modal-minimal-subtitle">
                    Mantente al día con las últimas noticias del ciclismo en Chile, consejos de mantenimiento y novedades del catálogo.
                </p>
            </div>
            
            <div class="newsletter-minimal-box">
                <div class="newsletter-minimal-copy">
                    <span class="newsletter-minimal-kicker">Boletín BiciTodo</span>
                    <p class="newsletter-minimal-text">Recibe consejos mecánicos, rutas recomendadas y alertas de bajas de precio.</p>
                </div>
                <form id="newsletter-form" class="newsletter-minimal-form" onsubmit="submitNewsletter(event)">
                    <input type="email" id="newsletter-email" class="newsletter-minimal-input" placeholder="tu-correo@ciclismo.cl" required>
                    <button type="submit" class="btn-minimal-primary">
                        Suscribirse <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </form>
            </div>
            
            <div class="news-minimal-section">
                <div class="news-minimal-section-head">
                    <h3 class="news-minimal-section-title">Artículos y Noticias Recientes</h3>
                </div>
                
                <div id="news-container" class="news-minimal-grid">
                    <div class="news-minimal-loading">
                        <i class="fa-solid fa-circle-notch fa-spin"></i>
                        <p>Cargando artículos recientes...</p>
                    </div>
                </div>
            </div>
            
            <div class="modal-minimal-footer">
                <button type="button" class="btn-minimal-secondary" onclick="closeModal()">
                    Cerrar
                </button>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    const newsContainer = document.getElementById('news-container');
    if (!newsContainer) return;

    try {
        const resp = await fetch(`${API_BASE_URL}/api/novedades`, { cache: 'no-store' });
        if (!resp.ok) throw new Error("HTTP error " + resp.status);
        const articles = await resp.json();
        
        if (articles && articles.length > 0) {
            const categoryIcons = {
                'MTB': 'fa-mountain-sun',
                'Ruta': 'fa-road',
                'Entrevistas': 'fa-microphone',
                'Artículos': 'fa-newspaper',
                'Consejos': 'fa-screwdriver-wrench',
                'Noticias': 'fa-circle-info'
            };

            newsContainer.innerHTML = articles.map(article => {
                const cat = article.category || 'Noticias';
                const icon = categoryIcons[cat] || 'fa-newspaper';

                return `
                    <article class="news-minimal-card is-clickable"
                         onclick="window.open('${article.url}', '_blank', 'noopener,noreferrer')">
                        <span class="news-minimal-badge">
                            <i class="fa-solid ${icon}"></i> ${escapeHtml(cat)}
                        </span>
                        <h4 class="news-minimal-card-title">${escapeHtml(article.title)}</h4>
                        <p class="news-minimal-card-desc">
                            ${escapeHtml(article.summary)}
                        </p>
                        <span class="news-minimal-link">
                            Leer artículo <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </span>
                    </article>
                `;
            }).join('');
        } else {
            newsContainer.innerHTML = defaultArticlesHtml;
        }
    } catch (e) {
        console.warn("Failed to fetch news from API, falling back to static news:", e);
        newsContainer.innerHTML = defaultArticlesHtml;
    }
};

window.submitNewsletter = function(event) {
    if (event) event.preventDefault();
    const emailInput = document.getElementById('newsletter-email');
    if (!emailInput || !emailInput.value) return;
    
    const form = document.getElementById('newsletter-form');
    if (form && form.parentElement) {
        form.parentElement.innerHTML = `
            <div class="newsletter-minimal-success">
                <i class="fa-solid fa-circle-check"></i>
                <div>
                    <strong>Suscripción confirmada</strong>
                    <p>Recibirás nuestras próximas novedades y alertas de ofertas directamente en tu correo.</p>
                </div>
            </div>
        `;
    }
    showToast('Te has suscrito con éxito al boletín de BiciTodo.');
};

openProfileModal = window.openProfileModal = function(event) {
    if (event) event.preventDefault();
    
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navC = document.getElementById('nav-cuenta');
    if (navC) navC.classList.add('active');
    
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;
    
    const allProducts = [...state.data.bicicletas, ...state.data.accesorios, ...state.data.repuestos];
    const userFavs = state.favorites.map(f => {
        const p = allProducts.find(item => item.id === f.id) || (state.data.cache && state.data.cache[f.id]);
        if (p) {
            return { ...p, alertPrice: f.alertPrice };
        }
        return null;
    }).filter(Boolean);
    
    const favsHtml = userFavs.length > 0 ? userFavs.map(p => {
        const alertText = p.alertPrice
            ? `<span class="profile-fav-alert active"><i class="fa-solid fa-bell"></i> Alerta: ${formatCLP(p.alertPrice)}</span>`
            : `<span class="profile-fav-alert"><i class="fa-solid fa-bell-slash"></i> Sin alerta activa</span>`;
        
        return `
        <div class="profile-fav-item">
            <div class="profile-fav-info">
                <div class="profile-fav-thumb">
                    <img src="${getProductImage(p)}" alt="${escapeHtml(p.model)}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)">
                </div>
                <div class="profile-fav-meta">
                    <span class="profile-fav-brand">${escapeHtml(p.brand)}</span>
                    <span class="profile-fav-model">${escapeHtml(p.model)}</span>
                    ${alertText}
                </div>
            </div>
            <div class="profile-fav-actions">
                <button type="button" class="btn-minimal-outline-sm" onclick="closeModal(); openProductDetail(${p.id});">
                    Configurar alerta
                </button>
                <button type="button" class="btn-minimal-danger-sm" onclick="toggleFavorite(${p.id}); openProfileModal(event);" title="Eliminar de favoritos">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        </div>
        `;
    }).join('') : '<p class="profile-fav-empty">Aún no tienes productos guardados en favoritos.</p>';
    
    const displayName = state.user ? state.user.displayName : 'Invitado';
    const email = state.user ? state.user.email : 'Sesión local';
    const avatar = state.user ? state.user.avatar : 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y';
    
    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-minimal-shell modal-minimal-narrow">
            <div class="modal-minimal-header">
                ${renderAvatarHTML(avatar, '68px', '2px')}
                <h2 class="modal-minimal-title" style="margin-top:0.5rem;">${escapeHtml(displayName)}</h2>
                <span class="modal-minimal-eyebrow">${escapeHtml(email)}</span>
            </div>
            
            <div class="profile-minimal-card">
                <h4 class="profile-minimal-card-title"><i class="fa-solid fa-user-astronaut"></i> Avatar de perfil</h4>
                <div class="profile-avatar-grid">
                    ${Object.keys(EMOJI_GRADIENTS).map(emoji => {
                        const isActive = avatar === emoji;
                        return `
                            <button type="button" onclick="changeAvatar('${emoji}')" class="avatar-select-pill ${isActive ? 'active-avatar' : ''}" style="background: ${EMOJI_GRADIENTS[emoji]};" title="Elegir ${emoji}">
                                ${emoji}
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>
            
            <div class="profile-minimal-card">
                <h4 class="profile-minimal-card-title"><i class="fa-regular fa-heart"></i> Tus Favoritos y Alertas (${userFavs.length})</h4>
                <div class="profile-fav-list">
                    ${favsHtml}
                </div>
            </div>
            
            <div class="profile-minimal-card profile-minimal-note">
                <i class="fa-solid fa-bell"></i>
                <p>Recibirás una notificación por correo electrónico cuando cualquiera de tus bicicletas o componentes favoritos baje de tu precio objetivo.</p>
            </div>
            
            <div class="modal-minimal-footer">
                <button type="button" class="btn-minimal-primary" onclick="closeModal()">
                    Listo
                </button>
            </div>
        </div>
    `;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

openCountryModal = window.openCountryModal = function() {
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;

    const integratedStores = [
        { key: 'oxford', name: 'Oxford Store', type: 'Especialista' },
        { key: 'specialized', name: 'Specialized Chile', type: 'Marca Oficial' },
        { key: 'trek', name: 'Trek Chile', type: 'Marca Oficial' },
        { key: 'decathlon', name: 'Decathlon', type: 'Deportes' },
        { key: 'totem', name: 'Totem Chile', type: 'Especialista' },
        { key: 'ibikes', name: 'iBikes', type: 'Especialista' },
        { key: 'vidaurre', name: 'Vidaurre Bikes', type: 'Especialista' },
        { key: 'faucon', name: 'Faucon Bikes', type: 'Especialista' },
        { key: 'satiro', name: 'Sátiro Bikes', type: 'Especialista' },
        { key: 'copenhague', name: 'Copenhague', type: 'Especialista' },
        { key: 'crossmountain', name: 'CrossMountain', type: 'Especialista' },
        { key: 'dsbikes', name: 'DS Bikes', type: 'Especialista' },
        { key: 'fullbike', name: 'Full Bike', type: 'Especialista' },
        { key: 'sparta', name: 'Sparta', type: 'Deportes' },
        { key: 'falabella', name: 'Falabella', type: 'Multitienda' },
        { key: 'ripley', name: 'Ripley', type: 'Multitienda' },
        { key: 'paris', name: 'Paris', type: 'Multitienda' },
        { key: 'aliexpress', name: 'AliExpress', type: 'Internacional', isIntl: true }
    ];

    const storesGridHtml = integratedStores.map(store => {
        const isSelected = state.filters.stores && state.filters.stores.includes(store.key);
        const clickHandler = store.isIntl
            ? `closeModal(); activateInternationalMode(event);`
            : `closeModal(); filterByStoreChip('${store.key}');`;
        return `
            <button type="button" class="store-modal-card ${isSelected ? 'active' : ''}" onclick="${clickHandler}">
                <div class="store-modal-card-top">
                    ${getStoreDot(store.key)}
                    <span class="store-modal-name">${escapeHtml(store.name)}</span>
                </div>
                <span class="store-modal-type">${escapeHtml(store.type)}</span>
            </button>
        `;
    }).join('');
    
    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-minimal-shell">
            <div class="modal-minimal-header">
                <span class="modal-minimal-eyebrow">Mercado Activo Completo · CLP ($)</span>
                <h2 class="modal-minimal-title">Región: Chile</h2>
                <p class="modal-minimal-subtitle">
                    Comparamos en tiempo real el catálogo de ${integratedStores.length} tiendas oficiales y distribuidores autorizados en todo Chile. Selecciona cualquier tienda para filtrar sus productos directamente.
                </p>
            </div>
            
            <div class="stores-modal-section">
                <div class="stores-modal-header">
                    <span class="stores-modal-label">Tiendas integradas (${integratedStores.length})</span>
                    ${(state.filters.stores && state.filters.stores.length > 0) ? `<button type="button" class="stores-modal-clear" onclick="closeModal(); clearFilters();">Ver todas las tiendas</button>` : ''}
                </div>
                <div class="stores-modal-grid">
                    ${storesGridHtml}
                </div>
            </div>
            
            <div class="modal-minimal-footer">
                <button type="button" class="btn-minimal-primary" onclick="closeModal()">
                    Aceptar
                </button>
            </div>
        </div>
    `;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

// =============================================
// RENDERING
// =============================================
// Global cache for all fetched products to support detailed modal & comparison anywhere
if (!state.data.cache) state.data.cache = {};

async function openPendingProductFromUrl() {
    if (!state.pendingProductId || state.pendingProductOpened) return;

    let product = findProductById(state.pendingProductId) || state.data.cache[state.pendingProductId];
    if (!product) {
        try {
            const params = new URLSearchParams({
                producto_id: String(state.pendingProductId),
                page: '1',
                limit: '1'
            });
            const response = await fetch(`${API_BASE_URL}/api/productos?${params.toString()}`, { cache: 'no-store' });
            if (response.ok) {
                const data = await response.json();
                product = data.productos?.[0];
                if (product) {
                    state.data.cache[product.id] = product;
                    if (!state.data[product.category]) state.data[product.category] = [];
                    if (!state.data[product.category].some(item => item.id === product.id)) {
                        state.data[product.category].push(product);
                    }
                }
            }
        } catch (error) {
            console.warn('No se pudo cargar el producto compartido:', error);
        }
    }

    if (product) {
        state.pendingProductOpened = true;
        setTimeout(() => openProductDetail(product.id), 50);
    }
}

async function render(forceFetch = true) {
    const grid = document.getElementById('catalog-grid');
    if (!grid) return;
    syncCatalogUiState();
    
    try {
        let pageItems = state.data[state.category] || [];
        let totalPages = state.totalPages || 1;
        let totalCount = state.totalCount || pageItems.length;
    
    if (forceFetch || pageItems.length === 0) {
        // 1. Build Query Parameters from state
        const params = new URLSearchParams();
        params.append('page', state.currentPage);
        params.append('limit', state.itemsPerPage);
        params.append('categoria', state.category);
        
        if (state.filters.search) {
            params.append('search', state.filters.search);
        }
        
        if (state.filters.priceMin !== null && state.filters.priceMin !== undefined) {
            params.append('price_min', state.filters.priceMin);
        }
        if (state.filters.priceMax !== null && state.filters.priceMax !== undefined) {
            params.append('price_max', state.filters.priceMax);
        }
        
        // Budget Pill ranges override manual inputs if set
        if (state.filters.budgetRange) {
            const ranges = {
                'sub100': [0, 99990],
                '100-200': [100000, 199990],
                '200-400': [200000, 399990],
                '400-800': [400000, 799990],
                '800plus': [800000, Infinity]
            };
            const [min, max] = ranges[state.filters.budgetRange] || [0, Infinity];
            params.set('price_min', min);
            if (max !== Infinity) params.set('price_max', max);
        }
        
        if (state.filters.stores.length > 0) {
            params.append('tienda', state.filters.stores.join(','));
        }
        
        if (state.filters.brands.length > 0) {
            params.append('brand', state.filters.brands.join(','));
        }

        if (state.category === 'bicicletas' && state.filters.types.length > 0) {
            params.append('tipo', state.filters.types.join(','));
        }

        if (state.category === 'bicicletas' && state.filters.wheelSizes.length > 0) {
            params.append('aro', state.filters.wheelSizes.join(','));
        }

        if (state.category !== 'bicicletas' && state.filters.dynTypes.length > 0) {
            params.append('tipo', state.filters.dynTypes.join(','));
        }
        
        if (state.sortBy) {
            params.append('sort_by', state.sortBy);
        }
        
        if (state.filters.discountMin !== null && state.filters.discountMin !== undefined) {
            params.append('discount_min', state.filters.discountMin);
        }
        
        if (state.isInternationalMode) {
            params.append('internacional', 'true');
            if (state.filters.aliexpressQuickFilter && state.filters.aliexpressQuickFilter !== 'all') {
                params.append('quick_filter', state.filters.aliexpressQuickFilter);
            }
        }
        
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem;">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 3rem; color: var(--primary); margin-bottom: 1rem; display: block;"></i>
                <h3>Cargando productos...</h3>
            </div>
        `;

        try {
            const response = await fetch(`${API_BASE_URL}/api/productos?${params.toString()}`, { cache: 'no-store' });
            if (!response.ok) throw new Error("API error");
            const resData = await response.json();
            
            let rawPageItems = resData.productos || [];
            
            // If in Cyber Mode, only show items with significant discounts (>= 20%)
            if (isCyberMode) {
                rawPageItems = rawPageItems.filter(product => {
                    const best = [...product.offers].sort((o1, o2) => o1.price - o2.price)[0];
                    const disc = best.oldPrice ? Math.round((1 - best.price / best.oldPrice) * 100) : 0;
                    return disc >= 20;
                });
            }
            
            pageItems = rawPageItems.filter(product => !isBlockedSyntheticProduct(product));
            const blockedOnPage = rawPageItems.length - pageItems.length;
            totalPages = isCyberMode ? 1 : (resData.total_pages || 1);
            totalCount = isCyberMode ? pageItems.length : Math.max(0, (resData.total_count || 0) - blockedOnPage);
            state.totalPages = totalPages;
            state.totalCount = totalCount;
            
            // Update local state categories + cache
            state.data[state.category] = pageItems;
            pageItems.forEach(p => {
                state.data.cache[p.id] = p;
            });
            
            // Set metadata on state for dynamic filter lists
            state.brandsMetadata = resData.brands || {};
            state.typesMetadata = resData.types || {};
            
            // Render filter options dynamically based on retrieved data!
            renderBrandFilter();
            renderTypeFilter();
        } catch (error) {
            console.warn("API offline or error, falling back to local data.json:", error);
            if (!state.fallbackData) {
                try {
                    const fallbackResp = await fetch('./data.json');
                    if (fallbackResp.ok) {
                        state.fallbackData = await fallbackResp.json();
                    }
                } catch (e) {
                    console.error("Could not load data.json fallback:", e);
                }
            }
            if (state.fallbackData) {
                const catItems = state.fallbackData[state.category] || [];
                let filtered = catItems.filter(p => !isBlockedSyntheticProduct(p));

                if (state.filters.search) {
                    const q = state.filters.search.toLowerCase();
                    filtered = filtered.filter(p => 
                        (p.brand && p.brand.toLowerCase().includes(q)) || 
                        (p.model && p.model.toLowerCase().includes(q)) ||
                        (p.specs && p.specs.toLowerCase().includes(q))
                    );
                }
                if (state.filters.brands && state.filters.brands.length > 0) {
                    filtered = filtered.filter(p => state.filters.brands.includes(p.brand.toLowerCase()));
                }
                if (state.filters.types && state.filters.types.length > 0) {
                    filtered = filtered.filter(p => state.filters.types.includes((p.type || '').toLowerCase()));
                }
                if (state.filters.wheelSizes && state.filters.wheelSizes.length > 0) {
                    filtered = filtered.filter(p => state.filters.wheelSizes.includes((p.wheelSize || '').toLowerCase()));
                }
                if (state.filters.priceMin !== null && state.filters.priceMin !== undefined) {
                    filtered = filtered.filter(p => {
                        const minPrice = Math.min(...(p.offers || []).map(o => o.price));
                        return minPrice >= state.filters.priceMin;
                    });
                }
                if (state.filters.priceMax !== null && state.filters.priceMax !== undefined) {
                    filtered = filtered.filter(p => {
                        const minPrice = Math.min(...(p.offers || []).map(o => o.price));
                        return minPrice <= state.filters.priceMax;
                    });
                }

                if (state.sortBy === 'price-asc') {
                    filtered.sort((a, b) => Math.min(...a.offers.map(o => o.price)) - Math.min(...b.offers.map(o => o.price)));
                } else if (state.sortBy === 'price-desc') {
                    filtered.sort((a, b) => Math.min(...b.offers.map(o => o.price)) - Math.min(...a.offers.map(o => o.price)));
                } else if (state.sortBy === 'stores') {
                    filtered.sort((a, b) => (b.offers || []).length - (a.offers || []).length);
                }

                totalCount = filtered.length;
                totalPages = Math.max(1, Math.ceil(totalCount / state.itemsPerPage));
                state.totalCount = totalCount;
                state.totalPages = totalPages;

                const startIdx = (state.currentPage - 1) * state.itemsPerPage;
                pageItems = filtered.slice(startIdx, startIdx + state.itemsPerPage);

                pageItems.forEach(p => {
                    state.data.cache[p.id] = p;
                });

                const brandCounts = {};
                catItems.forEach(p => {
                    brandCounts[p.brand] = (brandCounts[p.brand] || 0) + 1;
                });
                state.brandsMetadata = brandCounts;
                renderBrandFilter();
                renderTypeFilter();
            }
        }
    }
    
    grid.innerHTML = '';
    document.getElementById('results-count').innerText = `Mostrando ${totalCount} modelos`;
    
    // Pagination controls
    document.querySelector('.page-info').textContent = `Página ${state.currentPage} de ${totalPages}`;
    document.querySelector('.btn-page.prev').disabled = state.currentPage <= 1;
        document.querySelector('.btn-page.next').disabled = state.currentPage >= totalPages;
        
        if (pageItems.length === 0) {
            let suggestions = [];
            const query = state.filters.search ? state.filters.search.toLowerCase() : '';
            if (query) {
                const categories = {
                    'bicicletas': 'Bicicletas',
                    'accesorios': 'Accesorios',
                    'repuestos': 'Repuestos'
                };
                for (const catKey in categories) {
                    if (catKey !== state.category) {
                        const checkParams = new URLSearchParams();
                        if (state.filters.search) {
                            checkParams.set('search', state.filters.search);
                        }
                        checkParams.set('categoria', catKey);
                        checkParams.set('page', '1');
                        checkParams.set('limit', '1');
                        try {
                            const checkResp = await fetch(`${API_BASE_URL}/api/productos?${checkParams.toString()}`, { cache: 'no-store' });
                            if (checkResp.ok) {
                                const checkData = await checkResp.json();
                                if (checkData.total_count > 0) {
                                    suggestions.push({ cat: catKey, catName: categories[catKey], count: checkData.total_count });
                                }
                            }
                        } catch (e) {}
                    }
                }
            }

            let suggestionHtml = '';
            if (suggestions.length > 0) {
                suggestionHtml = `
                    <div class="empty-suggestions-box">
                        <p>Encontramos resultados en otras secciones:</p>
                        <div class="empty-suggestions-actions">
                            ${suggestions.map(s => `
                                <button onclick="setCategory('${s.cat}'); document.getElementById('main-search').value='${state.filters.search}'; state.filters.search='${state.filters.search}'; render();" 
                                        class="btn-empty-suggestion">
                                    Ver ${s.count} en ${s.catName}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            grid.innerHTML = `
                <div class="empty-results-state">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <h3>Sin resultados para los filtros seleccionados</h3>
                    <p>Intenta ajustar el rango de precio, cambiar de categoría o limpiar los filtros.</p>
                    <button onclick="clearFilters()" class="btn-clear-empty">Limpiar filtros</button>
                    ${suggestionHtml}
                </div>
            `;
            return;
        }

        const fragment = document.createDocumentFragment();

        pageItems.forEach((product, index) => {
            const sortedOffers = [...(product.offers || [])].sort((a, b) => a.price - b.price);
            const bestOffer = sortedOffers[0] || { price: 0, store: 'Tienda', storeKey: 'oxford' };
            const maxOffer = sortedOffers[sortedOffers.length - 1] || bestOffer;
            const minPrice = bestOffer.price || 0;
            const maxPrice = maxOffer.price || minPrice;
            const hasPriceRange = sortedOffers.length > 1 && maxPrice > minPrice;
            const discount = bestOffer.oldPrice && bestOffer.oldPrice > bestOffer.price
                ? Math.round((1 - bestOffer.price / bestOffer.oldPrice) * 100)
                : 0;
            const isComparing = state.compare.includes(product.id);
            const isIntlProduct = isInternationalProduct(product);

            const card = document.createElement('article');
            card.className = `product-card elite${isComparing ? ' comparing' : ''}${isIntlProduct ? ' international' : ''}`;
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            card.setAttribute('aria-label', `Ver detalles de ${product.brand} ${product.model}`);
            const cardFallback = getProductFallbackImage(product);
            const isFavorite = state.favorites.some(f => f.id === product.id);
            const favIcon = isFavorite ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
            const productSharePath = getProductSharePath(product);

            const priceDisplayHtml = hasPriceRange
                ? `<span class="prod-price-main">${formatCLP(minPrice)} - ${formatCLP(maxPrice)}</span>`
                : `<span class="prod-price-main">${formatCLP(minPrice)}</span>${discount > 0 && bestOffer.oldPrice ? `<span class="prod-price-old">${formatCLP(bestOffer.oldPrice)}</span>` : ''}`;

            const storeNames = [...new Set(sortedOffers.map(o => o.store).filter(Boolean))];
            const storeSummaryText = storeNames.length > 1
                ? `${storeNames[0]} y ${storeNames.length - 1} tienda${storeNames.length - 1 > 1 ? 's' : ''} más`
                : (storeNames[0] || 'Tienda disponible');

            const cyberBadgeHtml = (isCyberMode && discount >= 20)
                ? `<span class="card-badge card-badge-cyber">Cyber -${discount}%</span>`
                : (discount >= 10 ? `<span class="card-badge card-badge-discount">-${discount}%</span>` : '');

            const intlBadgeHtml = isIntlProduct
                ? `<span class="card-badge card-badge-intl">Internacional</span>`
                : '';
            const histStatus = getHistoricalPriceStatus(product);
            const histBadgeHtml = (!cyberBadgeHtml && histStatus.status === 'low')
                ? `<span class="card-badge card-badge-hist-low" title="${escapeHtml(histStatus.detail)}"><i class="fa-solid fa-arrow-trend-down"></i> Mínimo histórico</span>`
                : '';

            const actionLabel = isIntlProduct
                ? 'Ver en AliExpress <i class="fa-solid fa-arrow-up-right-from-square"></i>'
                : (sortedOffers.length > 1 ? `Comparar (${sortedOffers.length})` : 'Ver oferta');

            card.innerHTML = `
                <div class="product-img">
                    <div class="card-badges-top-left">
                        ${cyberBadgeHtml}
                        ${histBadgeHtml}
                        ${intlBadgeHtml}
                    </div>
                    <div class="card-actions-top-right">
                        <button type="button" class="btn-compare-toggle ${isComparing ? 'active' : ''}" onclick="toggleCompare(${product.id}, event)" aria-label="${isComparing ? 'Quitar del comparador' : 'Comparar modelo'}" title="${isComparing ? 'Quitar del comparador' : 'Comparar modelo'}">
                            <i class="fa-solid ${isComparing ? 'fa-check' : 'fa-scale-balanced'}"></i>
                        </button>
                        <button type="button" class="btn-fav ${isFavorite ? 'active' : ''}" onclick="toggleFavorite(${product.id}, event)" aria-label="${isFavorite ? 'Quitar de favoritos' : 'Guardar en favoritos'}" title="${isFavorite ? 'Quitar de favoritos' : 'Guardar en favoritos'}">
                            <i class="${favIcon}"></i>
                        </button>
                    </div>
                    <img src="${getProductImage(product)}" alt="${escapeHtml(product.brand)} ${escapeHtml(product.model)}"
                         width="320" height="220"
                         data-fallbacks="${getImageFallbacks(product).join('|')}"
                         onerror="handleProductImageError(this, '${cardFallback}')"
                         loading="${index < (lowPowerDevice ? 2 : 3) ? 'eager' : 'lazy'}"
                         decoding="async"
                         fetchpriority="${index < (lowPowerDevice ? 2 : 3) ? 'high' : 'low'}"
                         draggable="false">
                </div>
                <div class="product-info">
                    <span class="prod-brand">${escapeHtml(product.brand || 'Ciclismo')}</span>
                    <h3 class="prod-title">
                        <a class="prod-title-link" href="${productSharePath}" onclick="event.preventDefault(); openProductDetail(${product.id});">${escapeHtml(product.model)}</a>
                    </h3>
                    <div class="prod-price-row">
                        ${priceDisplayHtml}
                    </div>
                    <div class="card-bottom-row">
                        <span class="card-store-summary" title="${escapeHtml(storeNames.join(' • '))}">
                            ${getStoreDot(bestOffer.storeKey)}
                            <span>${escapeHtml(storeSummaryText)}</span>
                        </span>
                        <button type="button" class="btn-ver-ofertas" onclick="openProductAction(${product.id}, event)">
                            ${actionLabel}
                        </button>
                    </div>
                </div>
            `;
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-ver-ofertas') && !e.target.closest('a') && !e.target.closest('.btn-compare-toggle') && !e.target.closest('.btn-fav')) {
                    openProductAction(product.id, e);
                }
            });
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openProductAction(product.id, e);
                }
            });
            fragment.appendChild(card);
        });
        grid.appendChild(fragment);
        openPendingProductFromUrl();
        openPendingCompareFromUrl();
    } catch (e) {
        console.error("Error rendering from API:", e);
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; color: var(--warning); margin-bottom: 1rem; display: block;"></i>
                <h3>Error de conexión</h3>
                <p>No se pudo conectar al servidor de BiciTodo. Asegúrate de que el backend (FastAPI) esté activo.</p>
                <button onclick="render()" style="margin-top:1rem; background:var(--primary); color:#000; border:none; padding:0.65rem 1.5rem; border-radius:8px; font-weight:700; cursor:pointer;">Reintentar</button>
            </div>
        `;
    }
}

function initInteractiveChart(product) {
    const chartSvg = document.getElementById('history-chart');
    if (!chartSvg) return;

    const hist = product.history;
    const histMin = Math.min(...hist);
    const histMax = Math.max(...hist);
    const range = histMax - histMin || 1;

    // SVG coordinate mappings
    // x mapping: 6 points distributed from x=40 to x=365
    const xCoords = [40, 105, 170, 235, 300, 365];
    
    // y mapping: value mapped to y range [25, 115]
    const yCoords = hist.map(val => 120 - ((val - histMin) / range) * 95);

    // Build the SVG path string
    let pathD = `M ${xCoords[0]},${yCoords[0]}`;
    for (let i = 1; i < xCoords.length; i++) {
        pathD += ` L ${xCoords[i]},${yCoords[i]}`;
    }

    // Build the closed area path string
    const areaD = `${pathD} L ${xCoords[xCoords.length - 1]},120 L ${xCoords[0]},120 Z`;

    // Apply paths to elements
    const linePath = document.getElementById('chart-line-path');
    const areaPath = document.getElementById('chart-area-path');
    if (linePath) linePath.setAttribute('d', pathD);
    if (areaPath) areaPath.setAttribute('d', areaD);

    // Interactive mouse tracking
    const trackerLine = document.getElementById('tracker-line');
    const trackerDot = document.getElementById('tracker-dot');
    const tooltip = document.getElementById('chart-tooltip');

    if (!trackerLine || !trackerDot || !tooltip) return;

    // Date/Time descriptions corresponding to the 6 points
    const dates = [
        "Hace 5 semanas",
        "Hace 4 semanas",
        "Hace 3 semanas",
        "Hace 2 semanas",
        "Hace 1 semana",
        "Precio Actual"
    ];

    chartSvg.addEventListener('mousemove', (e) => {
        const rect = chartSvg.getBoundingClientRect();
        // Calculate raw X in SVG view space (which is 0 to 400 pixels wide)
        const mouseX = ((e.clientX - rect.left) / rect.width) * 400;

        // Find the index of the closest point in xCoords
        let closestIdx = 0;
        let minDiff = Infinity;
        xCoords.forEach((x, idx) => {
            const diff = Math.abs(mouseX - x);
            if (diff < minDiff) {
                minDiff = diff;
                closestIdx = idx;
            }
        });

        const activeX = xCoords[closestIdx];
        const activeY = yCoords[closestIdx];
        const activePrice = hist[closestIdx];
        const activeDate = dates[closestIdx];

        // Position vertical line
        trackerLine.setAttribute('x1', activeX);
        trackerLine.setAttribute('x2', activeX);
        trackerLine.style.opacity = '1';

        // Position glowing dot
        trackerDot.setAttribute('cx', activeX);
        trackerDot.setAttribute('cy', activeY);
        trackerDot.style.opacity = '1';

        // Update tooltip content
        const formatCLP = (num) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(num);
        const isBestPrice = activePrice === histMin;
        
        tooltip.innerHTML = `
            <span class="date">${activeDate}</span>
            <span class="price">${formatCLP(activePrice)}</span>
            ${isBestPrice ? '<span class="badge-best">🔥 ¡Mejor Precio!</span>' : ''}
        `;

        // Position tooltip relative to container (convert SVG coords to percentage/pixel inside container)
        const percentX = (activeX / 400) * 100;
        const pixelY = (activeY / 150) * 200; // mapped to container height (200px)
        
        tooltip.style.left = `${percentX}%`;
        tooltip.style.top = `${pixelY - 10}px`;
        tooltip.style.opacity = '1';
    });

    chartSvg.addEventListener('mouseleave', () => {
        trackerLine.style.opacity = '0';
        trackerDot.style.opacity = '0';
        tooltip.style.opacity = '0';
    });
}

toggleMobileFilters = window.toggleMobileFilters = function() {
    const sidebar = document.querySelector('.sidebar-filters');
    if (sidebar) {
        sidebar.classList.toggle('mobile-open');
        const overlay = document.getElementById('filters-overlay');
        if (overlay) {
            overlay.classList.toggle('active');
        }
    }
};

// =============================================
// USER AUTHENTICATION & FAVORITES LOGIC
// =============================================
function loadFavoritesLocalOnly() {
    const local = localStorage.getItem('bicitodo_favorites');
    if (local) {
        try {
            state.favorites = JSON.parse(local);
        } catch (e) {
            state.favorites = [];
        }
    } else {
        state.favorites = [];
    }
}

async function loadFavorites() {
    loadFavoritesLocalOnly();
    
    // Sync with Firestore in background with short timeout so UI never hangs
    if (useFirebase && cloudAuth && cloudAuth.currentUser && cloudDb) {
        try {
            const uid = cloudAuth.currentUser.uid;
            const doc = await Promise.race([
                cloudDb.collection('bicitodo_users').doc(uid).get(),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Firestore timeout')), 2000))
            ]);
            if (doc && doc.exists) {
                const cloudFavs = doc.data().favorites || [];
                const merged = [...state.favorites];
                cloudFavs.forEach(cf => {
                    if (!merged.some(lf => lf.id === cf.id)) {
                        merged.push(cf);
                    }
                });
                state.favorites = merged;
                localStorage.setItem('bicitodo_favorites', JSON.stringify(merged));
                cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: merged }, { merge: true }).catch(() => {});
            } else {
                cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: state.favorites }, { merge: true }).catch(() => {});
            }
        } catch (e) {
            // Ignore Firestore offline/timeout errors silently
        }
    }
}

toggleFavorite = window.toggleFavorite = async function(productId, event) {
    if (event) event.stopPropagation();
    
    const idx = state.favorites.findIndex(f => f.id === productId);
    let msg = '';
    
    if (idx > -1) {
        state.favorites.splice(idx, 1);
        msg = 'Eliminado de tus favoritos.';
    } else {
        state.favorites.push({ id: productId, alertPrice: null });
        msg = 'Agregado a favoritos.';
        
        // Suggest login if not logged in
        if (!state.user) {
            showToast('Guardado localmente. ¡Inicia sesión para respaldar en la nube y activar alertas de correo!');
        }
    }
    
    // Save locally
    localStorage.setItem('bicitodo_favorites', JSON.stringify(state.favorites));
    
    // Save to Firestore if logged in
    if (useFirebase && cloudAuth && cloudAuth.currentUser) {
        try {
            const uid = cloudAuth.currentUser.uid;
            await cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: state.favorites }, { merge: true });
        } catch (e) {
            console.error("Failed to sync favorites deletion:", e);
        }
    }
    
    showToast(msg);
    render(false);
};

toggleFavoriteDetail = window.toggleFavoriteDetail = function(productId) {
    toggleFavorite(productId);
    // Reopen modal to show price alert panel
    openProductDetail(productId);
};

togglePriceAlert = window.togglePriceAlert = async function(productId) {
    const activeFav = state.favorites.find(f => f.id === productId);
    if (!activeFav) return;
    
    const input = document.getElementById('alert-price-input');
    if (!input) return;
    const targetPrice = parseInt(input.value);
    
    if (activeFav.alertPrice !== null && activeFav.alertPrice !== undefined) {
        // Deactivate alert
        activeFav.alertPrice = null;
        showToast('Alerta de precio desactivada.');
    } else {
        // Activate alert
        activeFav.alertPrice = targetPrice;
        showToast(`¡Alerta activada! Te avisaremos si baja de ${formatCLP(targetPrice)}`);
    }
    
    // Save locally
    localStorage.setItem('bicitodo_favorites', JSON.stringify(state.favorites));
    
    // Sync with Firestore if logged in
    if (useFirebase && cloudAuth && cloudAuth.currentUser) {
        try {
            const uid = cloudAuth.currentUser.uid;
            await cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: state.favorites }, { merge: true });
        } catch (e) {
            console.error("Failed to sync price alert to Firestore:", e);
        }
    }
    
    // Refresh the modal
    openProductDetail(productId);
    render();
};

function updateUserMenu() {
    const container = document.getElementById('user-menu-container');
    if (!container) return;
    
    if (state.user) {
        // Logged in
        const displayName = state.user.displayName || state.user.email.split('@')[0];
        const avatarHtml = renderAvatarHTML(state.user.avatar || '🦊', '22px', '1.5px');
        
        container.innerHTML = `
            <button type="button" class="nav-link user-menu-trigger" id="nav-cuenta" onclick="toggleUserDropdown(event)" aria-haspopup="menu" aria-expanded="false" style="display: flex; align-items: center; gap: 0.45rem; cursor: pointer;">
                ${displayName} ${avatarHtml}
            </button>
            <div class="user-menu-dropdown" id="user-menu-dropdown" role="menu">
                <button class="dropdown-item" onclick="openProfileModal(event)"><i class="fa-solid fa-heart" style="color:#ef4444;"></i> Mis Favoritos</button>
                <button class="dropdown-item" onclick="openAuthAlerts(event)"><i class="fa-solid fa-bell" style="color:var(--warning);"></i> Alertas de Precios</button>
                <button class="dropdown-item logout" onclick="handleLogout(event)"><i class="fa-solid fa-right-from-bracket"></i> Cerrar Sesión</button>
            </div>
        `;
    } else {
        // Guest
        container.innerHTML = `
            <a href="#catalog" class="nav-link nav-auth-link" id="nav-cuenta" onclick="openAuthModal(event)">
                <span>Ingresar</span>
            </a>
        `;
    }
}

toggleUserDropdown = window.toggleUserDropdown = function(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const dropdown = document.getElementById('user-menu-dropdown');
    const trigger = document.getElementById('nav-cuenta');
    if (dropdown) {
        dropdown.classList.toggle('show');
        if (trigger) {
            trigger.setAttribute('aria-expanded', dropdown.classList.contains('show') ? 'true' : 'false');
        }
    }
};

openAuthModal = window.openAuthModal = function(event) {
    if (event) event.preventDefault();
    state.activeAuthTab = 'login';
    renderAuthModalContent();
    document.getElementById('auth-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
};

closeAuthModal = window.closeAuthModal = function() {
    document.getElementById('auth-modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
};

function renderAuthModalContent() {
    ensureFirebaseInitialized();
    const content = document.getElementById('auth-modal-content');
    if (!content) return;
    
    if (state.activeAuthTab === 'login') {
        content.innerHTML = `
            <button class="modal-close" onclick="closeAuthModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
            <form class="auth-form-container" onsubmit="handleAuthSubmit(event)">
                <div class="auth-minimal-header">
                    <span class="modal-minimal-eyebrow">Cuenta BiciTodo</span>
                    <h2 class="auth-minimal-title">Iniciar Sesión</h2>
                    <p class="auth-minimal-subtitle">Sincroniza tus favoritos en la nube y activa alertas de baja de precio.</p>
                </div>
                
                <div class="auth-tabs">
                    <button type="button" class="auth-tab-btn active">Ingresar</button>
                    <button type="button" class="auth-tab-btn" onclick="switchAuthTab('signup')">Crear Cuenta</button>
                </div>

                <button type="button" class="btn-auth-google" onclick="handleGoogleLogin(event)">
                    ${GOOGLE_AUTH_LOGO}
                    <span>Continuar con Google</span>
                </button>

                <div class="auth-divider">
                    <span>o con tu correo</span>
                </div>
                
                <div class="auth-inputs">
                    <div class="auth-input-group">
                        <label for="auth-email">Correo Electrónico</label>
                        <input type="email" id="auth-email" required placeholder="tu@correo.cl" autocomplete="email">
                    </div>
                    <div class="auth-input-group">
                        <label for="auth-password">Contraseña</label>
                        <input type="password" id="auth-password" required placeholder="••••••••" autocomplete="current-password">
                    </div>
                </div>
                
                <button type="submit" class="btn-auth-submit">Iniciar Sesión</button>
                
                <div class="auth-switch-text">
                    ¿No tienes cuenta? <span onclick="switchAuthTab('signup')">Regístrate gratis</span>
                </div>
            </form>
        `;
    } else {
        content.innerHTML = `
            <button class="modal-close" onclick="closeAuthModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
            <form class="auth-form-container" onsubmit="handleAuthSubmit(event)">
                <div class="auth-minimal-header">
                    <span class="modal-minimal-eyebrow">Cuenta BiciTodo</span>
                    <h2 class="auth-minimal-title">Crear Cuenta</h2>
                    <p class="auth-minimal-subtitle">Crea tu perfil gratuito en segundos o regístrate con Google.</p>
                </div>
                
                <div class="auth-tabs">
                    <button type="button" class="auth-tab-btn" onclick="switchAuthTab('login')">Ingresar</button>
                    <button type="button" class="auth-tab-btn active">Crear Cuenta</button>
                </div>

                <button type="button" class="btn-auth-google" onclick="handleGoogleLogin(event)">
                    ${GOOGLE_AUTH_LOGO}
                    <span>Registrarse con Google</span>
                </button>

                <div class="auth-divider">
                    <span>o completa tus datos</span>
                </div>
                
                <div class="auth-inputs">
                    <div class="auth-input-group">
                        <label for="auth-name">Nombre</label>
                        <input type="text" id="auth-name" required placeholder="Juan Pérez" autocomplete="name">
                    </div>
                    <div class="auth-input-group">
                        <label for="auth-email">Correo Electrónico</label>
                        <input type="email" id="auth-email" required placeholder="tu@correo.cl" autocomplete="email">
                    </div>
                    <div class="auth-input-group">
                        <label for="auth-password">Contraseña</label>
                        <input type="password" id="auth-password" required minlength="6" placeholder="Mínimo 6 caracteres" autocomplete="new-password">
                    </div>
                </div>
                
                <div class="auth-avatar-picker">
                    <label class="auth-avatar-label">Elige tu avatar:</label>
                    <div class="profile-avatar-grid">
                        ${Object.keys(EMOJI_GRADIENTS).map(emoji => {
                            const isActive = state.selectedSignupAvatar === emoji;
                            return `
                                <button type="button" onclick="selectSignupAvatar('${emoji}')" style="background: ${EMOJI_GRADIENTS[emoji]};" class="avatar-signup-pill ${isActive ? 'active-avatar' : ''}" title="Elegir ${emoji}">
                                    ${emoji}
                                </button>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <button type="submit" class="btn-auth-submit">Crear Cuenta</button>
                
                <div class="auth-switch-text">
                    ¿Ya tienes una cuenta? <span onclick="switchAuthTab('login')">Inicia sesión</span>
                </div>
            </form>
        `;
    }
}

switchAuthTab = window.switchAuthTab = function(tab) {
    state.activeAuthTab = tab;
    renderAuthModalContent();
};

openAuthAlerts = window.openAuthAlerts = function(event) {
    if (event) event.preventDefault();
    openProfileModal(event);
};

handleAuthSubmit = window.handleAuthSubmit = async function(event) {
    event.preventDefault();
    ensureFirebaseInitialized();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    
    if (useFirebase && cloudAuth) {
        const submitBtn = event.target ? event.target.querySelector('.btn-auth-submit') : null;
        const originalBtnText = submitBtn ? submitBtn.textContent : '';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Ingresando...';
        }
        try {
            if (state.activeAuthTab === 'login') {
                const userCred = await cloudAuth.signInWithEmailAndPassword(email, password);
                const loggedUser = {
                    uid: userCred.user.uid,
                    email: userCred.user.email,
                    displayName: userCred.user.displayName || email.split('@')[0],
                    avatar: userCred.user.photoURL || '🦊'
                };
                state.user = loggedUser;
                cacheAuthUserProfile(loggedUser);
                closeAuthModal();
                updateUserMenu();
                showToast('¡Sesión iniciada con éxito!');
            } else {
                const name = document.getElementById('auth-name').value;
                const avatar = state.selectedSignupAvatar || '🦊';
                const userCred = await cloudAuth.createUserWithEmailAndPassword(email, password);
                state.user = {
                    uid: userCred.user.uid,
                    email: userCred.user.email,
                    displayName: name,
                    avatar: avatar
                };
                cacheAuthUserProfile(state.user);
                closeAuthModal();
                updateUserMenu();
                showToast('¡Cuenta creada con éxito!');

                // Actualizar perfil y Firestore en segundo plano sin bloquear el cierre del modal
                userCred.user.updateProfile({ displayName: name, photoURL: avatar }).catch(() => {});
                if (cloudDb) {
                    cloudDb.collection('bicitodo_users').doc(userCred.user.uid).set({
                        displayName: name,
                        email: email,
                        avatar: avatar,
                        favorites: state.favorites
                    }, { merge: true }).catch(() => {});
                }
            }
            loadFavorites().then(() => {
                updateUserMenu();
            }).catch(() => {});
        } catch (error) {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText || 'Iniciar Sesión';
            }
            console.error("Auth error:", error);
            let friendlyMsg = error.message || 'No se pudo autenticar.';
            if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password' || error.code === 'auth/user-not-found') {
                friendlyMsg = 'Correo o contraseña incorrectos.';
            } else if (error.code === 'auth/email-already-in-use') {
                friendlyMsg = 'Este correo ya está registrado. Inicia sesión o usa Google.';
            }
            showToast('Error: ' + friendlyMsg);
        }
    } else {
        showToast('Iniciando sesión en modo local...');
        setTimeout(() => {
            if (state.activeAuthTab === 'login') {
                let savedAvatar = '🦊';
                try {
                    const mockData = localStorage.getItem('bicitodo_mock_user');
                    if (mockData) {
                        const parsed = JSON.parse(mockData);
                        if (parsed.email === email && parsed.avatar) {
                            savedAvatar = parsed.avatar;
                        }
                    }
                } catch (e) {}
                
                state.user = {
                    email: email,
                    displayName: email.split('@')[0],
                    avatar: savedAvatar
                };
                showToast('Sesión iniciada.');
            } else {
                const name = document.getElementById('auth-name').value;
                state.user = {
                    email: email,
                    displayName: name,
                    avatar: state.selectedSignupAvatar || '🦊'
                };
                showToast('Cuenta creada.');
            }
            localStorage.setItem('bicitodo_mock_user', JSON.stringify(state.user));
            loadFavorites().then(() => {
                updateUserMenu();
                closeAuthModal();
                render(false);
            });
        }, 400);
    }
};

async function finalizeGoogleUserSession(user) {
    if (!user) return;
    const cached = getCachedAuthUserProfile();
    const fallbackAvatar = (cached && cached.uid === user.uid && cached.avatar) ? cached.avatar : (user.photoURL || '🦊');
    state.user = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName || (user.email ? user.email.split('@')[0] : 'Ciclista'),
        avatar: fallbackAvatar
    };
    cacheAuthUserProfile(state.user);

    // Respuesta visual INSTANTÁNEA: cerrar modal, actualizar navbar y mostrar bienvenida sin esperar a Firestore
    loadFavoritesLocalOnly();
    closeAuthModal();
    updateUserMenu();
    showToast(`¡Bienvenido, ${state.user.displayName}! Sesión iniciada con Google.`);

    // Sincronizar Firestore en segundo plano sin bloquear la pantalla
    if (cloudDb) {
        Promise.race([
            cloudDb.collection('bicitodo_users').doc(user.uid).get(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
        ]).then((userDoc) => {
            if (!userDoc || !userDoc.exists) {
                cloudDb.collection('bicitodo_users').doc(user.uid).set({
                    displayName: state.user.displayName,
                    email: user.email,
                    avatar: fallbackAvatar,
                    favorites: state.favorites || []
                }, { merge: true }).catch(() => {});
            } else if (userDoc.data()?.avatar && userDoc.data().avatar !== state.user.avatar) {
                state.user.avatar = userDoc.data().avatar;
                cacheAuthUserProfile(state.user);
                updateUserMenu();
            }
        }).catch(() => {});
    }

    loadFavorites().then(() => {
        updateUserMenu();
    }).catch(() => {});
}

handleGoogleLogin = window.handleGoogleLogin = async function(event) {
    if (event) event.preventDefault();
    ensureFirebaseInitialized();

    // Nota importante de Firebase Auth: por defecto Firebase autoriza 'localhost' pero no '127.0.0.1'.
    // Si el usuario está en 127.0.0.1, redirigimos automáticamente a localhost en el mismo puerto para que el popup OAuth de Google sea autorizado por Firebase.
    if (window.location.hostname === '127.0.0.1') {
        const targetUrl = new URL(window.location.href);
        targetUrl.hostname = 'localhost';
        targetUrl.searchParams.set('google_auth', '1');
        showToast('Redirigiendo a localhost para autorizar Google con Firebase...');
        window.location.href = targetUrl.toString();
        return;
    }

    if (useFirebase && cloudAuth) {
        try {
            const googleBtn = event && event.currentTarget ? event.currentTarget : document.querySelector('.btn-auth-google');
            if (googleBtn) {
                googleBtn.style.opacity = '0.75';
                const span = googleBtn.querySelector('span');
                if (span) span.textContent = 'Conectando con Google...';
            }
            const provider = new firebase.auth.GoogleAuthProvider();
            provider.setCustomParameters({ prompt: 'select_account' });
            const result = await cloudAuth.signInWithPopup(provider);
            if (result && result.user) {
                await finalizeGoogleUserSession(result.user);
            }
        } catch (error) {
            const googleBtn = document.querySelector('.btn-auth-google');
            if (googleBtn) {
                googleBtn.style.opacity = '';
                const span = googleBtn.querySelector('span');
                if (span) span.textContent = state.activeAuthTab === 'signup' ? 'Registrarse con Google' : 'Continuar con Google';
            }
            console.error("Google Auth error:", error);
            if (error && error.code === 'auth/popup-blocked') {
                try {
                    showToast('Ventana emergente bloqueada, redirigiendo a Google...');
                    const provider = new firebase.auth.GoogleAuthProvider();
                    provider.setCustomParameters({ prompt: 'select_account' });
                    await cloudAuth.signInWithRedirect(provider);
                    return;
                } catch (redirErr) {
                    console.error("Google Redirect error:", redirErr);
                }
            }
            if (error && error.code === 'auth/popup-closed-by-user') {
                showToast('Inicio de sesión con Google cancelado.');
                return;
            }
            if (error && error.code === 'auth/unauthorized-domain') {
                showToast(`Dominio (${window.location.hostname}) no autorizado en Firebase Console -> Authentication -> Settings -> Authorized domains.`);
                return;
            }
            showToast('Error al conectar con Google: ' + (error.message || 'Intenta nuevamente'));
        }
    } else {
        showToast('Cargando servicios de autenticación de Google, intenta en un segundo...');
    }
};

crearAlertaSupabase = window.crearAlertaSupabase = async function(productId) {
    if (!state.user) {
        showToast('Inicia sesión para activar alertas de correo.');
        openAuthModal();
        return;
    }
    const input = document.getElementById('alert-price-input');
    const targetPrice = input ? parseInt(input.value) : 0;
    const email = state.user.email;
    if (!targetPrice || targetPrice <= 0) {
        showToast('Ingresa un precio objetivo valido.');
        if (input) input.focus();
        return;
    }
    
    try {
        showToast('Creando alerta en la nube...');
        const response = await fetch(`${API_BASE_URL}/api/crear-alerta`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email_usuario: email,
                id_producto: productId,
                precio_actual: targetPrice
            })
        });
        if (response.ok) {
            showToast('¡Alerta de precio creada!');
            
            const activeFav = state.favorites.find(f => f.id === productId);
            if (activeFav) {
                activeFav.alertPrice = targetPrice;
            } else {
                state.favorites.push({ id: productId, alertPrice: targetPrice });
            }
            localStorage.setItem('bicitodo_favorites', JSON.stringify(state.favorites));
            openProductDetail(productId);
            render(false);
        } else {
            const err = await response.json();
            showToast('Error: ' + (err.detail || 'No se pudo crear la alerta'));
        }
    } catch(e) {
        showToast('Error de conexión con el servidor.');
        console.error(e);
    }
};

handleLogout = window.handleLogout = async function(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const dropdown = document.getElementById('user-menu-dropdown');
    if (dropdown) dropdown.classList.remove('show');
    state.user = null;
    state.favorites = [];
    clearAuthUserProfileCache();
    localStorage.removeItem('bicitodo_mock_user');
    localStorage.removeItem('bicitodo_favorites');
    updateUserMenu();
    render(false);
    if (useFirebase && cloudAuth) {
        try {
            await cloudAuth.signOut();
            showToast('Sesión cerrada.');
        } catch (e) {
            showToast('Error al cerrar sesión.');
        }
    } else {
        showToast('Sesión cerrada.');
    }
};

function setupFirebaseAuthListener() {
    ensureFirebaseInitialized();

    const overlay = document.getElementById('auth-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeAuthModal();
        });
    }

    // Si venimos redirigidos desde 127.0.0.1 -> localhost/?google_auth=1, abrimos el modal de acceso automáticamente
    try {
        const params = new URLSearchParams(window.location.search);
        if (params.get('google_auth') === '1') {
            params.delete('google_auth');
            const cleanSearch = params.toString();
            const newUrl = window.location.pathname + (cleanSearch ? `?${cleanSearch}` : '') + window.location.hash;
            window.history.replaceState({}, '', newUrl);
            setTimeout(() => {
                openAuthModal();
                showToast('Haz clic en "Continuar con Google" para iniciar sesión.');
            }, 250);
        }
    } catch (_) {}

    if (useFirebase && cloudAuth) {
        const cachedUser = getCachedAuthUserProfile();
        if (cachedUser) {
            state.user = cachedUser;
            updateUserMenu();
        }

        if (typeof cloudAuth.getRedirectResult === 'function') {
            cloudAuth.getRedirectResult().then((result) => {
                if (result && result.user) {
                    finalizeGoogleUserSession(result.user);
                }
            }).catch((err) => {
                console.warn("Redirect auth check:", err);
            });
        }

        cloudAuth.onAuthStateChanged((user) => {
            if (user) {
                const latestCache = getCachedAuthUserProfile();
                const userAvatar = (latestCache && latestCache.uid === user.uid && latestCache.avatar) ? latestCache.avatar : (user.photoURL || '🦊');
                const userDisplayName = user.displayName || latestCache?.displayName || (user.email ? user.email.split('@')[0] : 'Usuario');
                state.user = {
                    uid: user.uid,
                    email: user.email,
                    displayName: userDisplayName,
                    avatar: userAvatar
                };
                cacheAuthUserProfile(state.user);
                loadFavoritesLocalOnly();
                updateUserMenu();

                // Sincronización silenciosa en segundo plano
                if (cloudDb) {
                    Promise.race([
                        cloudDb.collection('bicitodo_users').doc(user.uid).get(),
                        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
                    ]).then((doc) => {
                        if (doc && doc.exists && state.user) {
                            if (doc.data().avatar) state.user.avatar = doc.data().avatar;
                            if (doc.data().displayName) state.user.displayName = doc.data().displayName;
                            cacheAuthUserProfile(state.user);
                            updateUserMenu();
                        }
                    }).catch(() => {});
                }
                loadFavorites().catch(() => {});
            } else {
                state.user = null;
                clearAuthUserProfileCache();
                loadFavoritesLocalOnly();
                updateUserMenu();
            }
        });
    } else {
        const mock = localStorage.getItem('bicitodo_mock_user');
        if (mock) {
            try {
                state.user = JSON.parse(mock);
            } catch (e) {
                state.user = null;
            }
        }
        loadFavorites().then(() => {
            updateUserMenu();
            render(false);
        });
    }
}

// Close dropdown on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('#user-menu-container')) {
        const dropdown = document.getElementById('user-menu-dropdown');
        if (dropdown) dropdown.classList.remove('show');
        const trigger = document.getElementById('nav-cuenta');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }
});

// =========================================================================
// 6 PREMIUM FEATURES:
// 1. Bike Fit Calculator (Calculadora de Talla en 10s)
// 2. Historical Price Indicator (Semáforo de Precio Histórico)
// 3. Instant Search Palette with Live Preview (Ctrl + K)
// 4. 3-Step Interactive Bike Advisor (Asesor en 3 pasos)
// 5. WhatsApp & Direct Link Comparison Sharing (?compare=id1,id2)
// 6. Component / Drivetrain Tier Filter (Shimano / SRAM / Carbon)
// =========================================================================

// --- FEATURE 2: HISTORICAL PRICE INDICATOR ---
function getHistoricalPriceStatus(product = {}) {
    const bestOffer = getBestProductOffer(product) || { price: 0 };
    const currentPrice = Number(bestOffer.price || 0);
    const rawHist = Array.isArray(product.history) && product.history.length > 0
        ? product.history.map(Number).filter(n => Number.isFinite(n) && n > 0)
        : [currentPrice];
    const allPoints = [...rawHist, currentPrice].filter(n => n > 0);
    const histMin = allPoints.length ? Math.min(...allPoints) : currentPrice;
    const histMax = allPoints.length ? Math.max(...allPoints) : currentPrice;
    const histAvg = allPoints.length
        ? Math.round(allPoints.reduce((a, b) => a + b, 0) / allPoints.length)
        : currentPrice;
    const oldPrice = Number(bestOffer.oldPrice || 0);

    if (currentPrice > 0 && ((currentPrice <= histMin * 1.01 && histMax > histMin * 1.03) || (oldPrice >= currentPrice * 1.12))) {
        return {
            status: 'low',
            badge: 'Mínimo histórico',
            icon: 'fa-arrow-trend-down',
            detail: 'Está en su precio más bajo registrado. Excelente momento para comprar.',
            histMin,
            histAvg: Math.max(histAvg, oldPrice || histAvg),
            histMax: Math.max(histMax, oldPrice || histMax)
        };
    }
    if (currentPrice > 0 && (currentPrice <= histAvg * 0.96 || (oldPrice > currentPrice))) {
        return {
            status: 'good',
            badge: 'Buen momento para comprar',
            icon: 'fa-circle-check',
            detail: 'Su precio actual se encuentra bajo el promedio histórico de mercado.',
            histMin,
            histAvg: Math.max(histAvg, oldPrice || histAvg),
            histMax
        };
    }
    if (currentPrice > histAvg * 1.06) {
        return {
            status: 'high',
            badge: 'Sobre el promedio',
            icon: 'fa-bell',
            detail: 'Estuvo más barata hace unas semanas. Te recomendamos activar una alerta de precio.',
            histMin,
            histAvg,
            histMax
        };
    }
    return {
        status: 'normal',
        badge: 'Precio habitual',
        icon: 'fa-equals',
        detail: 'Se mantiene estable dentro de su rango promedio en tiendas chilenas.',
        histMin,
        histAvg,
        histMax
    };
}

function renderHistoricalPriceBanner(product) {
    if (!product) return '';
    const info = getHistoricalPriceStatus(product);
    return `
        <div class="hist-price-banner status-${info.status}">
            <div class="hist-price-banner-top">
                <span class="hist-price-pill status-${info.status}">
                    <i class="fa-solid ${info.icon}"></i> ${escapeHtml(info.badge)}
                </span>
                <span class="hist-price-metrics">
                    Mín. histórico: <strong>${formatCLP(info.histMin)}</strong> · Promedio: <strong>${formatCLP(info.histAvg)}</strong>
                </span>
            </div>
            <p class="hist-price-detail">${escapeHtml(info.detail)}</p>
        </div>
    `;
}

// --- FEATURE 6: COMPONENT / DRIVETRAIN TIER FILTER ---
toggleSpecChip = window.toggleSpecChip = function(specKey, btnEl) {
    if (!specKey) return;
    isCyberMode = false;
    document.body?.classList.remove('cyber-theme');

    const isSame = state.filters.spec === specKey;
    state.filters.spec = isSame ? null : specKey;
    state.currentPage = 1;

    document.querySelectorAll('.component-tier-pill').forEach(pill => {
        pill.classList.toggle('active', !isSame && pill.dataset.spec === specKey);
    });

    render();
    if (!isSame && btnEl) {
        showToast(`Filtrando por equipamiento: ${btnEl.textContent.trim()}`);
    }
};

// --- FEATURE 5: SHARE COMPARISON VIA WHATSAPP & DIRECT LINK ---
function getCompareShareUrl() {
    const ids = (state.compare || []).slice(0, 3).join(',');
    const url = new URL(window.location.href);
    url.search = '';
    url.hash = '';
    if (ids) url.searchParams.set('compare', ids);
    return url.toString();
}

copyCompareLink = window.copyCompareLink = async function() {
    if (!state.compare || state.compare.length < 2) return;
    const shareUrl = getCompareShareUrl();
    try {
        await navigator.clipboard.writeText(shareUrl);
        showToast('Enlace directo de comparación copiado al portapapeles.');
    } catch (e) {
        window.prompt('Copia el enlace de comparación:', shareUrl);
    }
};

shareCompareWhatsApp = window.shareCompareWhatsApp = function() {
    const products = (state.compare || []).map(id => findProductById(id)).filter(Boolean);
    if (products.length < 2) return;
    const shareUrl = getCompareShareUrl();
    const lines = products.map((p, i) => {
        const best = getBestProductOffer(p) || { price: 0, store: 'Tienda' };
        return `${i + 1}. ${p.brand} ${p.model} — Desde ${formatCLP(best.price)} (${best.store})`;
    });
    const text = `Mira esta comparación de bicicletas en BiciTodo.cl:\n\n${lines.join('\n')}\n\nComparativa completa aquí: ${shareUrl}`;
    const waUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(waUrl, '_blank', 'noopener,noreferrer');
};

async function openPendingCompareFromUrl() {
    if (state.pendingCompareOpened) return;
    const params = new URLSearchParams(window.location.search);
    const compareParam = params.get('compare');
    if (!compareParam) return;

    state.pendingCompareOpened = true;
    const ids = compareParam
        .split(',')
        .map(v => parseInt(v.trim(), 10))
        .filter(n => Number.isFinite(n) && n > 0)
        .slice(0, 3);

    if (ids.length < 2) return;

    for (const id of ids) {
        if (!findProductById(id)) {
            try {
                const q = new URLSearchParams({ producto_id: String(id), page: '1', limit: '1' });
                const resp = await fetch(`${API_BASE_URL}/api/productos?${q.toString()}`, { cache: 'no-store' });
                if (resp.ok) {
                    const data = await resp.json();
                    const p = data.productos?.[0];
                    if (p) {
                        state.data.cache[p.id] = p;
                    }
                }
            } catch (_) {}
        }
    }

    const validIds = ids.filter(id => Boolean(findProductById(id)));
    if (validIds.length >= 2) {
        state.compare = validIds;
        updateCompareBar();
        setTimeout(() => openCompareModal(), 80);
    }
}

// --- FEATURE 1: INTELLIGENT BIKE FIT CALCULATOR (BIOMECÁNICA REAL) ---
const bikeFitState = {
    discipline: 'mtb',
    heightCm: 173,
    inseamCm: ''
};

function calculateBikeFitRecommendation(heightCm, inseamRaw, discipline) {
    const h = Math.max(120, Math.min(215, Number(heightCm) || 173));
    const hasCustomInseam = inseamRaw !== null && inseamRaw !== undefined && String(inseamRaw).trim() !== '' && Number(inseamRaw) >= 45 && Number(inseamRaw) <= 110;
    const inseam = hasCustomInseam
        ? Number(inseamRaw)
        : Math.round(h * 0.455 * 10) / 10;

    // Índice antropométrico pierna/estatura (promedio humano ~0.455)
    const apeRatio = inseam / h;
    let morphologyNote = 'Proporción estándar equilibrada entre torso y piernas.';
    if (apeRatio > 0.47) {
        morphologyNote = 'Piernas largas respecto al torso: te favorece una geometría Endurance (mayor Stack y tee 10 mm más corta).';
    } else if (apeRatio < 0.44) {
        morphologyNote = 'Torso largo respecto a las piernas: prioriza el Reach (alcance horizontal) para no quedar comprimido.';
    }

    // Estatura efectiva ponderada con la entrepierna real (60% entrepierna + 40% estatura)
    const effectiveHeight = hasCustomInseam ? Math.round((h * 0.45) + ((inseam / 0.455) * 0.55)) : h;

    // Fórmulas biomecánicas clásicas:
    // - Ruta / Gravel / Urbana: Entrepierna × 0.65 (cm centro-a-centro / Stack-Reach eq.)
    // - MTB: Entrepierna × 0.226 (pulgadas de tubo de sillín)
    // - Altura de sillín (Greg LeMond): Entrepierna × 0.883 (cm desde centro del eje motor al tope del sillín)
    const exactRoadCm = Math.round(inseam * 0.655);
    const exactMtbIn = (inseam * 0.226).toFixed(1);
    const saddleHeightCm = (inseam * 0.883).toFixed(1);

    // Largo de bielas biomecánico según entrepierna
    let crankLengthMm = '170 mm';
    if (inseam < 74) crankLengthMm = '165 mm';
    else if (inseam < 81) crankLengthMm = '170 mm';
    else if (inseam < 86) crankLengthMm = '172.5 mm';
    else crankLengthMm = '175 mm';

    // Reach de cuadro estimado (mm) y potencia/tee recomendada
    const reachMm = discipline === 'mtb'
        ? Math.round(255 + (effectiveHeight - 135) * 3.15)
        : Math.round(340 + (effectiveHeight - 135) * 0.92);
    const stemMm = discipline === 'mtb'
        ? (effectiveHeight < 168 ? '45 – 50 mm' : '50 – 65 mm')
        : (effectiveHeight < 165 ? '80 mm' : (effectiveHeight < 180 ? '90 – 100 mm' : '100 – 110 mm'));

    let frameCode = 'M';
    let mtbInches = `${exactMtbIn}" (17" – 18")`;
    let roadCm = `${exactRoadCm} cm (53 – 55 cm)`;
    let wheelSize = '29';
    let wheelLabel = 'Aro 29"';

    if (effectiveHeight < 148) {
        frameCode = 'Infantil / Jr';
        mtbInches = `12" – 13.5"`;
        roadCm = `43 – 46 cm`;
        wheelSize = effectiveHeight < 135 ? '20' : '24';
        wheelLabel = effectiveHeight < 135 ? 'Aro 20"' : 'Aro 24"';
    } else if (effectiveHeight < 160) {
        frameCode = 'XS';
        mtbInches = `${exactMtbIn}" (13.5" – 15")`;
        roadCm = `${exactRoadCm} cm (47 – 49 cm)`;
        wheelSize = discipline === 'mtb' ? '27.5' : '700c';
        wheelLabel = discipline === 'mtb' ? 'Aro 27.5"' : '700c';
    } else if (effectiveHeight < 169) {
        frameCode = 'S';
        mtbInches = `${exactMtbIn}" (15" – 16.5")`;
        roadCm = `${exactRoadCm} cm (50 – 52 cm)`;
        wheelSize = discipline === 'mtb' ? '29' : '700c';
        wheelLabel = discipline === 'mtb' ? 'Aro 27.5" / 29"' : '700c';
    } else if (effectiveHeight < 178) {
        frameCode = 'M';
        mtbInches = `${exactMtbIn}" (17" – 18")`;
        roadCm = `${exactRoadCm} cm (53 – 55 cm)`;
        wheelSize = discipline === 'mtb' ? '29' : '700c';
        wheelLabel = discipline === 'mtb' ? 'Aro 29"' : '700c';
    } else if (effectiveHeight < 186) {
        frameCode = 'L';
        mtbInches = `${exactMtbIn}" (18.5" – 19.5")`;
        roadCm = `${exactRoadCm} cm (56 – 58 cm)`;
        wheelSize = discipline === 'mtb' ? '29' : '700c';
        wheelLabel = discipline === 'mtb' ? 'Aro 29"' : '700c';
    } else {
        frameCode = 'XL';
        mtbInches = `${exactMtbIn}" (20" – 21.5")`;
        roadCm = `${exactRoadCm} cm (59 – 62 cm)`;
        wheelSize = discipline === 'mtb' ? '29' : '700c';
        wheelLabel = discipline === 'mtb' ? 'Aro 29"' : '700c';
    }

    const measureDetail = (discipline === 'ruta' || discipline === 'gravel') ? roadCm : mtbInches;

    return {
        frameCode,
        measureDetail,
        wheelSize,
        wheelLabel,
        inseam,
        saddleHeightCm,
        crankLengthMm,
        reachMm,
        stemMm,
        morphologyNote
    };
}

openBikeFitModal = window.openBikeFitModal = function(event) {
    if (event) event.preventDefault();
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;

    const rec = calculateBikeFitRecommendation(bikeFitState.heightCm, bikeFitState.inseamCm, bikeFitState.discipline);

    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-minimal-shell">
            <div class="modal-minimal-header">
                <span class="modal-minimal-eyebrow">Biomecánica Aplicada · Método LeMond & Stack/Reach</span>
                <h2 class="modal-minimal-title">Calculadora Bike Fit</h2>
                <p class="modal-minimal-subtitle">
                    Calcula tu talla real combinando tu estatura y longitud de entrepierna (fórmula biomecánica de Greg LeMond <code>0.883 × entrepierna</code> + conversión por geometría de cuadro).
                </p>
            </div>

            <div class="bikefit-layout">
                <div class="bikefit-controls">
                    <div class="bikefit-field">
                        <label class="bikefit-label">1. Geometría / Disciplina</label>
                        <div class="bikefit-discipline-grid">
                            <button type="button" class="bikefit-disc-btn ${bikeFitState.discipline === 'mtb' ? 'active' : ''}" onclick="updateBikeFitResult('mtb', null, null)">
                                <i class="fa-solid fa-mountain-sun"></i> Montaña (MTB)
                            </button>
                            <button type="button" class="bikefit-disc-btn ${bikeFitState.discipline === 'ruta' ? 'active' : ''}" onclick="updateBikeFitResult('ruta', null, null)">
                                <i class="fa-solid fa-road"></i> Ruta
                            </button>
                            <button type="button" class="bikefit-disc-btn ${bikeFitState.discipline === 'gravel' ? 'active' : ''}" onclick="updateBikeFitResult('gravel', null, null)">
                                <i class="fa-solid fa-compass"></i> Gravel
                            </button>
                            <button type="button" class="bikefit-disc-btn ${bikeFitState.discipline === 'urbana' ? 'active' : ''}" onclick="updateBikeFitResult('urbana', null, null)">
                                <i class="fa-solid fa-city"></i> Urbana
                            </button>
                        </div>
                    </div>

                    <div class="bikefit-field">
                        <div class="bikefit-label-row">
                            <label class="bikefit-label" for="bikefit-height-range">2. Tu estatura total</label>
                            <strong id="bikefit-height-display" class="bikefit-value-pill">${bikeFitState.heightCm} cm</strong>
                        </div>
                        <input type="range" id="bikefit-height-range" min="130" max="205" step="1" value="${bikeFitState.heightCm}"
                               class="bikefit-slider" oninput="updateBikeFitResult(null, this.value, null)">
                        <div class="bikefit-scale-labels">
                            <span>130 cm</span>
                            <span>170 cm</span>
                            <span>205 cm</span>
                        </div>
                    </div>

                    <div class="bikefit-field">
                        <label class="bikefit-label" for="bikefit-inseam-input">3. Entrepierna en cm (descalzo del suelo a la ingle)</label>
                        <div class="bikefit-inseam-row">
                            <input type="number" id="bikefit-inseam-input" min="48" max="105" step="0.5" placeholder="Estimada: ${rec.inseam} cm (escribe la tuya para mayor precisión)"
                                   value="${bikeFitState.inseamCm}" class="newsletter-minimal-input"
                                   oninput="updateBikeFitResult(null, null, this.value)">
                            <span class="bikefit-inseam-hint">Al ingresar tu entrepierna real, recalculamos tanto la talla de cuadro como la altura del sillín y largo de bielas.</span>
                        </div>
                    </div>
                </div>

                <div class="bikefit-result-card" id="bikefit-result-box">
                    <span class="bikefit-result-eyebrow">Resultado Biomecánico</span>
                    <div class="bikefit-main-size">
                        <span class="bikefit-size-letter" id="bf-letter">${rec.frameCode}</span>
                        <div class="bikefit-size-sub">
                            <strong id="bf-measure">Tubo: ${rec.measureDetail}</strong>
                            <span id="bf-wheel">${rec.wheelLabel} recomendado</span>
                        </div>
                    </div>
                    <div class="bikefit-metrics-grid">
                        <div class="bikefit-metric-box">
                            <span class="bikefit-metric-label">Altura de sillín (LeMond)</span>
                            <strong class="bikefit-metric-val" id="bf-saddle">${rec.saddleHeightCm} cm</strong>
                        </div>
                        <div class="bikefit-metric-box">
                            <span class="bikefit-metric-label">Reach / Potencia (Tee)</span>
                            <strong class="bikefit-metric-val" id="bf-reach">~${rec.reachMm} mm · Tee ${rec.stemMm}</strong>
                        </div>
                        <div class="bikefit-metric-box">
                            <span class="bikefit-metric-label">Largo de biela ideal</span>
                            <strong class="bikefit-metric-val" id="bf-crank">${rec.crankLengthMm}</strong>
                        </div>
                        <div class="bikefit-metric-box">
                            <span class="bikefit-metric-label">Entrepierna considerada</span>
                            <strong class="bikefit-metric-val" id="bf-inseam">${rec.inseam} cm</strong>
                        </div>
                    </div>
                    <p class="bikefit-tip" id="bf-morphology">${escapeHtml(rec.morphologyNote)}</p>
                    <button type="button" class="btn-minimal-primary" style="width:100%;" onclick="applyBikeFitToCatalog()">
                        Filtrar bicicletas compatibles en el catálogo <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

updateBikeFitResult = window.updateBikeFitResult = function(newDisc, newHeight, newInseam) {
    if (newDisc) bikeFitState.discipline = newDisc;
    if (newHeight !== null && newHeight !== undefined) bikeFitState.heightCm = Number(newHeight);
    if (newInseam !== null && newInseam !== undefined) bikeFitState.inseamCm = newInseam;

    document.querySelectorAll('.bikefit-disc-btn').forEach(btn => {
        const onclickStr = btn.getAttribute('onclick') || '';
        btn.classList.toggle('active', onclickStr.includes(`'${bikeFitState.discipline}'`));
    });

    const heightDisplay = document.getElementById('bikefit-height-display');
    if (heightDisplay) heightDisplay.textContent = `${bikeFitState.heightCm} cm`;

    const rec = calculateBikeFitRecommendation(bikeFitState.heightCm, bikeFitState.inseamCm, bikeFitState.discipline);
    const elLetter = document.getElementById('bf-letter');
    const elMeasure = document.getElementById('bf-measure');
    const elWheel = document.getElementById('bf-wheel');
    const elSaddle = document.getElementById('bf-saddle');
    const elReach = document.getElementById('bf-reach');
    const elCrank = document.getElementById('bf-crank');
    const elInseam = document.getElementById('bf-inseam');
    const elMorph = document.getElementById('bf-morphology');

    if (elLetter) elLetter.textContent = rec.frameCode;
    if (elMeasure) elMeasure.textContent = `Tubo: ${rec.measureDetail}`;
    if (elWheel) elWheel.textContent = `${rec.wheelLabel} recomendado`;
    if (elSaddle) elSaddle.textContent = `${rec.saddleHeightCm} cm`;
    if (elReach) elReach.textContent = `~${rec.reachMm} mm · Tee ${rec.stemMm}`;
    if (elCrank) elCrank.textContent = rec.crankLengthMm;
    if (elInseam) elInseam.textContent = `${rec.inseam} cm`;
    if (elMorph) elMorph.textContent = rec.morphologyNote;
};

applyBikeFitToCatalog = window.applyBikeFitToCatalog = function() {
    const rec = calculateBikeFitRecommendation(bikeFitState.heightCm, bikeFitState.inseamCm, bikeFitState.discipline);
    closeModal();
    setCategory('bicicletas');

    const isJunior = rec.frameCode.startsWith('Infantil');
    const targetTypes = isJunior ? ['infantil'] : [bikeFitState.discipline];
    state.filters.types = targetTypes;

    document.querySelectorAll('#type-filter-list input').forEach(input => {
        input.checked = targetTypes.includes(input.value);
    });
    const allBtn = document.getElementById('btn-all-bike-types');
    if (allBtn) allBtn.classList.remove('active');

    // En la base de datos:
    // - MTB tiene 27.5 y 29 (y 20/24 en infantil)
    // - Ruta tiene 700c
    // - Gravel y Urbana tienen modelos con wheel_size vacío o 29/700c, por lo que no restringimos wheelSizes en gravel/urbana para no ocultar modelos válidos
    if (isJunior) {
        state.filters.wheelSizes = [rec.wheelSize];
    } else if (bikeFitState.discipline === 'mtb') {
        state.filters.wheelSizes = rec.frameCode === 'XS' ? ['27.5'] : (rec.frameCode === 'S' ? ['27.5', '29'] : ['29']);
    } else if (bikeFitState.discipline === 'ruta') {
        state.filters.wheelSizes = ['700c'];
    } else {
        state.filters.wheelSizes = [];
    }

    document.querySelectorAll('.wheel-pill').forEach(pill => {
        pill.classList.toggle('active', state.filters.wheelSizes.includes(pill.dataset.size));
    });

    state.currentPage = 1;
    render();
    const catalogEl = document.getElementById('catalog');
    if (catalogEl) window.scrollTo({ top: catalogEl.offsetTop - 72, behavior: 'smooth' });
    showToast(`Bike Fit aplicado: Talla ${rec.frameCode} (${rec.measureDetail}) · Sillín a ${rec.saddleHeightCm} cm.`);
};

// --- FEATURE 4: 3-STEP INTERACTIVE BIKE ADVISOR ---
const advisorState = {
    terrain: 'mtb',
    budget: '400-800',
    priority: 'value'
};

openBikeAdvisorModal = window.openBikeAdvisorModal = function(event) {
    if (event) event.preventDefault();
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;

    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()" aria-label="Cerrar"><i class="fa-solid fa-xmark"></i></button>
        <div class="modal-minimal-shell">
            <div class="modal-minimal-header">
                <span class="modal-minimal-eyebrow">Asesor Interactivo · 3 Pasos</span>
                <h2 class="modal-minimal-title">Encuentra tu Bicicleta Ideal</h2>
                <p class="modal-minimal-subtitle">
                    Responde estas 3 preguntas rápidas y nuestro algoritmo seleccionará las mejores opciones reales en stock hoy en Chile.
                </p>
            </div>

            <div class="advisor-steps-grid">
                <div class="advisor-step-box">
                    <span class="advisor-step-num">Paso 1 · Terreno principal</span>
                    <div class="advisor-options-col" data-group="terrain">
                        <button type="button" class="advisor-opt-btn ${advisorState.terrain === 'mtb' ? 'active' : ''}" onclick="selectAdvisorOption('terrain', 'mtb', this)">
                            <i class="fa-solid fa-mountain-sun"></i>
                            <div>
                                <strong>Cerro y Senderos (MTB)</strong>
                                <span>Tierra, parques y montaña</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.terrain === 'ruta' ? 'active' : ''}" onclick="selectAdvisorOption('terrain', 'ruta', this)">
                            <i class="fa-solid fa-road"></i>
                            <div>
                                <strong>Carretera y Asfalto (Ruta)</strong>
                                <span>Velocidad y largas distancias</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.terrain === 'gravel' ? 'active' : ''}" onclick="selectAdvisorOption('terrain', 'gravel', this)">
                            <i class="fa-solid fa-compass"></i>
                            <div>
                                <strong>Mixto y Ripio (Gravel)</strong>
                                <span>Aventura en pavimento y tierra</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.terrain === 'urbana' ? 'active' : ''}" onclick="selectAdvisorOption('terrain', 'urbana', this)">
                            <i class="fa-solid fa-city"></i>
                            <div>
                                <strong>Ciudad y Ciclovía (Urbana)</strong>
                                <span>Transporte diario y paseo</span>
                            </div>
                        </button>
                    </div>
                </div>

                <div class="advisor-step-box">
                    <span class="advisor-step-num">Paso 2 · Presupuesto</span>
                    <div class="advisor-options-col" data-group="budget">
                        <button type="button" class="advisor-opt-btn ${advisorState.budget === 'sub400' ? 'active' : ''}" onclick="selectAdvisorOption('budget', 'sub400', this)">
                            <i class="fa-solid fa-wallet"></i>
                            <div>
                                <strong>Hasta $400.000</strong>
                                <span>Iniciación y uso recreativo</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.budget === '400-800' ? 'active' : ''}" onclick="selectAdvisorOption('budget', '400-800', this)">
                            <i class="fa-solid fa-scale-balanced"></i>
                            <div>
                                <strong>$400.000 – $800.000</strong>
                                <span>Gama media y componentes fiables</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.budget === '800-1500' ? 'active' : ''}" onclick="selectAdvisorOption('budget', '800-1500', this)">
                            <i class="fa-solid fa-medal"></i>
                            <div>
                                <strong>$800.000 – $1.500.000</strong>
                                <span>Entrenamiento avanzado</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.budget === '1500plus' ? 'active' : ''}" onclick="selectAdvisorOption('budget', '1500plus', this)">
                            <i class="fa-solid fa-trophy"></i>
                            <div>
                                <strong>Más de $1.500.000</strong>
                                <span>Alta gama / Carbono / Competición</span>
                            </div>
                        </button>
                    </div>
                </div>

                <div class="advisor-step-box">
                    <span class="advisor-step-num">Paso 3 · Qué priorizas</span>
                    <div class="advisor-options-col" data-group="priority">
                        <button type="button" class="advisor-opt-btn ${advisorState.priority === 'value' ? 'active' : ''}" onclick="selectAdvisorOption('priority', 'value', this)">
                            <i class="fa-solid fa-star"></i>
                            <div>
                                <strong>Mejor Calidad-Precio</strong>
                                <span>Máximo equipamiento por tu dinero</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.priority === 'price-asc' ? 'active' : ''}" onclick="selectAdvisorOption('priority', 'price-asc', this)">
                            <i class="fa-solid fa-tag"></i>
                            <div>
                                <strong>El menor precio posible</strong>
                                <span>Opciones más económicas primero</span>
                            </div>
                        </button>
                        <button type="button" class="advisor-opt-btn ${advisorState.priority === 'discount' ? 'active' : ''}" onclick="selectAdvisorOption('priority', 'discount', this)">
                            <i class="fa-solid fa-bolt"></i>
                            <div>
                                <strong>Mayor descuento hoy</strong>
                                <span>Liquidaciones y rebajas activas</span>
                            </div>
                        </button>
                    </div>
                </div>
            </div>

            <div id="advisor-results-area" class="advisor-results-area">
                <button type="button" class="btn-minimal-primary" onclick="runBikeAdvisor()">
                    Descubrir mis 3 bicicletas recomendadas <i class="fa-solid fa-wand-magic-sparkles"></i>
                </button>
            </div>
        </div>
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    runBikeAdvisor();
};

selectAdvisorOption = window.selectAdvisorOption = function(group, value, btnEl) {
    advisorState[group] = value;
    const container = btnEl?.closest('.advisor-options-col');
    if (container) {
        container.querySelectorAll('.advisor-opt-btn').forEach(b => b.classList.remove('active'));
    }
    if (btnEl) btnEl.classList.add('active');
    runBikeAdvisor();
};

runBikeAdvisor = window.runBikeAdvisor = async function() {
    const resultsArea = document.getElementById('advisor-results-area');
    if (!resultsArea) return;

    resultsArea.innerHTML = `
        <div class="news-minimal-loading" style="padding:1rem;">
            <i class="fa-solid fa-circle-notch fa-spin"></i>
            <p>Analizando catálogo en tiempo real...</p>
        </div>
    `;

    const budgetRanges = {
        'sub400': [0, 400000],
        '400-800': [400000, 800000],
        '800-1500': [800000, 1500000],
        '1500plus': [1500000, null]
    };
    const [pMin, pMax] = budgetRanges[advisorState.budget] || [0, null];

    const params = new URLSearchParams({
        page: '1',
        limit: '24',
        categoria: 'bicicletas',
        tipo: advisorState.terrain,
        sort_by: advisorState.priority === 'value' ? 'relevant' : advisorState.priority
    });
    if (pMin) params.set('price_min', String(pMin));
    if (pMax) params.set('price_max', String(pMax));

    try {
        const resp = await fetch(`${API_BASE_URL}/api/productos?${params.toString()}`, { cache: 'no-store' });
        const data = resp.ok ? await resp.json() : { productos: [] };
        let items = (data.productos || []).filter(p => !isBlockedSyntheticProduct(p));

        if (advisorState.priority === 'value') {
            items.sort((a, b) => (calculateValueScore(b) || 0) - (calculateValueScore(a) || 0));
        }

        const top3 = items.slice(0, 3);
        items.forEach(p => { state.data.cache[p.id] = p; });

        if (top3.length === 0) {
            resultsArea.innerHTML = `
                <div class="advisor-empty">
                    <p>No encontramos modelos exactos en ese rango específico, pero podemos mostrarte todas las opciones de esa categoría.</p>
                    <button type="button" class="btn-minimal-primary" onclick="applyAdvisorToCatalog(true)">
                        Ver todas las bicicletas ${advisorState.terrain.toUpperCase()}
                    </button>
                </div>
            `;
            return;
        }

        const cardsHtml = top3.map((p, idx) => {
            const best = getBestProductOffer(p) || { price: 0, store: 'Tienda' };
            const score = calculateValueScore(p) || 82;
            const rankLabels = ['Opción #1 Ideal', 'Alternativa Destacada', 'Gran Oportunidad'];
            return `
                <div class="advisor-rec-card" onclick="closeModal(); openProductDetail(${p.id});">
                    <span class="advisor-rec-badge">${rankLabels[idx] || 'Recomendada'} · ${score}/100</span>
                    <div class="advisor-rec-img">
                        <img src="${getProductImage(p)}" alt="${escapeHtml(p.model)}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)">
                    </div>
                    <span class="advisor-rec-brand">${escapeHtml(p.brand)}</span>
                    <h4 class="advisor-rec-title">${escapeHtml(p.model)}</h4>
                    <div class="advisor-rec-price">${formatCLP(best.price)}</div>
                    <span class="advisor-rec-store">${getStoreDot(best.storeKey)} Disponible en ${escapeHtml(best.store)}</span>
                </div>
            `;
        }).join('');

        resultsArea.innerHTML = `
            <div class="advisor-recs-header">
                <span>Top ${top3.length} bicicletas recomendadas para ti (${data.total_count || items.length} encontradas)</span>
                <button type="button" class="btn-minimal-primary" onclick="applyAdvisorToCatalog(false)">
                    Ver las ${data.total_count || items.length} en el catálogo <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
            <div class="advisor-recs-grid">
                ${cardsHtml}
            </div>
        `;
    } catch (e) {
        resultsArea.innerHTML = `
            <button type="button" class="btn-minimal-primary" onclick="applyAdvisorToCatalog(false)">
                Aplicar filtros al catálogo <i class="fa-solid fa-arrow-right"></i>
            </button>
        `;
    }
};

applyAdvisorToCatalog = window.applyAdvisorToCatalog = function(ignoreBudget = false) {
    const budgetRanges = {
        'sub400': [0, 400000],
        '400-800': [400000, 800000],
        '800-1500': [800000, 1500000],
        '1500plus': [1500000, null]
    };
    const [pMin, pMax] = ignoreBudget ? [null, null] : (budgetRanges[advisorState.budget] || [null, null]);

    closeModal();
    setCategory('bicicletas');

    state.filters.types = [advisorState.terrain];
    document.querySelectorAll('#type-filter-list input').forEach(input => {
        input.checked = (input.value === advisorState.terrain);
    });
    const allBtn = document.getElementById('btn-all-bike-types');
    if (allBtn) allBtn.classList.remove('active');

    state.filters.priceMin = pMin;
    state.filters.priceMax = pMax;
    const minEl = document.getElementById('price-min');
    const maxEl = document.getElementById('price-max');
    if (minEl) minEl.value = pMin || '';
    if (maxEl) maxEl.value = pMax || '';

    state.sortBy = advisorState.priority === 'value' ? 'relevant' : advisorState.priority;
    const sortEl = document.getElementById('sort-select');
    if (sortEl) sortEl.value = state.sortBy;

    state.currentPage = 1;
    render();
    const catalogEl = document.getElementById('catalog');
    if (catalogEl) window.scrollTo({ top: catalogEl.offsetTop - 72, behavior: 'smooth' });
    showToast('Recomendaciones del asesor aplicadas al catálogo.');
};

// --- FEATURE 3: INSTANT SEARCH COMMAND PALETTE (CTRL + K) ---
let instantSearchTimer = null;

function renderDefaultInstantDropdown() {
    const dropdown = document.getElementById('search-instant-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = `
        <div class="instant-search-section">
            <span class="instant-search-label">Búsquedas populares en Chile</span>
            <div class="instant-search-chips">
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Trek')">Trek</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Specialized')">Specialized</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Scott')">Scott</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Oxford')">Oxford</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Deore')">Shimano Deore</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Gravel')">Gravel</button>
                <button type="button" class="instant-chip" onclick="applyInstantSearchTerm('Carbon')">Carbono</button>
            </div>
        </div>
        <div class="instant-search-section instant-search-tools">
            <button type="button" class="instant-tool-btn" onclick="document.getElementById('search-instant-dropdown')?.classList.remove('active'); openBikeAdvisorModal(event);">
                <i class="fa-solid fa-compass"></i> Asesor: Encuentra tu bici en 3 pasos
            </button>
            <button type="button" class="instant-tool-btn" onclick="document.getElementById('search-instant-dropdown')?.classList.remove('active'); openBikeFitModal(event);">
                <i class="fa-solid fa-ruler-horizontal"></i> Calculadora de Talla (Bike Fit)
            </button>
        </div>
    `;
}

async function updateInstantSearchPreview(rawQuery) {
    const dropdown = document.getElementById('search-instant-dropdown');
    if (!dropdown) return;
    const q = (rawQuery || '').trim();
    if (q.length < 2) {
        renderDefaultInstantDropdown();
        return;
    }

    try {
        const params = new URLSearchParams({
            page: '1',
            limit: '5',
            search: q
        });
        const resp = await fetch(`${API_BASE_URL}/api/productos?${params.toString()}`, { cache: 'no-store' });
        if (!resp.ok) return;
        const data = await resp.json();
        const items = (data.productos || []).filter(p => !isBlockedSyntheticProduct(p)).slice(0, 5);
        items.forEach(p => { state.data.cache[p.id] = p; });

        if (items.length === 0) {
            dropdown.innerHTML = `
                <div class="instant-search-empty">
                    Sin coincidencias directas para "<strong>${escapeHtml(q)}</strong>".
                </div>
            `;
            return;
        }

        const rowsHtml = items.map(p => {
            const best = getBestProductOffer(p) || { price: 0, store: 'Tienda' };
            return `
                <button type="button" class="instant-result-row" onclick="selectInstantSearchItem(${p.id})">
                    <div class="instant-result-thumb">
                        <img src="${getProductImage(p)}" alt="${escapeHtml(p.model)}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)">
                    </div>
                    <div class="instant-result-info">
                        <span class="instant-result-brand">${escapeHtml(p.brand)} · ${escapeHtml(p.category || 'bicicletas')}</span>
                        <span class="instant-result-model">${escapeHtml(p.model)}</span>
                    </div>
                    <div class="instant-result-price">
                        <strong>${formatCLP(best.price)}</strong>
                        <span>${(p.offers || []).length} tienda${(p.offers || []).length > 1 ? 's' : ''}</span>
                    </div>
                </button>
            `;
        }).join('');

        dropdown.innerHTML = `
            <div class="instant-search-section">
                <span class="instant-search-label">Resultados instantáneos (${data.total_count || items.length})</span>
                <div class="instant-results-list">
                    ${rowsHtml}
                </div>
                <button type="button" class="instant-view-all" onclick="applyInstantSearchTerm('${escapeHtml(q)}')">
                    Ver todos los resultados para "${escapeHtml(q)}" <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        `;
    } catch (_) {}
}

selectInstantSearchItem = window.selectInstantSearchItem = function(productId) {
    const dropdown = document.getElementById('search-instant-dropdown');
    if (dropdown) dropdown.classList.remove('active');
    openProductDetail(productId);
};

applyInstantSearchTerm = window.applyInstantSearchTerm = function(term) {
    const input = document.getElementById('main-search');
    const dropdown = document.getElementById('search-instant-dropdown');
    if (input) input.value = term;
    if (dropdown) dropdown.classList.remove('active');
    state.filters.search = (term || '').toLowerCase();
    state.currentPage = 1;
    render();
    const catalogEl = document.getElementById('catalog');
    if (catalogEl && typeof window.scrollTo === 'function') {
        window.scrollTo({ top: (catalogEl.offsetTop || 0) - 72, behavior: 'smooth' });
    }
};

function initInstantSearch() {
    const searchInput = document.getElementById('main-search');
    const dropdown = document.getElementById('search-instant-dropdown');
    if (!searchInput || !dropdown) return;

    if (typeof searchInput.addEventListener === 'function') {
        searchInput.addEventListener('focus', () => {
            dropdown.classList.add('active');
            updateInstantSearchPreview(searchInput.value);
        });
        searchInput.addEventListener('input', (e) => {
            dropdown.classList.add('active');
            clearTimeout(instantSearchTimer);
            instantSearchTimer = setTimeout(() => {
                updateInstantSearchPreview(e.target.value);
            }, 140);
        });
    }

    if (typeof document.addEventListener === 'function') {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                if (typeof searchInput.focus === 'function') searchInput.focus();
                dropdown.classList.add('active');
                updateInstantSearchPreview(searchInput.value);
            } else if (e.key === 'Escape') {
                dropdown.classList.remove('active');
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target && e.target.closest && !e.target.closest('#search-wrapper-box')) {
                dropdown.classList.remove('active');
            }
        });
    }
}


// Kickstart
init();
