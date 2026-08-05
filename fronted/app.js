// Lexical declarations for window functions to prevent ReferenceErrors
let setCategory, clearFilters, toggleCompare, clearCompare, openCompareModal, closeCompareModal, openProductDetail, openProductStore, openProductAction, closeModal, switchTab, activateExplorar, activateDeals, activateInternationalMode, openNovedadesModal, openProfileModal, openCountryModal, toggleMobileFilters, toggleFavorite, toggleFavoriteDetail, togglePriceAlert, toggleUserDropdown, openAuthModal, closeAuthModal, switchAuthTab, openAuthAlerts, handleAuthSubmit, handleLogout, renderAvatarHTML, selectSignupAvatar, changeAvatar, handleProductImageError, handleGoogleLogin, crearAlertaSupabase, toggleTheme, copyProductLink;

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

try {
    if (typeof firebase !== 'undefined' && FIREBASE_CONFIG.apiKey !== "YOUR_API_KEY") {
        firebase.initializeApp(FIREBASE_CONFIG);
        cloudDb = firebase.firestore();
        cloudAuth = firebase.auth();
        firebasePersistenceReady = cloudAuth.setPersistence(firebase.auth.Auth.Persistence.LOCAL).catch((error) => {
            console.warn("Firebase auth local persistence not enabled:", error);
        });
        cloudDb.enablePersistence?.({ synchronizeTabs: true }).catch((error) => {
            console.warn("Firestore offline persistence not enabled:", error);
        });
        useFirebase = true;
        console.log("Firebase initialized successfully in Cloud Mode!");
    } else {
        console.log("Firebase credentials not configured. Running in local Offline mode (localStorage enabled).");
    }
} catch (error) {
    console.warn("Failed to initialize Firebase:", error);
}

// =============================================
// CONFIGURACIÓN DE API
// =============================================
// Detecta automáticamente el entorno: en producción usa el mismo origen,
// en desarrollo local apunta al servidor FastAPI en el puerto 8000.
const API_BASE_URL = (typeof window.API_BASE_URL === 'string') ? window.API_BASE_URL : (() => {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        // Producción: backend corriendo en Render
        return 'https://bicitodo.onrender.com';
    }
    // Desarrollo local: FastAPI corriendo en puerto 8000
    return 'http://127.0.0.1:8000';
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
    <svg class="google-auth-logo" viewBox="0 0 48 48" aria-hidden="true">
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
        gridHtml += `<polygon points="${points}" fill="none" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1.2" />`;
    });
    
    let spokeHtml = '';
    angles.forEach((angle, i) => {
        const x = centerX + maxRadius * Math.cos(angle);
        const y = centerY + maxRadius * Math.sin(angle);
        spokeHtml += `<line x1="${centerX}" y1="${centerY}" x2="${x}" y2="${y}" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1.2" />`;
        
        const labelRadius = maxRadius + 18;
        const lx = centerX + labelRadius * Math.cos(angle);
        const ly = centerY + labelRadius * Math.sin(angle);
        
        let textAnchor = "middle";
        if (Math.cos(angle) > 0.1) textAnchor = "start";
        if (Math.cos(angle) < -0.1) textAnchor = "end";
        
        let dy = 4;
        if (i === 0) dy = -5;
        if (i === 2 || i === 3) dy = 10;
        
        spokeHtml += `<text x="${lx}" y="${ly + dy}" text-anchor="${textAnchor}" fill="var(--text-muted)" font-size="0.65rem" font-family="'Poppins', sans-serif;" font-weight="700" style="text-transform: uppercase; letter-spacing: 0.5px;">${dimensions[i]}</text>`;
    });
    
    const colors = [
        { stroke: "#22c55e", fill: "rgba(34, 197, 94, 0.15)", glow: "rgba(34, 197, 94, 0.4)" },
        { stroke: "#3b82f6", fill: "rgba(59, 130, 246, 0.15)", glow: "rgba(59, 130, 246, 0.4)" },
        { stroke: "#ec4899", fill: "rgba(236, 72, 153, 0.15)", glow: "rgba(236, 72, 153, 0.4)" }
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
            <polygon points="${points}" fill="${color.fill}" stroke="${color.stroke}" stroke-width="2.5" style="filter: drop-shadow(0 0 4px ${color.glow}); transition: all 0.3s;" />
        `;
        
        legendHtml += `
            <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; font-weight: 700; color: #fff;">
                <span style="width: 10px; height: 10px; border-radius: 50%; background: ${color.stroke}; box-shadow: 0 0 6px ${color.stroke};"></span>
                <span>${p.brand} ${p.model}</span>
            </div>
        `;
    });
    
    return `
        <div class="radar-chart-wrapper" style="display: flex; flex-direction: column; align-items: center; margin: 1.5rem auto 0.5rem; background: rgba(15,23,42,0.4); border: 1px solid rgba(255,255,255,0.06); padding: 1.25rem 2rem; border-radius: 16px; max-width: 480px; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
            <span style="font-family:'Poppins', sans-serif; font-size: 0.72rem; font-weight: 800; color: var(--primary); letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 0.75rem;"><i class="fa-solid fa-chart-pie" style="margin-right: 0.35rem;"></i> Comparación de Rendimiento RPG</span>
            <svg width="340" height="340" viewBox="0 0 340 340" style="margin-bottom: 0.5rem;">
                <g transform="translate(20, 20)">
                    ${gridHtml}
                    ${spokeHtml}
                    ${polygonsHtml}
                    <circle cx="${centerX}" cy="${centerY}" r="3" fill="#fff" opacity="0.5" />
                </g>
            </svg>
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.75rem; width: 100%;">
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
            document.body.classList.remove('cyber-theme');
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

function getProductFallbackImage() {
    return FALLBACK_PRODUCT_IMAGE;
}

function getProductImage(product = {}) {
    const offers = Array.isArray(product.offers) ? product.offers : [];
    const candidates = [
        product.image,
        product.original_img_url,
        ...offers.map(offer => offer && offer.imageUrl)
    ].filter(Boolean);

    const preferred = candidates.find(src => !isPlaceholderImage(src));
    return preferred || candidates[0] || getProductFallbackImage(product);
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
    if (cat === 'accesorios') return 'Accesorios y Equipamiento';
    if (cat === 'repuestos') return 'Componentes y Repuestos';
    return 'Catálogo de Bicicletas';
}

function getInternationalTitle(cat) {
    if (cat === 'repuestos') return 'AliExpress Componentes Internacionales';
    return 'AliExpress Accesorios Internacionales';
}

function syncCatalogUiState() {
    const titleEl = document.getElementById('section-title');
    if (titleEl) {
        titleEl.innerText = state.isInternationalMode ? getInternationalTitle(state.category) : getCategoryTitle(state.category);
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

// Theme Toggle System
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        const themeBtnIcon = document.querySelector('#theme-toggle i');
        if (themeBtnIcon) {
            themeBtnIcon.className = 'fa-solid fa-sun';
        }
    } else {
        document.body.classList.remove('light-mode');
        const themeBtnIcon = document.querySelector('#theme-toggle i');
        if (themeBtnIcon) {
            themeBtnIcon.className = 'fa-solid fa-moon';
        }
    }
}

toggleTheme = window.toggleTheme = function() {
    const isLight = document.body.classList.toggle('light-mode');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    const themeBtnIcon = document.querySelector('#theme-toggle i');
    if (themeBtnIcon) {
        themeBtnIcon.className = isLight ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        
        // Add rotation animation
        themeBtnIcon.style.transform = 'rotate(360deg) scale(1.2)';
        themeBtnIcon.style.transition = 'transform 0.4s ease';
        setTimeout(() => {
            themeBtnIcon.style.transform = '';
            themeBtnIcon.style.transition = '';
        }, 400);
    }
    showToast(`☀️ Modo ${isLight ? 'Claro' : 'Oscuro'} Activado`);
};

// =============================================
// CORE FUNCTIONS
// =============================================
function init() {
    initTheme();
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
        if (statBicis) statBicis.textContent = '0';
        if (statAcc) statAcc.textContent = '0';
        if (statRep) statRep.textContent = '0';
        if (statTiendas) statTiendas.textContent = '0';
    }
}

function renderBrandFilter() {
    const counts = state.brandsMetadata || {};
    const sortedBrands = Object.entries(counts)
        .filter(([brand, count]) => count > 0)
        .sort((a, b) => a[0].localeCompare(b[0]));
        
    const container = document.getElementById('brand-filter-list');
    if (!container) return;
    
    // Save scroll position of the brand list container
    const scrollTop = container.scrollTop;
    
    container.innerHTML = sortedBrands.map(([b, count]) => {
        const isChecked = state.filters.brands.includes(b.toLowerCase()) ? 'checked' : '';
        return `
            <label style="display: flex; justify-content: space-between; align-items: center;">
                <span><input type="checkbox" class="brand-check" value="${b.toLowerCase()}" ${isChecked}> ${b}</span>
                <span class="filter-count" style="font-size: 0.8rem; color: rgba(255,255,255,0.4); font-weight: 500;">(${count})</span>
            </label>
        `;
    }).join('');
    
    // Restore scroll position
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
        
        // Use server types metadata or fallback
        const counts = state.typesMetadata || { 'mtb': 0, 'ruta': 0, 'gravel': 0, 'fixie': 0, 'urbana': 0, 'hibrida': 0, 'infantil': 0, 'electrica': 0 };
        const typeContainer = document.getElementById('type-filter-list');
        if (typeContainer) {
            typeContainer.querySelectorAll('label').forEach(label => {
                const input = label.querySelector('input');
                if (input) {
                    const type = input.value;
                    const count = counts[type] || 0;
                    const isChecked = state.filters.types.includes(type) ? 'checked' : '';
                    
                    let iconHtml = '';
                    if (type === 'mtb') iconHtml = '<i class="fa-solid fa-mountain-sun" style="color:#22c55e;width:14px"></i>';
                    else if (type === 'ruta') iconHtml = '<i class="fa-solid fa-road" style="color:#3b82f6;width:14px"></i>';
                    else if (type === 'gravel') iconHtml = '<i class="fa-solid fa-compass" style="color:#0d9488;width:14px"></i>';
                    else if (type === 'fixie') iconHtml = '<i class="fa-solid fa-circle-dot" style="color:#0ea5e9;width:14px"></i>';
                    else if (type === 'urbana') iconHtml = '<i class="fa-solid fa-city" style="color:#eab308;width:14px"></i>';
                    else if (type === 'hibrida') iconHtml = '<i class="fa-solid fa-shuffle" style="color:#f97316;width:14px"></i>';
                    else if (type === 'infantil') iconHtml = '<i class="fa-solid fa-child" style="color:#ec4899;width:14px"></i>';
                    else if (type === 'electrica') iconHtml = '<i class="fa-solid fa-bolt" style="color:#8b5cf6;width:14px"></i>';
                    
                    const labelText = {
                        'mtb': 'Montaña (MTB)',
                        'ruta': 'Ruta (Road)',
                        'gravel': 'Gravel',
                        'fixie': 'Fixie / Single-speed',
                        'urbana': 'Urbana (City)',
                        'hibrida': 'Híbrida (Hybrid)',
                        'infantil': 'Infantil',
                        'electrica': 'Eléctrica'
                    }[type] || type.toUpperCase();

                    label.innerHTML = `<input type="checkbox" class="type-check" value="${type}" ${isChecked}> ${iconHtml} ${labelText} <span class="filter-count" style="margin-left: auto; font-size: 0.8rem; color: rgba(255,255,255,0.4); font-weight: 500;">(${count})</span>`;
                    label.style.display = count === 0 ? 'none' : 'flex';
                }
            });
            typeContainer.querySelectorAll('.type-check').forEach(input => {
                input.addEventListener('change', () => {
                    const checked = typeContainer.querySelectorAll('.type-check:checked');
                    state.filters.types = Array.from(checked).map(i => i.value);
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

    // Save scroll position of the dynamic type list
    const dynList = document.getElementById('dyn-type-filter-list');
    const dynScrollTop = dynList ? dynList.scrollTop : 0;

    const label = state.category === 'accesorios' ? 'Tipo de Accesorio' : 'Tipo de Componente';
    dynContainer.innerHTML = `
        <label>${label}</label>
        <div class="checkbox-list" id="dyn-type-filter-list">
            ${sortedTypes.map(([t, count]) => {
                const isChecked = state.filters.dynTypes.includes(t.toLowerCase()) ? 'checked' : '';
                return `
                    <label style="display: flex; justify-content: space-between; align-items: center;">
                        <span><input type="checkbox" class="dyn-type-check" value="${t.toLowerCase()}" ${isChecked}> ${t}</span>
                        <span class="filter-count" style="font-size: 0.8rem; color: rgba(255,255,255,0.4); font-weight: 500;">(${count})</span>
                    </label>
                `;
            }).join('')}
        </div>
    `;
    dynContainer.style.display = 'block';

    // Restore scroll position of the dynamic type list
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
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: preservedDiscountMin, aliexpressQuickFilter: 'all' };
    
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
    document.body.classList.remove('cyber-theme');
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: null, aliexpressQuickFilter: 'all' };
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
    event.stopPropagation();
    const idx = state.compare.indexOf(productId);
    if (idx > -1) {
        state.compare.splice(idx, 1);
    } else {
        if (state.compare.length >= 3) {
            showToast('Solo puedes comparar hasta 3 bicicletas a la vez.');
            return;
        }
        state.compare.push(productId);
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
        countEl.textContent = state.compare.length;
    } else {
        bar.classList.remove('visible');
    }
}

clearCompare = window.clearCompare = function() {
    state.compare = [];
    updateCompareBar();
    render(false);
};

openCompareModal = window.openCompareModal = function() {
    const allProducts = [...state.data.bicicletas, ...state.data.accesorios, ...state.data.repuestos];
    const products = state.compare.map(id => allProducts.find(p => p.id === id)).filter(Boolean);
    if (products.length < 2) { showToast('Selecciona al menos 2 productos para comparar.'); return; }

    // Build all unique spec keys
    const allKeys = [...new Set(products.flatMap(p => Object.keys(p.fullSpecs || {})))];

    // Highlight evaluation helpers
    const parsedWeights = products.map(p => {
        const wStr = String(p.fullSpecs?.["Peso Aproximado"] || p.fullSpecs?.["Peso"] || '');
        const m = wStr.match(/(\d+(?:\.\d+)?)/);
        return m ? parseFloat(m[1]) : Infinity;
    });
    const minWeight = Math.min(...parsedWeights);

    const parsedPrices = products.map(p => Math.min(...p.offers.map(o => o.price)));
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
        const bestPrice = Math.min(...p.offers.map(o => o.price));
        const isCheapest = bestPrice === minPrice && products.length > 1 && products.some(p2 => Math.min(...p2.offers.map(o => o.price)) > minPrice);
        const valScore = calculateValueScore(p);
        
        const priceStyle = isCheapest 
            ? `style="background: rgba(34, 197, 94, 0.15); border: 1.5px solid var(--primary); border-radius: 8px; padding: 0.25rem 0.5rem; color: #4ade80; font-weight: 800; display: inline-block; box-shadow: 0 0 10px rgba(34,197,94,0.25);"` 
            : `style="font-weight: 800;"`;
            
        return `
            <div class="compare-col" style="position: relative;">
                ${isCheapest ? `<span style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: var(--primary); color: #000; font-size: 0.65rem; font-weight: 900; padding: 0.15rem 0.5rem; border-radius: 99px; text-transform: uppercase; white-space: nowrap; letter-spacing: 0.5px; box-shadow: 0 2px 8px var(--primary-glow);">Mejor Precio</span>` : ''}
                <div class="compare-img-wrap" style="border: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.2); border-radius: 12px; padding: 0.5rem;"><img src="${getProductImage(p)}" alt="${p.model}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)" style="object-fit: contain;"></div>
                <div class="compare-brand" style="margin-top: 0.75rem;">${p.brand}</div>
                <div class="compare-model">${p.model}</div>
                ${valScore ? `
                    <div style="margin: 0.35rem 0; display: flex; align-items: center; justify-content: center; gap: 0.35rem;">
                        <span style="font-size: 0.68rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">Calidad-Precio:</span>
                        <span style="background: rgba(34,197,94,0.12); color: #4ade80; font-weight: 800; font-size: 0.75rem; padding: 0.1rem 0.4rem; border-radius: 4px;">${valScore}/100</span>
                    </div>
                ` : ''}
                <div class="compare-best-price" style="margin: 0.5rem 0;">Desde <span ${priceStyle}>${formatCLP(bestPrice)}</span></div>
                <a href="${getProductUrl(p.offers[0])}" target="_blank" rel="noopener" class="btn-compare-buy">Ver en tienda <i class="fa-solid fa-arrow-up-right-from-square"></i></a>
            </div>
        `;
    }).join('');

    const rowsHtml = allKeys.map(key => {
        const cells = products.map((p, idx) => {
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
            
            const cellStyle = isSuperior 
                ? `style="background: rgba(34, 197, 94, 0.12); color: #4ade80; border-left: 3px solid var(--primary); font-weight: 600;"` 
                : '';
            const checkIcon = isSuperior ? `<i class="fa-solid fa-circle-check" style="color: var(--primary); margin-right: 0.4rem; font-size: 0.8rem;"></i> ` : '';
            
            return `<td ${cellStyle}>${checkIcon}${val}</td>`;
        }).join('');
        
        return `<tr><th>${key}</th>${cells}</tr>`;
    }).join('');

    const radarChartHtml = renderRadarChart(products);

    document.getElementById('compare-modal-overlay').innerHTML = `
        <div class="compare-modal-content" style="max-width: 1050px;">
            <button class="modal-close" onclick="closeCompareModal()"><i class="fa-solid fa-xmark"></i></button>
            <h2 class="compare-title" style="margin-bottom: 1.5rem;"><i class="fa-solid fa-scale-balanced"></i> Comparación de Productos</h2>
            <div class="compare-cols">${colsHtml}</div>
            ${radarChartHtml}
            <div class="compare-table-wrap" style="margin-top: 1.5rem;">
                <table class="compare-table">
                    <thead><tr><th>Especificación</th>${products.map(p => `<th>${p.brand} ${p.model}</th>`).join('')}</tr></thead>
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
                if (!target.hostname.toLowerCase().includes('aliexpress.') || !target.pathname.includes('/item/')) return '#';
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
    return allProducts.find(p => p.id === productId);
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
    const url = getProductUrl(offer || {});
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
                    <span style="font-size:0.8rem; color:#fff; font-weight:700;">Avisarme si baja de:</span>
                    <input type="number" id="alert-price-input" value="${currentAlertVal}" step="1000" style="font-family:'Poppins',sans-serif; font-weight:800; text-align:center; width:120px; background:rgba(0,0,0,0.25); border:1px solid var(--glass-border); border-radius:6px; color:#fff; padding:0.35rem 0.5rem; outline:none;">
                    <button type="button" id="btn-alerta" class="btn-price-alert ${hasAlert ? 'active' : ''}" onclick="crearAlertaSupabase(${productId})">
                        ${hasAlert ? 'Desactivar Alerta' : 'Activar Alerta'}
                    </button>
                </div>
            </div>
        `;
    } else {
        alertHtml = `
            <div class="price-alert-panel" style="border-color: rgba(255,255,255,0.06); background: rgba(255,255,255,0.01);">
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
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.25); padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); min-width: 80px;">
                <span style="font-family: 'Poppins', sans-serif; font-weight: 900; font-size: 1.5rem; color: #fff; line-height: 1.1;">${valScore}</span>
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
                    <button type="button" class="modal-share-link" onclick="copyProductLink(${product.id})">
                        <i class="fa-solid fa-link"></i> Copiar enlace
                    </button>
                    <div class="modal-best-price-hero">
                        <span class="label">Desde</span>
                        <span class="amount">${formatCLP(bestOffer.price)}</span>
                        <span class="stores-count">en ${product.offers.length} tienda${product.offers.length > 1 ? 's' : ''}</span>
                    </div>
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
                                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 0.45rem 0.75rem; border-radius: 8px; font-size: 0.75rem; min-width: 100px; flex: 1; text-align: left;">
                                            <span style="display: block; font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">${key}</span>
                                            <span style="font-weight: 700; color: #fff; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; display: block;">${val}</span>
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
    document.body.classList.remove('cyber-theme');
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
    document.body.classList.remove('cyber-theme');
    
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
    document.body.classList.add('cyber-theme');
    
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
    document.body.classList.remove('cyber-theme');
    
    // Activate international mode
    state.isInternationalMode = true;
    
    // AliExpress has accessories and parts. If current category is bicycles, switch to accesorios
    if (state.category === 'bicicletas') {
        state.category = 'accesorios';
    }
    
    // Reset filters
    state.filters = { search: '', priceMin: null, priceMax: null, stores: [], types: [], wheelSizes: [], brands: [], budgetRange: null, dynTypes: [], discountMin: null, aliexpressQuickFilter: 'all' };
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
        <!-- Article 1 -->
        <div style="background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; text-align: left;">
            <span style="font-size: 0.65rem; font-weight: 800; color: #60a5fa; background: rgba(59, 130, 246, 0.1); padding: 0.2rem 0.5rem; border-radius: 4px; width: fit-content; text-transform: uppercase;">Tendencias</span>
            <h4 style="font-family:'Poppins', sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; line-height: 1.3; color: var(--text-white);">Gravel en Chile: La aventura de invierno</h4>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.4;">
                El gravel sigue creciendo exponencialmente. Conoce las mejores bicicletas de aventura y cómo equipar tu transmisión para terrenos de barro y ripio este invierno.
            </p>
        </div>
        
        <!-- Article 2 -->
        <div style="background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; text-align: left;">
            <span style="font-size: 0.65rem; font-weight: 800; color: var(--primary); background: rgba(34, 197, 94, 0.1); padding: 0.2rem 0.5rem; border-radius: 4px; width: fit-content; text-transform: uppercase;">Consejos</span>
            <h4 style="font-family:'Poppins', sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; line-height: 1.3; color: var(--text-white);">Mantenimiento de cadena contra la humedad</h4>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.4;">
                La humedad y la salinidad desgastan los eslabones rápidamente. Te dejamos un tutorial simple para limpiar, secar y lubricar con cera húmeda después de pedalear bajo la lluvia.
            </p>
        </div>
        
        <!-- Article 3 -->
        <div style="background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; text-align: left;">
            <span style="font-size: 0.65rem; font-weight: 800; color: var(--warning); background: rgba(245, 158, 11, 0.1); padding: 0.2rem 0.5rem; border-radius: 4px; width: fit-content; text-transform: uppercase;">Rutas</span>
            <h4 style="font-family:'Poppins', sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; line-height: 1.3; color: var(--text-white);">Ascenso a Farellones: Preparación segura</h4>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.4;">
                Subir a la cordillera es el sueño de todo ciclista de ruta. Te recomendamos verificar el estado de tus frenos, llevar luces traseras de alta potencia y ropa térmica de alta visibilidad.
            </p>
        </div>
    `;

    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
        <div style="padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; background: var(--nav-bg); backdrop-filter: blur(20px); border-radius: var(--radius-lg); max-width: 800px; margin: 0 auto; color: var(--text-white);">
            
            <!-- Header -->
            <div style="text-align: center; display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                <div style="font-size: 2.5rem; color: var(--primary);"><i class="fa-solid fa-envelope-open-text" style="filter: drop-shadow(0 0 10px var(--primary-glow));"></i></div>
                <h2 style="font-family:'Poppins', sans-serif; font-weight:800; font-size:1.8rem; margin: 0; color: var(--text-white);">Novedades del Pedal</h2>
                <p style="color: var(--text-muted); max-width: 550px; font-size: 0.9rem; line-height: 1.4; margin: 0;">
                    Mantente al día con las últimas noticias del ciclismo en Chile, consejos de mantenimiento para tu bicicleta y ofertas exclusivas de nuestra comunidad.
                </p>
            </div>
            
            <!-- Newsletter Sign-Up -->
            <div style="background: var(--card-bg); border: 1px solid var(--glass-border); padding: 1.5rem; border-radius: 16px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 0.75rem;">
                <span style="font-size: 0.75rem; font-weight: 800; color: var(--primary); letter-spacing: 1px; text-transform: uppercase;">BOLETÍN PARA AMANTES DEL CICLISMO</span>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0; max-width: 480px;">Recibe consejos mecánicos, recomendaciones de rutas y avisos de descuentos antes que nadie.</p>
                
                <form id="newsletter-form" onsubmit="submitNewsletter(event)" style="display: flex; gap: 0.5rem; width: 100%; max-width: 480px; margin-top: 0.25rem;">
                    <input type="email" id="newsletter-email" placeholder="tu-correo@ciclismo.cl" style="flex: 1; padding: 0.65rem 1rem; border-radius: 99px; background: var(--input-bg); border: 1px solid var(--glass-border); color: var(--text-white); outline: none; font-size: 0.85rem; transition: var(--transition);" required>
                    <button type="submit" style="background: var(--primary); color: #020617; font-weight: 800; border: none; padding: 0.65rem 1.5rem; border-radius: 99px; font-size: 0.85rem; cursor: pointer; transition: var(--transition); box-shadow: 0 4px 12px var(--primary-glow); display: flex; align-items: center; gap: 0.35rem;">
                        Suscribirse <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </form>
            </div>
            
            <!-- News Section -->
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <h3 style="font-family:'Poppins', sans-serif; font-size: 1.1rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 0.5rem; color: var(--text-white);">
                    <i class="fa-solid fa-newspaper" style="color: var(--accent);"></i> Artículos y Noticias Recientes
                </h3>
                
                <div id="news-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
                    <div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">
                        <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 1.5rem; color: var(--primary); margin-bottom: 0.5rem;"></i>
                        <p style="margin: 0; font-size: 0.85rem;">Cargando últimas noticias desde el pedal...</p>
                    </div>
                </div>
            </div>
            
            <!-- Footer action -->
            <button onclick="closeModal()" style="align-self: center; background: var(--primary); color: #020617; font-weight: 800; border: none; padding: 0.65rem 2rem; border-radius: 99px; font-size: 0.85rem; cursor: pointer; transition: var(--transition); box-shadow: 0 4px 12px var(--primary-glow);">
                Cerrar Novedades
            </button>
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
            const categoryColors = {
                'MTB': '#22c55e',       // green
                'Ruta': '#3b82f6',      // blue
                'Entrevistas': '#ec4899', // pink
                'Artículos': '#8b5cf6',  // purple
                'Consejos': '#f59e0b',   // yellow
                'Noticias': '#60a5fa'   // light blue
            };
            
            const categoryBgColors = {
                'MTB': 'rgba(34, 197, 94, 0.1)',
                'Ruta': 'rgba(59, 130, 246, 0.1)',
                'Entrevistas': 'rgba(236, 72, 153, 0.1)',
                'Artículos': 'rgba(139, 92, 246, 0.1)',
                'Consejos': 'rgba(245, 158, 11, 0.1)',
                'Noticias': 'rgba(96, 165, 250, 0.1)'
            };

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
                const color = categoryColors[cat] || '#60a5fa';
                const bg = categoryBgColors[cat] || 'rgba(96, 165, 250, 0.1)';
                const icon = categoryIcons[cat] || 'fa-newspaper';

                return `
                    <div style="background: var(--card-bg); border: 1px solid var(--glass-border); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; text-align: left; transition: var(--transition); cursor: pointer;" 
                         onmouseenter="this.style.borderColor='${color}'; this.style.transform='translateY(-2px)';" 
                         onmouseleave="this.style.borderColor='var(--glass-border)'; this.style.transform='none';"
                         onclick="window.open('${article.url}', '_blank', 'noopener,noreferrer')">
                        <span style="font-size: 0.65rem; font-weight: 800; color: ${color}; background: ${bg}; padding: 0.2rem 0.5rem; border-radius: 4px; width: fit-content; text-transform: uppercase; display: flex; align-items: center; gap: 0.3rem;">
                            <i class="fa-solid ${icon}"></i> ${cat}
                        </span>
                        <h4 style="font-family:'Poppins', sans-serif; font-size: 0.9rem; font-weight: 700; margin: 0; line-height: 1.35; color: var(--text-white);">${article.title}</h4>
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; line-height: 1.45;">
                            ${article.summary}
                        </p>
                        <span style="font-size: 0.68rem; color: var(--primary); font-weight: 700; margin-top: auto; display: flex; align-items: center; gap: 0.25rem; justify-content: flex-end;">
                            Leer más <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </span>
                    </div>
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
    
    // Simulate successful subscription and update the HTML view
    const form = document.getElementById('newsletter-form');
    if (form) {
        form.parentElement.innerHTML = `
            <span style="font-size: 0.75rem; font-weight: 800; color: var(--primary); letter-spacing: 1px; text-transform: uppercase;">SUSCRIPCIÓN EXITOSA</span>
            <div style="font-size: 2rem; color: var(--primary); margin: 0.25rem 0;"><i class="fa-solid fa-circle-check"></i></div>
            <p style="font-size: 0.9rem; color: var(--text-white); font-weight: 700; margin: 0;">¡Ya estás registrado, ciclista!</p>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0; text-align: center;">Pronto recibirás nuestras novedades directo en tu bandeja de entrada.</p>
        `;
    }
    showToast('🚲 ¡Te has suscrito con éxito al boletín!');
};

openProfileModal = window.openProfileModal = function(event) {
    if (event) event.preventDefault();
    
    // Update active link
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const navC = document.getElementById('nav-cuenta');
    if (navC) navC.classList.add('active');
    
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;
    
    const allProducts = [...state.data.bicicletas, ...state.data.accesorios, ...state.data.repuestos];
    const userFavs = state.favorites.map(f => {
        const p = allProducts.find(item => item.id === f.id);
        if (p) {
            return { ...p, alertPrice: f.alertPrice };
        }
        return null;
    }).filter(Boolean);
    
    const favsHtml = userFavs.length > 0 ? userFavs.map(p => {
        const bestOffer = [...p.offers].sort((a, b) => a.price - b.price)[0];
        const alertText = p.alertPrice ? `<span style="font-size:0.72rem; color:var(--primary); font-weight:700;"><i class="fa-solid fa-bell"></i> Alerta: ${formatCLP(p.alertPrice)}</span>` : '<span style="font-size:0.72rem; color:var(--text-dim); font-weight:600;"><i class="fa-solid fa-bell-slash"></i> Sin Alerta</span>';
        
        return `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.85rem; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; width: 100%; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 50px; height: 38px; background: #fff; border-radius: 6px; display: flex; align-items: center; justify-content: center; padding: 0.2rem;">
                    <img src="${getProductImage(p)}" alt="${p.model}" data-fallbacks="${getImageFallbacks(p).join('|')}" onerror="handleProductImageError(this)" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                </div>
                <div style="text-align: left;">
                    <span style="font-size: 0.68rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; display: block;">${p.brand}</span>
                    <span style="font-size: 0.85rem; font-weight: 700; color: #fff; line-height: 1.2; display:block;">${p.model}</span>
                    ${alertText}
                </div>
            </div>
            <div style="display:flex; gap:0.4rem; align-items:center;">
                <button onclick="closeModal(); openProductDetail(${p.id});" style="background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3); color: #60a5fa; font-size: 0.72rem; font-weight: 700; padding: 0.35rem 0.75rem; border-radius: 8px; cursor: pointer; transition: var(--transition); white-space:nowrap;">
                    Configurar Alerta
                </button>
                <button onclick="toggleFavorite(${p.id}); openProfileModal(event);" style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #f87171; font-size: 0.75rem; font-weight: 700; padding: 0.35rem 0.6rem; border-radius: 8px; cursor: pointer; transition: var(--transition);" title="Eliminar">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>
        </div>
        `;
    }).join('') : '<p style="font-size:0.85rem; color:var(--text-dim); text-align:center; width:100%; margin:1.5rem 0;">Aún no tienes productos agregados a favoritos.</p>';
    
    const displayName = state.user ? state.user.displayName : 'Invitado';
    const email = state.user ? state.user.email : 'Sin registrar';
    const avatar = state.user ? state.user.avatar : 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y';
    
    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
        <div style="padding: 2rem 2.5rem; text-align: center; display: flex; flex-direction: column; gap: 1.25rem; align-items: center; background: rgba(15,23,42,0.95); backdrop-filter: blur(20px);">
            ${renderAvatarHTML(avatar, '80px', '3px')}
            <div>
                <h2 style="font-family:'Poppins', sans-serif; font-weight:800; font-size:1.4rem; color:#fff; margin-bottom:0.15rem;">${displayName}</h2>
                <span style="font-size: 0.72rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.8px;">${email}</span>
            </div>
            
            <!-- Animal Avatar Selector Grid (Amigable y Lúdico) -->
            <div style="width: 100%; max-width: 500px; text-align: left; background: rgba(0,0,0,0.25); padding: 1rem 1.25rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
                <h4 style="font-family:'Poppins', sans-serif; font-size: 0.82rem; font-weight: 700; color: #fff; margin-bottom: 0.65rem; display:flex; align-items:center; gap:0.4rem; text-transform:uppercase; letter-spacing:0.5px;"><i class="fa-solid fa-face-smile" style="color:var(--primary);"></i> ¡Elige tu animalito de perfil!</h4>
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.6rem; justify-items: center;">
                    ${Object.keys(EMOJI_GRADIENTS).map(emoji => {
                        const isActive = avatar === emoji;
                        const borderStyle = isActive ? '2.5px solid var(--primary)' : '2.5px solid transparent';
                        const scaleStyle = isActive ? 'scale(1.15)' : 'scale(1)';
                        const shadowStyle = isActive ? '0 0 10px var(--primary-glow)' : 'none';
                        return `
                            <button onclick="changeAvatar('${emoji}')" style="background: ${EMOJI_GRADIENTS[emoji]}; width: 42px; height: 42px; border-radius: 50%; border: ${borderStyle}; cursor: pointer; transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; box-shadow: ${shadowStyle}; transform: ${scaleStyle}; padding:0; outline:none;" class="avatar-select-pill ${isActive ? 'active-avatar' : ''}" title="Elegir ${emoji}" onmouseenter="this.style.transform='scale(1.25)'" onmouseleave="this.style.transform='${scaleStyle}'">
                                ${emoji}
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>
            
            <div style="width: 100%; max-width: 500px; text-align: left; background: rgba(15,23,42,0.5); padding: 1.25rem 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.04); max-height:280px; overflow-y:auto; display:flex; flex-direction:column; gap:0.75rem;">
                <h4 style="font-family:'Poppins', sans-serif; font-size: 0.88rem; font-weight: 700; color: #fff; margin-bottom: 0.4rem; display:flex; align-items:center; gap:0.4rem;"><i class="fa-solid fa-heart" style="color:#ef4444;"></i> Tus Favoritos y Alertas:</h4>
                <div style="display: flex; flex-direction: column; gap: 0.65rem; width:100%;">
                    ${favsHtml}
                </div>
            </div>
            
            <div style="width: 100%; max-width: 500px; text-align: left; background: rgba(15,23,42,0.5); padding: 1.25rem 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.04);">
                <h4 style="font-family:'Poppins', sans-serif; font-size: 0.88rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;"><i class="fa-solid fa-bell" style="color:var(--warning); margin-right: 0.4rem;"></i> Alertas de Precios Activas:</h4>
                <p style="font-size: 0.78rem; color: var(--text-dim); line-height: 1.4; margin: 0;">
                    Recibirás un correo electrónico inmediato en cuanto cualquiera de tus productos favoritos caiga por debajo de tu valor objetivo.
                </p>
            </div>
            
            <button onclick="closeModal()" style="background: var(--primary); color: #000; font-weight: 800; border: none; padding: 0.7rem 1.8rem; border-radius: 99px; font-size: 0.85rem; cursor: pointer; transition: var(--transition); box-shadow: 0 4px 12px rgba(34, 197, 94, 0.25);">
                Cerrar
            </button>
        </div>
    `;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

openCountryModal = window.openCountryModal = function() {
    const modal = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    if (!modal || !content) return;
    
    content.innerHTML = `
        <button class="modal-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></button>
        <div style="padding: 2.5rem; text-align: center; display: flex; flex-direction: column; gap: 1.5rem; align-items: center; background: rgba(15,23,42,0.9); backdrop-filter: blur(20px);">
            <div style="font-size: 3.5rem; color: var(--primary);"><i class="fa-solid fa-location-dot" style="filter: drop-shadow(0 0 12px var(--primary-glow));"></i></div>
            <div>
                <h2 style="font-family:'Poppins', sans-serif; font-weight:800; font-size:1.4rem; color:#fff; margin-bottom:0.15rem;">Región: Chile 🇨🇱</h2>
                <span style="font-size: 0.72rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.8px;">Mercado Activo Completo</span>
            </div>
            
            <p style="color:var(--text-muted); max-width: 500px; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                Estás buscando en el mercado chileno. Comparamos los catálogos en tiempo real de las tiendas integradas para darte el mejor precio de ciclismo del país.
            </p>
            
            <div style="width: 100%; max-width: 500px; text-align: left; background: rgba(15,23,42,0.5); padding: 1.25rem 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.04);">
                <h4 style="font-family:'Poppins', sans-serif; font-size: 0.88rem; font-weight: 700; color: #fff; margin-bottom: 0.75rem;"><i class="fa-solid fa-store" style="color:var(--primary); margin-right: 0.4rem;"></i> Tiendas Integradas:</h4>
                <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.7; margin: 0;">
                    AliExpress • Copenhague • CrossMountain • Decathlon • DS Bikes • Falabella • Faucon Bikes • Full Bike • iBikes • Oxford Store • Paris • Ripley • Sátiro Bikes • Totem Chile • Sparta • Specialized Chile • Vidaurre Bikes.
                </p>
            </div>
            
            <button onclick="closeModal()" style="background: var(--primary); color: #020617; font-weight: 800; border: none; padding: 0.7rem 1.8rem; border-radius: 99px; font-size: 0.85rem; cursor: pointer; transition: var(--transition); box-shadow: 0 4px 12px var(--primary-glow);">
                Aceptar
            </button>
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
            console.error("API error, fallback to cache:", error);
        }
    }
    
    grid.innerHTML = '';
    document.getElementById('results-count').innerText = `${totalCount} modelos encontrados`;
    
    // Pagination controls
    document.querySelector('.page-info').textContent = `Página ${state.currentPage} de ${totalPages}`;
    document.querySelector('.btn-page.prev').disabled = state.currentPage <= 1;
        document.querySelector('.btn-page.next').disabled = state.currentPage >= totalPages;
        
        if (pageItems.length === 0) {
            // Check other categories
            let suggestions = [];
            const query = state.filters.search ? state.filters.search.toLowerCase() : '';
            if (query) {
                const categories = {
                    'bicicletas': 'Bicicletas',
                    'accesorios': 'Accesorios y Equipamiento',
                    'repuestos': 'Componentes y Repuestos'
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
                    <div style="margin-top: 1.5rem; padding: 1.25rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; display: inline-block;">
                        <p style="margin: 0 0 0.75rem 0; color: #fff; font-size: 0.95rem; font-weight: 600;">Encontramos resultados en otras categorías:</p>
                        <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
                            ${suggestions.map(s => `
                                <button onclick="setCategory('${s.cat}'); document.getElementById('main-search').value='${state.filters.search}'; state.filters.search='${state.filters.search}'; render();" 
                                        style="background: var(--primary); color: #000; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: transform 0.2s;">
                                    <i class="${s.cat === 'bicicletas' ? 'fa-solid fa-bicycle' : (s.cat === 'accesorios' ? 'fa-solid fa-helmet-safety' : 'fa-solid fa-gear')}"></i>
                                    Ver ${s.count} en ${s.catName}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
                    <i class="fa-solid fa-circle-xmark" style="font-size: 3rem; margin-bottom: 1rem; display: block;"></i>
                    <h3>Sin resultados</h3>
                    <p>Intenta con otros filtros o términos de búsqueda.</p>
                    <button onclick="clearFilters()" style="margin-top:1rem; background:var(--primary); color:#000; border:none; padding:0.65rem 1.5rem; border-radius:8px; font-weight:700; cursor:pointer;">Limpiar filtros</button>
                    <br>
                    ${suggestionHtml}
                </div>
            `;
            return;
        }

        // Helper colors for store dots
        const STORE_COLORS = {
            falabella: '#e73c3c',
            ripley: '#6b2fa0',
            paris: '#003da5',
            lider: '#00853e',
            decathlon: '#003DB6',
            trek: '#f05500',
            specialized: '#e81c15',
            oxford: '#1a56db',
            sparta: '#ff6900',
            faucon: '#0ea5e9',
            satiro: '#6d28d9',
            totem: '#059669',
            bikeplus: '#0891b2',
            bikeshop: '#9333ea',
            copenhague: '#14b8a6',
            dsbikes: '#06b6d4',
            crossmountain: '#16a34a',
            fullbike: '#dc2626',
            vidaurre: '#7c3aed',
            ibikes: '#f58220',
            aliexpress: '#ff4747'
        };

        const fragment = document.createDocumentFragment();

        pageItems.forEach((product, index) => {
            const bestOffer = [...product.offers].sort((a, b) => a.price - b.price)[0];
            const discount = bestOffer.oldPrice ? Math.round((1 - bestOffer.price / bestOffer.oldPrice) * 100) : 0;
            const isComparing = state.compare.includes(product.id);
            
            const frameMaterial = product.frameType || 'Aluminio';
            let transmission = 'Shimano';
            const specText = getProductSpecText(product);
            if (specText.includes('sram')) transmission = 'SRAM';
            else if (specText.includes('microshift')) transmission = 'MicroShift';
            else if (specText.includes('l-twoo')) transmission = 'L-Twoo';
            
            const wheelSize = product.wheelSize ? `Aro ${product.wheelSize}` : 'Adulto';
            
            let specsBadgesHtml = '';
            if (product.category === 'bicicletas') {
                specsBadgesHtml = `
                    <span class="spec-badge">${transmission}</span>
                    <span class="spec-badge">${frameMaterial}</span>
                    <span class="spec-badge">${wheelSize}</span>
                `;
            } else if (product.type) {
                const typeLabel = product.type.split(' ')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                specsBadgesHtml = `<span class="spec-badge" style="background: rgba(96, 165, 250, 0.08); color: #60a5fa; border-color: rgba(96, 165, 250, 0.15); font-weight: 700;">${typeLabel}</span>`;
            }
            const rating = product.rating ? product.rating.toFixed(1) : (4.3 + ((product.id * 7) % 7) * 0.1).toFixed(1);
            const reviews = product.review_count || (12 + ((product.id * 13) % 45));
            
            const isIntlProduct = isInternationalProduct(product);
            const card = document.createElement('div');
            card.className = `product-card elite${isComparing ? ' comparing' : ''}${isIntlProduct ? ' international' : ''}`;
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            card.setAttribute('aria-label', `Ver detalles de ${product.brand} ${product.model}`);
            const cardFallback = getProductFallbackImage(product);
            const isFavorite = state.favorites.some(f => f.id === product.id);
            const favIcon = isFavorite ? 'fa-solid fa-heart' : 'fa-regular fa-heart';
            const productSharePath = getProductSharePath(product);
            
            // Store dots with store favicon badge.
            const storeDotsHtml = product.offers.map(offer => {
                const color = STORE_COLORS[offer.storeKey] || '#64748b';
                const domain = STORE_DOMAINS[offer.storeKey] || 'copenhague.cl';
                const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
                return `
                    <span class="store-dot-mini" style="background: #ffffff; border: 1.5px solid ${color}; display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; padding: 0;" title="${escapeHtml(offer.store || offer.storeKey || 'Tienda')}">
                        <img src="${faviconUrl}" alt="${escapeHtml(offer.store || 'Tienda')}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';" style="width: 12px; height: 12px; object-fit: contain;">
                        <i class="fa-solid fa-store" style="font-size: 0.6rem; color: ${color}; display: none;"></i>
                    </span>
                `;
            }).join('');
            
            // Multi-store comparison badge
            const multiStoreBadge = product.offers.length > 1 
                ? `<div class="card-stores-badge"><i class="fa-solid fa-store"></i> Comparar en ${product.offers.length} tiendas</div>` 
                : '';
                
            const cyberBadgeHtml = (isCyberMode && discount >= 20)
                ? `<div class="cyber-flash-badge" style="position: absolute; top: 12px; left: 12px; background: #ec4899; color: #fff; font-size: 0.65rem; font-weight: 900; padding: 0.25rem 0.6rem; border-radius: 99px; text-transform: uppercase; z-index: 10; box-shadow: 0 0 10px rgba(236,72,153,0.6); animation: pulse 1.5s infinite;"><i class="fa-solid fa-bolt"></i> Cyber Days</div>`
                : '';
                
            const intlBadgeHtml = isIntlProduct 
                ? `<div class="intl-flash-badge"><i class="fa-solid fa-plane-up"></i> AliExpress</div>`
                : '';
            const actionLabel = isIntlProduct
                ? 'AliExpress <i class="fa-solid fa-arrow-up-right-from-square"></i>'
                : 'Ver';
                
            const shippingBadge = isIntlProduct 
                ? `<span class="spec-badge" style="background: rgba(251,146,60,0.12); color: #fb923c; border-color: rgba(251,146,60,0.25); font-weight: 700;"><i class="fa-solid fa-truck-fast"></i> Envío Gratis</span>`
                : '';

            const formatSales = (count) => {
                if (!count) return '';
                if (count >= 1000) {
                    return `+${(count / 1000).toFixed(1).replace('.0', '')}k`;
                }
                return `+${count}`;
            };

            card.innerHTML = `
                <div class="product-img">
                    ${cyberBadgeHtml}
                    ${intlBadgeHtml}
                    ${discount > 0 && !isCyberMode ? `<div class="card-discount-badge">-${discount}%</div>` : ''}
                    <img src="${getProductImage(product)}" alt="${product.model}"
                         data-fallbacks="${getImageFallbacks(product).join('|')}"
                         onerror="handleProductImageError(this, '${cardFallback}')"
                         loading="${index < (lowPowerDevice ? 1 : 2) ? 'eager' : 'lazy'}"
                         decoding="async"
                         fetchpriority="${index < (lowPowerDevice ? 1 : 2) ? 'high' : 'low'}"
                         draggable="false"
                         style="object-fit: contain;">
                    <button class="btn-compare-toggle ${isComparing ? 'active' : ''}" onclick="toggleCompare(${product.id}, event)" title="${isComparing ? 'Quitar del comparador' : 'Agregar al comparador'}">
                        <i class="fa-solid ${isComparing ? 'fa-check' : 'fa-scale-balanced'}"></i>
                    </button>
                    <button class="btn-fav" onclick="toggleFavorite(${product.id}, event)" title="${isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos'}">
                        <i class="${favIcon}"></i>
                    </button>
                </div>
                <div class="product-info">
                    <div class="prod-brand-row">
                        <h3 class="prod-title">
                            <a class="prod-title-link" href="${productSharePath}" onclick="event.preventDefault(); openProductDetail(${product.id});">${product.brand} ${product.model}</a>
                        </h3>
                    </div>
                    <div class="prod-specs-row">
                        ${specsBadgesHtml}
                        ${shippingBadge}
                    </div>
                    ${(function() {
                        let specsListHtml = '';
                        if (product.fullSpecs && Object.keys(product.fullSpecs).length > 0) {
                            const keySpecs = ['Cuadro', 'Frenos', 'Transmisión', 'Material', 'Capacidad', 'Medida', 'Uso', 'Tipo'];
                            const foundSpecs = [];
                            for (const key of keySpecs) {
                                const actualKey = Object.keys(product.fullSpecs).find(k => k.toLowerCase() === key.toLowerCase());
                                if (actualKey && product.fullSpecs[actualKey]) {
                                    let val = product.fullSpecs[actualKey];
                                    if (val.length > 32) val = val.substring(0, 29) + '...';
                                    foundSpecs.push(`<strong>${key}:</strong> ${val}`);
                                }
                                if (foundSpecs.length >= 2) break;
                            }
                            if (foundSpecs.length > 0) {
                                specsListHtml = `
                                    <div class="card-specs-list" style="font-size: 0.72rem; color: var(--text-muted); margin: 0.35rem 0; line-height: 1.35; display: flex; flex-direction: column; gap: 0.15rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.35rem;">
                                        ${foundSpecs.map(s => `<div style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${s}</div>`).join('')}
                                    </div>
                                `;
                            }
                        }
                        return specsListHtml;
                    })()}
                    
                    ${(function() {
                        const valScore = calculateValueScore(product);
                        return valScore ? `
                            <div class="value-score-wrapper" style="margin-top: 0.5rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; width: 100%;">
                                <span style="font-size: 0.65rem; font-weight: 800; color: var(--primary); text-transform: uppercase; white-space: nowrap;">Calidad-Precio</span>
                                <div style="flex-grow: 1; height: 5px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; position: relative;">
                                    <div style="width: ${valScore}%; height: 100%; background: linear-gradient(90deg, #10b981, #22c55e); box-shadow: 0 0 6px var(--primary-glow); border-radius: 3px;"></div>
                                </div>
                                <span style="font-family: 'Poppins', sans-serif; font-weight: 800; font-size: 0.72rem; color: #fff;">${valScore}</span>
                            </div>
                        ` : '';
                    })()}
                    
                    ${multiStoreBadge}
                    
                    <div class="card-bottom-wrapper" style="margin-top: auto; display: flex; flex-direction: column; gap: 0.2rem;">
                        <div class="card-store-dots" style="margin-top: 0; margin-bottom: 0.4rem;">
                            ${storeDotsHtml}
                        </div>
                        
                        <div class="neon-price-pill" style="margin-bottom: 0.4rem;">Desde ${formatCLP(bestOffer.price)}</div>
                        
                        <div class="card-bottom-row" style="margin-top: 0; padding-top: 0.5rem;">
                            <div class="card-rating">
                                <span class="star">★</span> <span class="rating-val">${rating}</span>
                                <span class="reviews-count">${reviews} Reseñas</span>
                            </div>
                            <button class="btn-ver-ofertas" onclick="openProductAction(${product.id}, event)" title="${isIntlProduct ? 'Abrir en AliExpress' : 'Ver detalle'}">
                                ${actionLabel}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.btn-ver-ofertas') && !e.target.closest('a') && !e.target.closest('.btn-compare-toggle') && !e.target.closest('.btn-fav')) {
                    openProductAction(product.id, e);
                }
            });
            fragment.appendChild(card);
        });
        grid.appendChild(fragment);
        openPendingProductFromUrl();
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
async function loadFavorites() {
    state.favorites = [];
    
    // Load guest favorites from localStorage
    const local = localStorage.getItem('bicitodo_favorites');
    if (local) {
        try {
            state.favorites = JSON.parse(local);
        } catch (e) {
            state.favorites = [];
        }
    }
    
    // If logged in via Firebase, sync/fetch from Firestore
    if (useFirebase && cloudAuth && cloudAuth.currentUser) {
        try {
            const uid = cloudAuth.currentUser.uid;
            const doc = await cloudDb.collection('bicitodo_users').doc(uid).get();
            if (doc.exists) {
                const cloudFavs = doc.data().favorites || [];
                
                // Merge local and cloud favorites
                const merged = [...state.favorites];
                cloudFavs.forEach(cf => {
                    if (!merged.some(lf => lf.id === cf.id)) {
                        merged.push(cf);
                    }
                });
                
                state.favorites = merged;
                // Save back to cloud and local
                await cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: merged }, { merge: true });
                localStorage.setItem('bicitodo_favorites', JSON.stringify(merged));
            } else {
                // First time user, save current local favorites to cloud
                await cloudDb.collection('bicitodo_users').doc(uid).set({ favorites: state.favorites });
            }
        } catch (e) {
            console.error("Error syncing favorites with Firestore:", e);
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
            <a href="#catalog" class="nav-link" id="nav-cuenta" onclick="openAuthModal(event)" style="display: flex; align-items: center; gap: 0.35rem;">
                ${GOOGLE_AUTH_LOGO}
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
    const content = document.getElementById('auth-modal-content');
    if (!content) return;
    
    if (state.activeAuthTab === 'login') {
        content.innerHTML = `
            <button class="modal-close" onclick="closeAuthModal()"><i class="fa-solid fa-xmark"></i></button>
            <form class="auth-form-container" onsubmit="handleAuthSubmit(event)">
                <h2 style="font-family:'Poppins',sans-serif; font-weight:800; color:#fff; font-size:1.5rem;"><i class="fa-solid fa-user-lock" style="color:var(--primary);"></i> Iniciar Sesión</h2>
                <p style="color:var(--text-muted); font-size:0.85rem; margin-top:-0.5rem;">Respalda tus favoritos en la nube y activa alertas de precio.</p>
                ${!useFirebase ? `
                <div style="background:rgba(251,146,60,0.1); border:1px solid rgba(251,146,60,0.3); border-radius:10px; padding:0.65rem 0.85rem; margin-bottom:0.75rem; display:flex; align-items:flex-start; gap:0.5rem;">
                    <i class="fa-solid fa-circle-info" style="color:#fb923c; margin-top:0.15rem; flex-shrink:0;"></i>
                    <span style="font-size:0.8rem; color:#fb923c; line-height:1.45;"><strong>Modo Local Activo</strong> — Tus datos se guardan en este navegador. Para sincronizar en la nube, configura Firebase en <code style="font-size:0.75rem;">app.js</code>.</span>
                </div>` : ''}
                
                <div class="auth-tabs">
                    <button type="button" class="auth-tab-btn active">Ingresar</button>
                    <button type="button" class="auth-tab-btn" onclick="switchAuthTab('signup')">Crear Cuenta</button>
                </div>
                
                <div class="auth-inputs">
                    <div class="auth-input-group">
                        <label>Correo Electrónico</label>
                        <input type="email" id="auth-email" required placeholder="tu@correo.com">
                    </div>
                    <div class="auth-input-group">
                        <label>Contraseña</label>
                        <input type="password" id="auth-password" required placeholder="••••••••">
                    </div>
                </div>
                
                <button type="submit" class="btn-auth-submit">Iniciar Sesión</button>

                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin: 0.75rem 0;">
                    <span style="flex-grow: 1; height: 1px; background: rgba(255,255,255,0.08);"></span>
                    <span style="font-size: 0.7rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">o</span>
                    <span style="flex-grow: 1; height: 1px; background: rgba(255,255,255,0.08);"></span>
                </div>

                <button type="button" class="btn-auth-google" onclick="handleGoogleLogin(event)" style="display:flex; align-items:center; justify-content:center; gap:0.5rem; width:100%; padding:0.65rem; border-radius:99px; border:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.03); color:#fff; font-family:'Poppins',sans-serif; font-weight:700; font-size:0.8rem; cursor:pointer; transition:all 0.2s;" onmouseenter="this.style.background='rgba(255,255,255,0.08)'" onmouseleave="this.style.background='rgba(255,255,255,0.03)'">
                    ${GOOGLE_AUTH_LOGO} Iniciar sesión con Google
                </button>
                
                <div class="auth-switch-text">
                    ¿No tienes cuenta? <span onclick="switchAuthTab('signup')">Regístrate gratis</span>
                </div>
            </form>
        `;
    } else {
        content.innerHTML = `
            <button class="modal-close" onclick="closeAuthModal()"><i class="fa-solid fa-xmark"></i></button>
            <form class="auth-form-container" onsubmit="handleAuthSubmit(event)">
                <h2 style="font-family:'Poppins',sans-serif; font-weight:800; color:#fff; font-size:1.5rem;"><i class="fa-solid fa-user-plus" style="color:var(--primary);"></i> Crear Cuenta</h2>
                <p style="color:var(--text-muted); font-size:0.85rem; margin-top:-0.5rem;">Crea tu perfil 100% gratis en segundos.</p>
                
                <div class="auth-tabs">
                    <button type="button" class="auth-tab-btn" onclick="switchAuthTab('login')">Ingresar</button>
                    <button type="button" class="auth-tab-btn active">Crear Cuenta</button>
                </div>
                
                <div class="auth-inputs">
                    <div class="auth-input-group">
                        <label>Nombre Completo</label>
                        <input type="text" id="auth-name" required placeholder="Juan Pérez">
                    </div>
                    <div class="auth-input-group">
                        <label>Correo Electrónico</label>
                        <input type="email" id="auth-email" required placeholder="tu@correo.com">
                    </div>
                    <div class="auth-input-group">
                        <label>Contraseña</label>
                        <input type="password" id="auth-password" required minlength="6" placeholder="Mínimo 6 caracteres">
                    </div>
                </div>
                
                <!-- Selector de Mascota Amigable Inicial -->
                <div style="text-align: left; display: flex; flex-direction: column; gap: 0.4rem; margin-top: 0.2rem; margin-bottom: 0.2rem;">
                    <label style="font-size: 0.72rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px;">Elige tu mascota de perfil:</label>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; background: rgba(0, 0, 0, 0.2); padding: 0.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); justify-items: center;">
                        ${Object.keys(EMOJI_GRADIENTS).map(emoji => {
                            const isActive = state.selectedSignupAvatar === emoji;
                            const borderStyle = isActive ? '2px solid var(--primary)' : '2px solid transparent';
                            const shadowStyle = isActive ? '0 0 8px var(--primary-glow)' : 'none';
                            const scaleStyle = isActive ? 'scale(1.15)' : 'scale(1)';
                            return `
                                <button type="button" onclick="selectSignupAvatar('${emoji}')" style="background: ${EMOJI_GRADIENTS[emoji]}; width: 34px; height: 34px; border-radius: 50%; border: ${borderStyle}; cursor: pointer; transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); display: flex; align-items: center; justify-content: center; font-size: 1.15rem; box-shadow: ${shadowStyle}; transform: ${scaleStyle}; padding:0; outline:none;" class="avatar-signup-pill ${isActive ? 'active-avatar' : ''}" title="Elegir ${emoji}" onmouseenter="this.style.transform='scale(1.3)'" onmouseleave="this.style.transform='${scaleStyle}'">
                                    ${emoji}
                                </button>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <button type="submit" class="btn-auth-submit">Registrarme</button>
                
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
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    
    if (useFirebase && cloudAuth) {
        try {
            await firebasePersistenceReady;
            showToast('Conectando con la nube...');
            if (state.activeAuthTab === 'login') {
                const userCred = await cloudAuth.signInWithEmailAndPassword(email, password);
                cacheAuthUserProfile({
                    uid: userCred.user.uid,
                    email: userCred.user.email,
                    displayName: userCred.user.displayName || email.split('@')[0],
                    avatar: userCred.user.photoURL || 'ðŸ¦Š'
                });
                showToast('¡Sesión iniciada con éxito!');
            } else {
                const name = document.getElementById('auth-name').value;
                const avatar = state.selectedSignupAvatar || '🦊';
                const userCred = await cloudAuth.createUserWithEmailAndPassword(email, password);
                await userCred.user.updateProfile({ displayName: name, photoURL: avatar });
                
                // save to Firestore
                try {
                    await cloudDb.collection('bicitodo_users').doc(userCred.user.uid).set({
                        displayName: name,
                        email: email,
                        avatar: avatar,
                        favorites: state.favorites
                    }, { merge: true });
                } catch(e) {
                    console.warn("Could not save profile metadata to Firestore:", e);
                }

                state.user = {
                    uid: userCred.user.uid,
                    email: userCred.user.email,
                    displayName: name,
                    avatar: avatar
                };
                cacheAuthUserProfile(state.user);
            }
            closeAuthModal();
            loadFavorites().then(() => {
                updateUserMenu();
                render(false);
            }).catch((favoritesError) => {
                console.warn("Favorites sync skipped after Google login:", favoritesError);
            });
        } catch (error) {
            console.error("Auth error:", error);
            showToast('Error de autenticación: ' + error.message);
        }
    } else {
        // Local mock auth mode
        showToast('Modo de Prueba Local Activo (Sin credenciales en la nube)');
        setTimeout(() => {
            if (state.activeAuthTab === 'login') {
                // If there's already a saved mock user, load its avatar
                let savedAvatar = '🦊';
                try {
                    const mockData = localStorage.getItem('bicitodo_mock_user');
                    if (mockData) {
                        const parsed = JSON.parse(mockData);
                        if (parsed.email === email && parsed.avatar) {
                            savedAvatar = parsed.avatar;
                        }
                    }
                } catch(e) {}
                
                state.user = {
                    email: email,
                    displayName: email.split('@')[0],
                    avatar: savedAvatar
                };
                showToast('Sesión iniciada en modo local.');
            } else {
                const name = document.getElementById('auth-name').value;
                state.user = {
                    email: email,
                    displayName: name,
                    avatar: state.selectedSignupAvatar || '🦊'
                };
                showToast('Cuenta de prueba creada en modo local.');
            }
            localStorage.setItem('bicitodo_mock_user', JSON.stringify(state.user));
            loadFavorites().then(() => {
                updateUserMenu();
                closeAuthModal();
                render();
            });
        }, 800);
    }
};

handleGoogleLogin = window.handleGoogleLogin = async function(event) {
    if (event) event.preventDefault();
    if (useFirebase && cloudAuth) {
        try {
            await firebasePersistenceReady;
            showToast('Conectando con Google...');
            const provider = new firebase.auth.GoogleAuthProvider();
            const result = await cloudAuth.signInWithPopup(provider);
            const user = result.user;
            const fallbackAvatar = user.photoURL || 'ðŸ¦Š';

            state.user = {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName || (user.email ? user.email.split('@')[0] : 'Usuario'),
                avatar: fallbackAvatar
            };
            cacheAuthUserProfile(state.user);
            
            try {
            // Check if profile exists, otherwise save
            const userDoc = await cloudDb.collection('bicitodo_users').doc(user.uid).get();
            if (!userDoc.exists) {
                await cloudDb.collection('bicitodo_users').doc(user.uid).set({
                    displayName: user.displayName,
                    email: user.email,
                    avatar: '🦊',
                    favorites: []
                }, { merge: true });
            }
            } catch (firestoreError) {
                console.warn("Google login ok, Firestore sync skipped:", firestoreError);
                showToast('Google conectado. Sincronizacion en la nube pendiente.');
            }
            updateUserMenu();
            render();
            showToast('¡Sesión iniciada con Google!');
            closeAuthModal();
        } catch (error) {
            console.error("Google Auth error:", error);
            showToast('Error de Google: ' + error.message);
        }
    } else {
        showToast('Google Login no está disponible en modo de prueba local.');
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
            showToast('¡Alerta de precio creada en Supabase!');
            
            // Replicate standard favorite visual behaviour
            const activeFav = state.favorites.find(f => f.id === productId);
            if (activeFav) {
                activeFav.alertPrice = targetPrice;
            } else {
                state.favorites.push({ id: productId, alertPrice: targetPrice });
            }
            localStorage.setItem('bicitodo_favorites', JSON.stringify(state.favorites));
            openProductDetail(productId);
            render();
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
    render();
    if (useFirebase && cloudAuth) {
        try {
            await cloudAuth.signOut();
            showToast('Sesión cerrada.');
        } catch (e) {
            showToast('Error al cerrar sesión.');
        }
    } else {
        state.user = null;
        localStorage.removeItem('bicitodo_mock_user');
        clearAuthUserProfileCache();
        localStorage.removeItem('bicitodo_favorites');
        state.favorites = [];
        showToast('Sesión local cerrada.');
        updateUserMenu();
        render();
    }
};

function setupFirebaseAuthListener() {
    // Auth modal overlay background close trigger
    const overlay = document.getElementById('auth-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeAuthModal();
        });
    }

    if (useFirebase && cloudAuth) {
        const cachedUser = getCachedAuthUserProfile();
        if (cachedUser) {
            state.user = cachedUser;
            updateUserMenu();
        }
        cloudAuth.onAuthStateChanged(async (user) => {
            if (user) {
                let userAvatar = user.photoURL || cachedUser?.avatar || '🦊';
                let userDisplayName = user.displayName || cachedUser?.displayName || (user.email ? user.email.split('@')[0] : 'Usuario');
                try {
                    const doc = await cloudDb.collection('bicitodo_users').doc(user.uid).get();
                    if (doc.exists && doc.data().avatar) {
                        userAvatar = doc.data().avatar;
                    }
                    if (doc.exists && doc.data().displayName) {
                        userDisplayName = doc.data().displayName;
                    }
                } catch(e) {
                    console.log("Could not fetch avatar from Firestore, using photoURL.");
                }
                
                state.user = {
                    uid: user.uid,
                    email: user.email,
                    displayName: userDisplayName,
                    avatar: userAvatar
                };
                cacheAuthUserProfile(state.user);
            } else {
                state.user = null;
                clearAuthUserProfileCache();
            }
            await loadFavorites();
            updateUserMenu();
            render();
        });
    } else {
        // Load mock user from localStorage if it exists
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
            render();
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

// Kickstart
init();
