(function () {
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const formError = document.getElementById('formError');

    function showError(message) {
        formError.textContent = message;
        formError.classList.remove('hidden');
    }

    function clearError() {
        formError.textContent = '';
        formError.classList.add('hidden');
    }

    function formatError(err) {
        const data = err && err.data;
        if (!data) return 'Не удалось выполнить запрос. Попробуйте позже.';
        if (typeof data === 'string') return data;
        if (data.detail) return data.detail;
        const parts = [];
        for (const key in data) {
            const value = data[key];
            parts.push(Array.isArray(value) ? value.join(' ') : String(value));
        }
        return parts.length ? parts.join(' ') : 'Проверьте правильность введённых данных.';
    }

    function setActive(active, inactive) {
        active.classList.add('bg-white', 'shadow-sm');
        active.classList.remove('text-gray-600');
        inactive.classList.remove('bg-white', 'shadow-sm');
        inactive.classList.add('text-gray-600');
    }

    function switchTab(target) {
        clearError();
        if (target === 'register') {
            registerForm.classList.remove('hidden');
            loginForm.classList.add('hidden');
            setActive(tabRegister, tabLogin);
        } else {
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            setActive(tabLogin, tabRegister);
        }
    }

    function nextUrl() {
        const params = new URLSearchParams(window.location.search);
        return params.get('next') || '/';
    }

    async function obtainToken(username, password) {
        const data = await apiJson('/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        auth.save(data.access, data.refresh);
    }

    tabLogin.addEventListener('click', function () { switchTab('login'); });
    tabRegister.addEventListener('click', function () { switchTab('register'); });

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        clearError();
        const form = new FormData(loginForm);
        try {
            await obtainToken(form.get('username'), form.get('password'));
            window.location.href = nextUrl();
        } catch (err) {
            showError(err.status === 401 ? 'Неверное имя пользователя или пароль.' : formatError(err));
        }
    });

    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        clearError();
        const form = new FormData(registerForm);
        const username = form.get('username');
        const password = form.get('password');
        const payload = { username, password };
        if (form.get('email')) payload.email = form.get('email');
        if (form.get('phone')) payload.phone = form.get('phone');
        try {
            await apiJson('/auth/register/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            await obtainToken(username, password);
            window.location.href = nextUrl();
        } catch (err) {
            showError(formatError(err));
        }
    });
})();
