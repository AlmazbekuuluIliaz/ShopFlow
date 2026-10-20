(function () {
    if (!Session.requireAuth()) return;

    const statusBox = document.getElementById('status');
    const ordersBox = document.getElementById('orders');
    const emptyBox = document.getElementById('empty');

    const STATUS = {
        PENDING: { label: 'Ожидает', cls: 'bg-yellow-100 text-yellow-800' },
        CONFIRMED: { label: 'Подтверждён', cls: 'bg-blue-100 text-blue-800' },
        PROCESSING: { label: 'В обработке', cls: 'bg-indigo-100 text-indigo-800' },
        SHIPPED: { label: 'Отправлен', cls: 'bg-purple-100 text-purple-800' },
        DELIVERED: { label: 'Доставлен', cls: 'bg-green-100 text-green-800' },
        CANCELLED: { label: 'Отменён', cls: 'bg-red-100 text-red-700' },
    };

    function statusBadge(status) {
        const s = STATUS[status] || { label: status, cls: 'bg-gray-100 text-gray-700' };
        return `<span class="text-xs px-2.5 py-1 rounded-full ${s.cls}">${esc(s.label)}</span>`;
    }

    function formatDate(iso) {
        const d = new Date(iso);
        return isNaN(d) ? '' : d.toLocaleString('ru-RU', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    }

    function itemRow(it) {
        return `
        <div class="flex justify-between gap-2 py-2 text-sm">
            <span class="text-gray-700 min-w-0 break-words">${esc(it.product_name)} × ${it.quantity}</span>
            <span class="text-gray-900 shrink-0">${esc(formatPrice(it.subtotal))}</span>
        </div>`;
    }

    function orderCard(o) {
        return `
        <div class="bg-white border border-gray-200 rounded-xl p-5">
            <div class="flex items-center justify-between gap-3 flex-wrap">
                <div>
                    <span class="font-semibold">Заказ #${o.id}</span>
                    <span class="text-sm text-gray-500 ml-2">${esc(formatDate(o.created_at))}</span>
                </div>
                ${statusBadge(o.status)}
            </div>
            <div class="mt-4 divide-y divide-gray-100">
                ${o.items.map(itemRow).join('')}
            </div>
            <div class="flex justify-between font-semibold border-t border-gray-200 mt-3 pt-3">
                <span>Итого</span>
                <span>${esc(formatPrice(o.total_price))}</span>
            </div>
        </div>`;
    }

    async function loadOrders() {
        statusBox.textContent = 'Загрузка…';
        try {
            const orders = await apiJson('/orders/');
            statusBox.textContent = '';
            if (!orders.length) {
                emptyBox.classList.remove('hidden');
                return;
            }
            ordersBox.innerHTML = orders.map(orderCard).join('');
        } catch (e) {
            statusBox.textContent = 'Не удалось загрузить заказы.';
        }
    }

    loadOrders();
})();
