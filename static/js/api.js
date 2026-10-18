const API_BASE = '/api';

const TOKEN_ACCESS = 'shopflow_access';
const TOKEN_REFRESH = 'shopflow_refresh';

const auth = {
    get access() {
        try { return localStorage.getItem(TOKEN_ACCESS); } catch (e) { return null; }
    },
    get refresh() {
        try { return localStorage.getItem(TOKEN_REFRESH); } catch (e) { return null; }
    },
    save(access, refresh) {
        try {
            if (access) localStorage.setItem(TOKEN_ACCESS, access);
            if (refresh) localStorage.setItem(TOKEN_REFRESH, refresh);
        } catch (e) {}
    },
    clear() {
        try {
            localStorage.removeItem(TOKEN_ACCESS);
            localStorage.removeItem(TOKEN_REFRESH);
        } catch (e) {}
    },
    get isAuthenticated() {
        return Boolean(this.access);
    },
};

async function refreshAccess() {
    const refresh = auth.refresh;
    if (!refresh) return false;

    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
    });

    if (!res.ok) {
        auth.clear();
        return false;
    }

    const data = await res.json();
    auth.save(data.access, null);
    return true;
}

async function apiFetch(path, options = {}, retry = true) {
    const headers = Object.assign({}, options.headers);

    if (options.body !== undefined && !(options.body instanceof FormData)) {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    if (auth.access) {
        headers['Authorization'] = `Bearer ${auth.access}`;
    }

    const res = await fetch(`${API_BASE}${path}`, Object.assign({}, options, { headers }));

    if (res.status === 401 && retry && auth.refresh) {
        const ok = await refreshAccess();
        if (ok) return apiFetch(path, options, false);
    }

    return res;
}

async function apiJson(path, options = {}) {
    const res = await apiFetch(path, options);
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;

    if (!res.ok) {
        const error = new Error('Ошибка запроса');
        error.status = res.status;
        error.data = data;
        throw error;
    }

    return data;
}
