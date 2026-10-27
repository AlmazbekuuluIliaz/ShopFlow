function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

function esc(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

function toast(message, type = 'success') {
    let box = document.getElementById('toastBox');
    if (!box) {
        box = document.createElement('div');
        box.id = 'toastBox';
        box.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(box);
    }
    const color = type === 'error' ? 'bg-red-600' : 'bg-gray-900';
    const item = document.createElement('div');
    item.className = `${color} text-white text-sm px-4 py-2 rounded-lg shadow-lg`;
    item.textContent = message;
    box.appendChild(item);
    setTimeout(function () { item.remove(); }, 2500);
}

function renderGuest() {
    document.querySelectorAll('.js-guest').forEach(show);
    document.querySelectorAll('.js-user').forEach(hide);
    document.querySelectorAll('.js-admin').forEach(hide);
}

function renderUser(me) {
    document.querySelectorAll('.js-guest').forEach(hide);
    document.querySelectorAll('.js-user').forEach(show);
    document.querySelectorAll('.js-username').forEach(function (el) {
        el.textContent = me.username;
    });
    const isAdmin = me.role === 'ADMIN';
    document.querySelectorAll('.js-admin').forEach(isAdmin ? show : hide);
}

async function updateNav() {
    if (!auth.isAuthenticated) {
        renderGuest();
        return;
    }
    try {
        const me = await apiJson('/users/me/');
        renderUser(me);
    } catch (e) {
        auth.clear();
        renderGuest();
    }
}

async function updateCartBadge(cart) {
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    if (!auth.isAuthenticated) {
        badge.classList.add('hidden');
        return;
    }
    try {
        if (!cart) cart = await apiJson('/cart/');
        const n = cart.total_quantity || 0;
        if (n > 0) {
            badge.textContent = n > 99 ? '99+' : n;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    } catch (e) {
        badge.classList.add('hidden');
    }
}

async function logout() {
    const refresh = auth.refresh;
    if (refresh) {
        try {
            await apiFetch('/auth/logout/', {
                method: 'POST',
                body: JSON.stringify({ refresh }),
            }, false);
        } catch (e) {}
    }
    auth.clear();
    window.location.href = '/';
}

const Session = {
    requireAuth() {
        if (!auth.isAuthenticated) {
            const next = encodeURIComponent(window.location.pathname + window.location.search);
            window.location.href = `/login/?next=${next}`;
            return false;
        }
        return true;
    },
};

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.js-logout').forEach(function (btn) {
        btn.addEventListener('click', logout);
    });
    updateNav();
    updateCartBadge();
});
