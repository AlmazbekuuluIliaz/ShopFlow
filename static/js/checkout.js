(function () {
    if (!Session.requireAuth()) return;

    const statusBox = document.getElementById('status');
    const emptyBox = document.getElementById('empty');
    const checkoutBox = document.getElementById('checkout');
    const form = document.getElementById('form');
    const fName = document.getElementById('fName');
    const fPhone = document.getElementById('fPhone');
    const fAddress = document.getElementById('fAddress');
    const fComment = document.getElementById('fComment');
    const sumItems = document.getElementById('sumItems');
    const sumQty = document.getElementById('sumQty');
    const sumDelivery = document.getElementById('sumDelivery');
    const sumTotal = document.getElementById('sumTotal');
    const submitBtn = document.getElementById('submit');
    const modal = document.getElementById('modal');
    const receipt = document.getElementById('receipt');

    let itemsTotal = 0;
    let tiers = [];

    function deliveryForSubtotal(subtotal) {
        let price = 0;
        tiers.forEach(function (t) {
            if (subtotal >= Number(t.min_subtotal)) price = Number(t.price);
        });
        return price;
    }

    function deliveryLabel(amount) {
        return amount > 0 ? formatPrice(amount) : 'Бесплатно';
    }

    function updateSummary() {
        const delivery = deliveryForSubtotal(itemsTotal);
        sumItems.textContent = formatPrice(itemsTotal);
        sumDelivery.textContent = deliveryLabel(delivery);
        sumTotal.textContent = formatPrice(itemsTotal + delivery);
    }

    function receiptRow(label, valueHtml) {
        return `
        <div class="flex justify-between gap-4">
            <dt class="font-semibold text-gray-700 shrink-0">${esc(label)}</dt>
            <dd class="text-gray-900 text-right min-w-0">${valueHtml}</dd>
        </div>`;
    }

    function showReceipt(order) {
        const itemsLines = order.items.map(function (it) {
            return esc(it.product_name) + ' × ' + it.quantity;
        }).join('<br>');
        receipt.innerHTML = [
            receiptRow('Номер заказа', '#' + order.id),
            receiptRow('Заказчик', esc(order.contact_name || order.username)),
            receiptRow('Номер телефона', esc(order.phone || '—')),
            receiptRow('Адрес', esc(order.address || '—')),
            receiptRow('Товары', itemsLines + ' — ' + esc(formatPrice(order.items_total))),
            receiptRow('Доставка', esc(deliveryLabel(Number(order.delivery_price)))),
            receiptRow('Скидка', esc(formatPrice(order.discount))),
            receiptRow('Итого', '<span class="font-bold">' + esc(formatPrice(order.total_price)) + '</span>'),
        ].join('');
        modal.classList.remove('hidden');
        updateCartBadge();
    }

    async function submitOrder(e) {
        e.preventDefault();
        const name = fName.value.trim();
        const phone = fPhone.value.trim();
        const address = fAddress.value.trim();
        if (!name) { toast('Укажите имя.', 'error'); fName.focus(); return; }
        if (!phone) { toast('Укажите номер телефона.', 'error'); fPhone.focus(); return; }
        if (!address) { toast('Укажите адрес.', 'error'); fAddress.focus(); return; }

        submitBtn.disabled = true;
        try {
            const order = await apiJson('/orders/', {
                method: 'POST',
                body: JSON.stringify({
                    contact_name: name,
                    phone: phone,
                    address: address,
                    comment: fComment.value.trim(),
                }),
            });
            showReceipt(order);
        } catch (err) {
            const data = err.data;
            let msg = 'Не удалось оформить заказ.';
            if (data && data.detail) {
                msg = data.detail;
            } else if (data && typeof data === 'object') {
                const key = Object.keys(data)[0];
                if (key) {
                    const v = data[key];
                    msg = Array.isArray(v) ? v[0] : String(v);
                }
            }
            toast(msg, 'error');
            submitBtn.disabled = false;
        }
    }

    async function init() {
        statusBox.textContent = 'Загрузка…';
        try {
            const results = await Promise.all([
                apiJson('/users/me/'),
                apiJson('/cart/'),
                apiJson('/delivery-tiers/'),
            ]);
            const me = results[0];
            const cart = results[1];
            tiers = results[2];
            statusBox.textContent = '';

            if (!cart.items.length) {
                emptyBox.classList.remove('hidden');
                return;
            }
            itemsTotal = Number(cart.total_price);
            sumQty.textContent = cart.total_quantity + ' товаров';

            fName.value = me.username || '';
            fPhone.value = me.phone || '';

            updateSummary();
            checkoutBox.classList.remove('hidden');
        } catch (e) {
            statusBox.textContent = 'Не удалось загрузить данные оформления.';
        }
    }

    form.addEventListener('submit', submitOrder);

    init();
})();
