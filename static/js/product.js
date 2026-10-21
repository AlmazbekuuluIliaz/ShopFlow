(function () {
    const statusBox = document.getElementById('status');
    const card = document.getElementById('product');
    const qtyInput = document.getElementById('qty');
    const addBtn = document.getElementById('addBtn');
    const buyRow = document.getElementById('buyRow');

    const productId = new URLSearchParams(window.location.search).get('id');

    async function categoryName(id) {
        if (!id) return '';
        try {
            const c = await apiJson('/categories/' + id + '/');
            return c.name;
        } catch (e) {
            return '';
        }
    }

    function render(p, catName) {
        const imgEl = document.getElementById('pImage');
        const imgWrap = document.getElementById('pImageWrap');
        if (p.image) {
            imgEl.src = p.image;
            imgEl.onerror = function () { imgWrap.style.display = 'none'; };
        } else {
            imgWrap.style.display = 'none';
        }

        document.getElementById('pCategory').textContent = catName;
        document.getElementById('pName').textContent = p.name;
        document.getElementById('pPrice').textContent = formatPrice(p.price);
        document.getElementById('pDesc').textContent = (p.description || '').trim();

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
            const catName = await categoryName(p.category);
            statusBox.textContent = '';
            render(p, catName);
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
