(function () {
    if (!Session.requireAuth()) return;

    const statusBox = document.getElementById('status');
    const ordersBox = document.getElementById('orders');
    const emptyBox = document.getElementById('empty');
    const titleEl = document.querySelector('h1');

    let isAdmin = false;

    const STATUS = {
        PENDING: { label: 'Ожидает', cls: 'bg-yellow-100 text-yellow-800' },
        CONFIRMED: { label: 'Подтверждён', cls: 'bg-blue-100 text-blue-800' },
        PROCESSING: { label: 'В обработке', cls: 'bg-indigo-100 text-indigo-800' },
        SHIPPED: { label: 'Отправлен', cls: 'bg-purple-100 text-purple-800' },
        DELIVERED: { label: 'Доставлен', cls: 'bg-green-100 text-green-800' },
        CANCELLED: { label: 'Отменён', cls: 'bg-red-100 text-red-700' },
    };

    const ALLOWED_TRANSITIONS = {
        PENDING: ['CONFIRMED', 'CANCELLED'],
        CONFIRMED: ['PROCESSING', 'CANCELLED'],
        PROCESSING: ['SHIPPED', 'CANCELLED'],
        SHIPPED: ['DELIVERED'],
        DELIVERED: [],
        CANCELLED: [],
    };

    function statusLabel(status) {
        return (STATUS[status] || { label: status }).label;
    }

    function statusBadge(status) {
        const s = STATUS[status] || { label: status, cls: 'bg-gray-100 text-gray-700' };
        return `<span class="shrink-0 whitespace-nowrap text-xs px-2.5 py-1 rounded-full ${s.cls}">${esc(s.label)}</span>`;
    }

    function statusControl(o) {
        const allowed = ALLOWED_TRANSITIONS[o.status] || [];
        if (!allowed.length) {
            return `
            <div class="flex items-center gap-2 shrink-0">
                ${statusBadge(o.status)}
                <span class="text-xs text-gray-400">финальный</span>
            </div>`;
        }
        const options = ['<option value="" disabled selected>Изменить…</option>']
            .concat(allowed.map(function (s) {
                return `<option value="${s}">${esc(statusLabel(s))}</option>`;
            }))
            .join('');
        return `
        <div class="flex items-center gap-2 shrink-0">
            ${statusBadge(o.status)}
            <select data-order-id="${o.id}" class="js-status-select text-xs border border-gray-300 rounded-lg px-2 py-1 bg-white">
                ${options}
            </select>
        </div>`;
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
        const customer = isAdmin
            ? `<span class="text-sm text-gray-500 ml-2">· ${esc(o.username)}</span>`
            : '';
        const right = isAdmin ? statusControl(o) : statusBadge(o.status);
        return `
        <div class="bg-white border border-gray-200 rounded-xl p-5">
            <div class="flex items-center justify-between gap-3">
                <div class="min-w-0 truncate">
                    <span class="font-semibold">Заказ #${o.id}</span>
                    <span class="text-sm text-gray-500 ml-2">${esc(formatDate(o.created_at))}</span>
                    ${customer}
                </div>
                ${right}
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
        emptyBox.classList.add('hidden');
        try {
            const orders = await apiJson('/orders/');
            statusBox.textContent = '';
            if (!orders.length) {
                ordersBox.innerHTML = '';
                emptyBox.classList.remove('hidden');
                return;
            }
            ordersBox.innerHTML = orders.map(orderCard).join('');
        } catch (e) {
            statusBox.textContent = 'Не удалось загрузить заказы.';
        }
    }

    async function changeStatus(select) {
        const id = select.getAttribute('data-order-id');
        const status = select.value;
        if (!status) return;
        select.disabled = true;
        try {
            await apiJson(`/orders/${id}/`, {
                method: 'PATCH',
                body: JSON.stringify({ status }),
            });
            toast('Статус обновлён');
            await loadOrders();
        } catch (err) {
            let msg = 'Не удалось изменить статус.';
            if (err.data) {
                const detail = err.data.detail || err.data.status;
                if (detail) msg = Array.isArray(detail) ? detail[0] : detail;
            }
            toast(msg, 'error');
            select.disabled = false;
        }
    }

    ordersBox.addEventListener('change', function (e) {
        const select = e.target.closest('.js-status-select');
        if (select) changeStatus(select);
    });

    async function init() {
        try {
            const me = await apiJson('/users/me/');
            isAdmin = me.role === 'ADMIN';
        } catch (e) {
            isAdmin = false;
        }
        if (isAdmin && titleEl) {
            titleEl.textContent = 'Все заказы';
        }
        if (isAdmin && emptyBox) {
            const p = emptyBox.querySelector('p');
            if (p) p.textContent = 'Заказов пока нет.';
        }
        await loadOrders();
    }

    init();
})();
