(function () {
    if (!Session.requireAuth()) return;

    const statusBox = document.getElementById('status');
    const cartBox = document.getElementById('cart');
    const emptyBox = document.getElementById('empty');
    const itemsBox = document.getElementById('items');
    const sumQty = document.getElementById('sumQty');
    const sumTotal = document.getElementById('sumTotal');
    const checkoutBtn = document.getElementById('checkout');

    function itemRow(it) {
        const atMax = it.quantity >= it.stock;
        return `
        <div data-id="${it.id}" data-stock="${it.stock}" class="bg-white border border-gray-200 rounded-xl p-4 flex gap-3 sm:gap-4">
            <a href="/product/?id=${it.product}" class="block w-16 sm:w-20 shrink-0 aspect-[3/4] rounded-lg overflow-hidden bg-gray-100">${it.image ? `<img src="${esc(it.image)}" alt="${esc(it.product_name)}" loading="lazy" class="w-full h-full object-cover" onerror="this.style.display='none'">` : ''}</a>
            <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                        <a href="/product/?id=${it.product}" class="font-medium hover:underline block truncate">${esc(it.product_name)}</a>
                        <div class="text-sm text-gray-500">${esc(formatPrice(it.price))} за шт.</div>
                    </div>
                    <button type="button" class="js-remove shrink-0 w-8 h-8 rounded-lg border border-gray-300 flex items-center justify-center text-gray-400 hover:text-red-600 hover:bg-gray-100" title="Удалить">✕</button>
                </div>
                <div class="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3">
                    <div class="flex items-center gap-2">
                        <button type="button" class="js-dec w-9 h-9 rounded-lg border border-gray-300 text-lg leading-none hover:bg-gray-100">−</button>
                        <input type="number" min="1" max="${it.stock}" value="${it.quantity}" aria-label="Количество"
                               class="js-qty w-14 h-9 text-center rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <button type="button" class="js-inc w-9 h-9 rounded-lg border border-gray-300 text-lg leading-none hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"${atMax ? ' disabled' : ''}>+</button>
                    </div>
                    <span class="text-xs text-gray-400 whitespace-nowrap">в наличии: ${it.stock} шт.</span>
                    <span class="font-semibold ml-auto">${esc(formatPrice(it.subtotal))}</span>
                </div>
            </div>
        </div>`;
    }

    function render(cart) {
        updateCartBadge(cart);
        if (!cart.items.length) {
            cartBox.classList.add('hidden');
            emptyBox.classList.remove('hidden');
            return;
        }
        emptyBox.classList.add('hidden');
        cartBox.classList.remove('hidden');
        itemsBox.innerHTML = cart.items.map(itemRow).join('');
        sumQty.textContent = cart.total_quantity;
        sumTotal.textContent = formatPrice(cart.total_price);
    }

    async function loadCart() {
        statusBox.textContent = 'Загрузка…';
        try {
            const cart = await apiJson('/cart/');
            statusBox.textContent = '';
            render(cart);
        } catch (e) {
            statusBox.textContent = 'Не удалось загрузить корзину.';
        }
    }

    async function updateQty(id, quantity) {
        if (quantity < 1) return;
        try {
            const cart = await apiJson('/cart/items/' + id + '/', {
                method: 'PATCH',
                body: JSON.stringify({ quantity }),
            });
            render(cart);
        } catch (err) {
            loadCart();
        }
    }

    async function removeItem(id) {
        try {
            const cart = await apiJson('/cart/items/' + id + '/', { method: 'DELETE' });
            render(cart);
        } catch (err) {
            toast('Не удалось удалить товар.', 'error');
        }
    }

    itemsBox.addEventListener('click', function (e) {
        const row = e.target.closest('[data-id]');
        if (!row) return;
        const id = Number(row.dataset.id);
        const stock = Number(row.dataset.stock);
        const input = row.querySelector('.js-qty');
        if (e.target.closest('.js-inc')) {
            const next = parseInt(input.value, 10) + 1;
            if (next <= stock) updateQty(id, next);
        } else if (e.target.closest('.js-dec')) {
            updateQty(id, parseInt(input.value, 10) - 1);
        } else if (e.target.closest('.js-remove')) {
            removeItem(id);
        }
    });

    itemsBox.addEventListener('change', function (e) {
        if (!e.target.classList.contains('js-qty')) return;
        const row = e.target.closest('[data-id]');
        const id = Number(row.dataset.id);
        const stock = Number(row.dataset.stock);
        let quantity = Math.max(1, parseInt(e.target.value, 10) || 1);
        if (quantity > stock) quantity = stock;
        updateQty(id, quantity);
    });

    checkoutBtn.addEventListener('click', async function () {
        checkoutBtn.disabled = true;
        try {
            await apiJson('/orders/', { method: 'POST', body: JSON.stringify({}) });
            toast('Заказ оформлен');
            window.location.href = '/orders/';
        } catch (err) {
            const data = err.data;
            const message = (data && data.detail)
                || (Array.isArray(data) ? data.join(' ') : null)
                || 'Не удалось оформить заказ.';
            toast(message, 'error');
            checkoutBtn.disabled = false;
        }
    });

    loadCart();
})();
