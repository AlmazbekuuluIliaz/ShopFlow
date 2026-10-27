(function () {
    if (!Session.requireAuth()) return;

    const statusBox = document.getElementById('status');
    const ordersBox = document.getElementById('orders');
    const emptyBox = document.getElementById('empty');
    const titleEl = document.querySelector('h1');
    const adminFilters = document.getElementById('adminFilters');
    const fSearch = document.getElementById('fSearch');
    const fStatus = document.getElementById('fStatus');
    const fCount = document.getElementById('fCount');

    let isAdmin = false;
    let allOrders = [];

    const STATUS = {
        PENDING: { label: 'Ожидает', cls: 'bg-indigo-50 text-indigo-700' },
        CONFIRMED: { label: 'Подтверждён', cls: 'bg-indigo-100 text-indigo-700' },
        PROCESSING: { label: 'В обработке', cls: 'bg-indigo-200 text-indigo-800' },
        SHIPPED: { label: 'Отправлен', cls: 'bg-indigo-300 text-indigo-900' },
        DELIVERED: { label: 'Доставлен', cls: 'bg-green-100 text-green-800' },
        CANCELLED: { label: 'Отменён', cls: 'bg-gray-100 text-gray-600' },
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

    function cancelButton(o) {
        if (!(ALLOWED_TRANSITIONS[o.status] || []).includes('CANCELLED')) return '';
        return `<button type="button" data-cancel-id="${o.id}" class="js-cancel shrink-0 text-xs px-3 py-1 rounded-lg border border-red-300 text-red-600 hover:bg-red-50">Отменить</button>`;
    }

    function deleteButton(o) {
        return `<button type="button" data-delete-id="${o.id}" class="js-delete shrink-0 text-xs px-3 py-1 rounded-lg border border-red-300 text-red-600 hover:bg-red-50">Удалить</button>`;
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

    function orderCard(o, no) {
        const customer = isAdmin
            ? `<span class="text-sm text-gray-500 ml-2">${esc(o.username)}</span>`
            : '';
        const right = isAdmin
            ? `<div class="flex flex-wrap items-center gap-2">${statusControl(o)}${deleteButton(o)}</div>`
            : `<div class="flex flex-wrap items-center gap-2 shrink-0">${statusBadge(o.status)}${cancelButton(o)}</div>`;
        return `
        <div class="bg-white border border-gray-200 rounded-xl p-5">
            <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="min-w-0">
                    <span class="font-semibold">Заказ #${no}</span>
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

    function render() {
        if (!allOrders.length) {
            ordersBox.innerHTML = '';
            if (fCount) fCount.textContent = '';
            emptyBox.classList.remove('hidden');
            return;
        }
        emptyBox.classList.add('hidden');

        let list = allOrders;
        if (isAdmin) {
            const q = fSearch.value.trim().toLowerCase();
            const st = fStatus.value;
            list = allOrders.filter(function (o) {
                if (st && o.status !== st) return false;
                if (q && !(o.username || '').toLowerCase().includes(q)) return false;
                return true;
            });
            fCount.textContent = `Показано: ${list.length} из ${allOrders.length}`;
        }

        if (!list.length) {
            ordersBox.innerHTML = '<p class="text-white [text-shadow:0_2px_10px_rgba(0,0,0,0.8)]">Ничего не найдено.</p>';
            return;
        }

        const total = allOrders.length;
        ordersBox.innerHTML = list.map(function (o) {
            const no = isAdmin ? o.id : total - allOrders.indexOf(o);
            return orderCard(o, no);
        }).join('');
    }

    async function loadOrders() {
        statusBox.textContent = 'Загрузка…';
        emptyBox.classList.add('hidden');
        try {
            allOrders = await apiJson('/orders/');
            statusBox.textContent = '';
            render();
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

    async function cancelOrder(btn) {
        const id = btn.getAttribute('data-cancel-id');
        if (!confirm('Отменить заказ #' + id + '?')) return;
        btn.disabled = true;
        try {
            await apiJson(`/orders/${id}/cancel/`, { method: 'POST', body: JSON.stringify({}) });
            toast('Заказ отменён');
            await loadOrders();
        } catch (err) {
            toast((err.data && err.data.detail) || 'Не удалось отменить заказ.', 'error');
            btn.disabled = false;
        }
    }

    async function deleteOrder(btn) {
        const id = btn.getAttribute('data-delete-id');
        if (!confirm('Удалить заказ #' + id + ' безвозвратно? Остаток на складе не изменится.')) return;
        btn.disabled = true;
        try {
            await apiJson(`/orders/${id}/`, { method: 'DELETE' });
            toast('Заказ удалён');
            await loadOrders();
        } catch (err) {
            toast((err.data && err.data.detail) || 'Не удалось удалить заказ.', 'error');
            btn.disabled = false;
        }
    }

    ordersBox.addEventListener('click', function (e) {
        const cancelBtn = e.target.closest('.js-cancel');
        if (cancelBtn) {
            cancelOrder(cancelBtn);
            return;
        }
        const deleteBtn = e.target.closest('.js-delete');
        if (deleteBtn) deleteOrder(deleteBtn);
    });

    async function init() {
        try {
            const me = await apiJson('/users/me/');
            isAdmin = me.role === 'ADMIN';
        } catch (e) {
            isAdmin = false;
        }
        if (isAdmin) {
            if (titleEl) titleEl.textContent = 'Все заказы';
            if (emptyBox) {
                const p = emptyBox.querySelector('p');
                if (p) p.textContent = 'Заказов пока нет.';
            }
            adminFilters.classList.remove('hidden');
            fSearch.addEventListener('input', render);
            fStatus.addEventListener('change', render);
        }
        await loadOrders();
    }

    init();
})();
