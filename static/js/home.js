(function () {
    const track = document.getElementById('carousel');
    if (!track) return;

    const categoryMap = {};

    async function loadCategories() {
        try {
            const cats = await apiJson('/categories/');
            cats.forEach(function (c) { categoryMap[c.id] = c.name; });
        } catch (e) {}
    }

    function cardHtml(p) {
        const img = p.image
            ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy" class="w-full h-full object-cover" onerror="this.style.display='none'">`
            : '';
        const category = categoryMap[p.category];
        const badge = category
            ? `<span class="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 min-w-0 truncate">${esc(category)}</span>`
            : '';
        const addBtn = p.in_stock
            ? `<button type="button" data-id="${p.id}" class="js-add w-full rounded-lg bg-indigo-600 text-white py-2 text-sm hover:bg-indigo-700 transition-colors">В корзину</button>`
            : `<button type="button" disabled class="w-full rounded-lg bg-gray-200 text-gray-400 py-2 text-sm cursor-not-allowed">В корзину</button>`;
        return `
        <div class="snap-start shrink-0 w-60 bg-white border border-gray-200 rounded-xl p-3 flex flex-col">
            <a href="/product/?id=${p.id}" class="block aspect-[3/4] rounded-lg overflow-hidden bg-gray-100">${img}</a>
            <a href="/product/?id=${p.id}" class="mt-2 h-10 text-sm font-medium line-clamp-2 hover:underline">${esc(p.name)}</a>
            <div class="mt-1 mb-2 flex items-center justify-between gap-2">
                <span class="text-sm font-semibold shrink-0">${esc(formatPrice(p.price))}</span>
                ${badge}
            </div>
            <div class="mt-auto">${addBtn}</div>
        </div>`;
    }

    async function load() {
        try {
            const data = await apiJson('/products/?ordering=-created_at');
            const items = data.results.slice(0, 6);
            track.innerHTML = items.length ? items.map(cardHtml).join('') : '';
        } catch (e) {
            track.innerHTML = '';
        }
    }

    track.addEventListener('click', async function (e) {
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
        load();
    })();
})();
