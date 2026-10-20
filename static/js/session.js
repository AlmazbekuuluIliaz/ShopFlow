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
}

function renderUser(username) {
    document.querySelectorAll('.js-guest').forEach(hide);
    document.querySelectorAll('.js-user').forEach(show);
    document.querySelectorAll('.js-username').forEach(function (el) {
        el.textContent = username;
    });
}

async function updateNav() {
    if (!auth.isAuthenticated) {
        renderGuest();
        return;
    }
    try {
        const me = await apiJson('/users/me/');
        renderUser(me.username);
    } catch (e) {
        auth.clear();
        renderGuest();
    }
}

function logout() {
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
});
