(function () {
    const searchInput = document.getElementById('search');
    const categorySelect = document.getElementById('category');
    const orderingSelect = document.getElementById('ordering');
    const grid = document.getElementById('grid');
    const statusBox = document.getElementById('status');
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    let page = 1;
    const categoryMap = {};

    function buildQuery() {
        const params = new URLSearchParams();
        if (searchInput.value.trim()) params.set('search', searchInput.value.trim());
        if (categorySelect.value) params.set('category', categorySelect.value);
        if (orderingSelect.value) params.set('ordering', orderingSelect.value);
        if (page > 1) params.set('page', String(page));
        return params.toString();
    }

    async function loadCategories() {
        try {
            const categories = await apiJson('/categories/');
            categories.forEach(function (c) {
                categoryMap[c.id] = c.name;
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name;
                categorySelect.appendChild(opt);
            });
        } catch (e) {
            // категории не критичны для отображения товаров
        }
    }

    function cardHtml(p) {
        const available = p.in_stock;
        const category = categoryMap[p.category];
        const badge = category
            ? `<span class="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700">${esc(category)}</span>`
            : '';
        const addBtn = available
            ? `<button type="button" data-id="${p.id}" class="js-add flex-1 rounded-lg bg-indigo-600 text-white py-2 text-sm hover:bg-indigo-700 transition-colors">В корзину</button>`
            : `<button type="button" disabled class="flex-1 rounded-lg bg-gray-200 text-gray-400 py-2 text-sm cursor-not-allowed">В корзину</button>`;
        return `
        <div class="bg-white border border-gray-200 rounded-xl p-4 flex flex-col">
            <h3 class="font-medium">${esc(p.name)}</h3>
            <p class="text-sm text-gray-500 mt-1 line-clamp-2">${esc(p.description)}</p>
            <div class="mt-auto pt-4">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-lg font-semibold">${esc(formatPrice(p.price))}</span>
                    ${badge}
                </div>
                <div class="flex gap-2">
                    <a href="/product/?id=${p.id}" class="flex-1 text-center rounded-lg border border-gray-300 py-2 text-sm hover:bg-gray-50 transition-colors">Подробнее</a>
                    ${addBtn}
                </div>
            </div>
        </div>`;
    }

    function renderPagination(data) {
        const hasNext = Boolean(data.next);
        const hasPrev = Boolean(data.previous);
        if (!hasNext && !hasPrev) {
            pagination.classList.add('hidden');
            return;
        }
        pagination.classList.remove('hidden');
        prevBtn.disabled = !hasPrev;
        nextBtn.disabled = !hasNext;
        pageInfo.textContent = `Страница ${page} · товаров: ${data.count}`;
    }

    async function loadProducts() {
        statusBox.textContent = 'Загрузка…';
        grid.innerHTML = '';
        pagination.classList.add('hidden');
        try {
            const data = await apiJson('/products/?' + buildQuery());
            if (!data.results.length) {
                statusBox.textContent = 'Товары не найдены.';
                return;
            }
            statusBox.textContent = '';
            grid.innerHTML = data.results.map(cardHtml).join('');
            renderPagination(data);
        } catch (err) {
            statusBox.textContent = (err.data && err.data.detail) || 'Не удалось загрузить каталог.';
        }
    }

    function reload() {
        page = 1;
        loadProducts();
    }

    let searchTimer;
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(reload, 400);
    });
    categorySelect.addEventListener('change', reload);
    orderingSelect.addEventListener('change', reload);
    document.getElementById('filters').addEventListener('submit', function (e) {
        e.preventDefault();
        reload();
    });

    prevBtn.addEventListener('click', function () {
        if (page > 1) { page -= 1; loadProducts(); window.scrollTo(0, 0); }
    });
    nextBtn.addEventListener('click', function () {
        page += 1; loadProducts(); window.scrollTo(0, 0);
    });

    grid.addEventListener('click', async function (e) {
        const btn = e.target.closest('.js-add');
        if (!btn) return;
        if (!Session.requireAuth()) return;
        btn.disabled = true;
        try {
            await apiJson('/cart/', {
                method: 'POST',
                body: JSON.stringify({ product: Number(btn.dataset.id), quantity: 1 }),
            });
            toast('Добавлено в корзину');
        } catch (err) {
            toast((err.data && err.data.detail) || 'Не удалось добавить товар.', 'error');
        } finally {
            btn.disabled = false;
        }
    });

    (async function init() {
        await loadCategories();
        loadProducts();
    })();
})();
