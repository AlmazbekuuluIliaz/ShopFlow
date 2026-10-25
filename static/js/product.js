(function () {
    const statusBox = document.getElementById('status');
    const card = document.getElementById('product');
    const qtyInput = document.getElementById('qty');
    const addBtn = document.getElementById('addBtn');

    const productId = new URLSearchParams(window.location.search).get('id');

    function renderSpecs(specs) {
        if (!specs || !specs.length) return;
        const dl = document.getElementById('pSpecs');
        dl.innerHTML = specs.map(function (s) {
            return `<div class="flex justify-between gap-4 border-b border-gray-100 py-1"><dt class="text-gray-500">${esc(s.label)}</dt><dd class="text-gray-800 text-right">${esc(s.value)}</dd></div>`;
        }).join('');
        document.getElementById('pSpecsBlock').classList.remove('hidden');
    }

    function renderRelated(items) {
        if (!items || !items.length) return;
        const grid = document.getElementById('relatedGrid');
        grid.innerHTML = items.map(function (p) {
            const img = p.image
                ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy" class="w-full h-full object-cover" onerror="this.style.display='none'">`
                : '';
            return `
            <a href="/product/?id=${p.id}" class="bg-white border border-gray-200 rounded-xl p-3 flex flex-col hover:shadow-sm transition-shadow">
                <div class="aspect-[3/4] rounded-lg overflow-hidden bg-gray-100 mb-2">${img}</div>
                <span class="text-sm font-medium line-clamp-2">${esc(p.name)}</span>
                <span class="mt-1 text-sm font-semibold">${esc(formatPrice(p.price))}</span>
            </a>`;
        }).join('');
        document.getElementById('relatedWrap').classList.remove('hidden');
    }

    function renderGallery(p) {
        const imgEl = document.getElementById('pImage');
        const imgWrap = document.getElementById('pImageWrap');
        const thumbs = document.getElementById('pThumbs');

        const gallery = [];
        if (p.image) gallery.push({ src: p.image, alt: p.name });
        (p.images || []).forEach(function (im) {
            gallery.push({ src: im.image, alt: im.alt || p.name });
        });

        if (!gallery.length) {
            imgWrap.style.display = 'none';
            return;
        }

        imgEl.src = gallery[0].src;
        imgEl.alt = gallery[0].alt;
        imgEl.onerror = function () { imgWrap.style.display = 'none'; };

        if (gallery.length < 2) return;
        thumbs.innerHTML = gallery.map(function (g, i) {
            return `<button type="button" data-src="${esc(g.src)}" class="js-thumb aspect-square rounded-lg overflow-hidden bg-gray-100 border ${i === 0 ? 'border-indigo-500' : 'border-gray-200'}"><img src="${esc(g.src)}" alt="${esc(g.alt)}" loading="lazy" class="w-full h-full object-cover"></button>`;
        }).join('');
        thumbs.addEventListener('click', function (e) {
            const btn = e.target.closest('.js-thumb');
            if (!btn) return;
            imgEl.src = btn.dataset.src;
            thumbs.querySelectorAll('.js-thumb').forEach(function (b) {
                b.className = b.className.replace('border-indigo-500', 'border-gray-200');
            });
            btn.className = btn.className.replace('border-gray-200', 'border-indigo-500');
        });
    }

    function render(p) {
        renderGallery(p);

        document.getElementById('pCategory').textContent = (p.category_detail && p.category_detail.name) || '';
        document.getElementById('pName').textContent = p.name;
        document.getElementById('pPrice').textContent = formatPrice(p.price);
        document.getElementById('pDesc').textContent = (p.description || '').trim();

        renderSpecs(p.specs);

        const avail = document.getElementById('pAvail');
        if (p.in_stock) {
            avail.textContent = 'В наличии: ' + p.stock + ' шт.';
            avail.className = 'mt-1 text-sm text-green-700';
            qtyInput.max = p.stock;
        } else {
            avail.textContent = 'Нет в наличии';
            avail.className = 'mt-1 text-sm text-gray-500';
            qtyInput.disabled = true;
            addBtn.disabled = true;
            addBtn.className = 'rounded-lg bg-gray-200 text-gray-400 px-6 py-2.5 font-medium cursor-not-allowed';
        }

        card.classList.remove('hidden');
    }

    async function load() {
        if (!productId) {
            statusBox.textContent = 'Товар не указан.';
            return;
        }
        statusBox.textContent = 'Загрузка…';
        try {
            const p = await apiJson('/products/' + productId + '/');
            statusBox.textContent = '';
            render(p);
            renderRelated(p.related);
        } catch (err) {
            statusBox.textContent = err.status === 404 ? 'Товар не найден.' : 'Не удалось загрузить товар.';
        }
    }

    addBtn.addEventListener('click', async function () {
        if (!Session.requireAuth()) return;
        const quantity = Math.max(1, parseInt(qtyInput.value, 10) || 1);
        addBtn.disabled = true;
        try {
            await apiJson('/cart/', {
                method: 'POST',
                body: JSON.stringify({ product: Number(productId), quantity }),
            });
            toast('Добавлено в корзину');
        } catch (err) {
            toast((err.data && err.data.detail) || 'Не удалось добавить товар.', 'error');
        } finally {
            addBtn.disabled = false;
        }
    });

    load();
})();
