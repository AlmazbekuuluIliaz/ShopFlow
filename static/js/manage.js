(function () {
    if (!Session.requireAuth()) return;

    const denied = document.getElementById('denied');
    const panel = document.getElementById('panel');

    const catForm = document.getElementById('catForm');
    const cId = document.getElementById('cId');
    const cName = document.getElementById('cName');
    const cSlug = document.getElementById('cSlug');
    const cSubmit = document.getElementById('cSubmit');
    const cCancel = document.getElementById('cCancel');
    const catStatus = document.getElementById('catStatus');
    const catList = document.getElementById('catList');

    const prodForm = document.getElementById('prodForm');
    const pId = document.getElementById('pId');
    const pCategory = document.getElementById('pCategory');
    const pType = document.getElementById('pType');
    const pName = document.getElementById('pName');
    const pSlug = document.getElementById('pSlug');
    const pPrice = document.getElementById('pPrice');
    const pStock = document.getElementById('pStock');
    const pAvailable = document.getElementById('pAvailable');
    const pAuthor = document.getElementById('pAuthor');
    const pPublisher = document.getElementById('pPublisher');
    const pLanguage = document.getElementById('pLanguage');
    const pMediaFormat = document.getElementById('pMediaFormat');
    const pAgeRating = document.getElementById('pAgeRating');
    const pCoverType = document.getElementById('pCoverType');
    const pYear = document.getElementById('pYear');
    const pPages = document.getElementById('pPages');
    const pIsbn = document.getElementById('pIsbn');
    const pIssn = document.getElementById('pIssn');
    const pIssueNumber = document.getElementById('pIssueNumber');
    const pIssueDate = document.getElementById('pIssueDate');
    const pDescription = document.getElementById('pDescription');
    const pImage = document.getElementById('pImage');
    const pImageHint = document.getElementById('pImageHint');
    const pSubmit = document.getElementById('pSubmit');
    const pCancel = document.getElementById('pCancel');
    const prodStatus = document.getElementById('prodStatus');
    const prodList = document.getElementById('prodList');
    const prodSort = document.getElementById('prodSort');
    const prodCount = document.getElementById('prodCount');
    const bookFields = document.getElementById('bookFields');
    const periodicalFields = document.getElementById('periodicalFields');

    const categoryMap = {};
    const productMap = {};
    let productsCache = [];

    function slugify(value) {
        return String(value).toLowerCase().trim()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    function errText(err, fallback) {
        if (err && err.data) {
            if (typeof err.data === 'string') return err.data;
            if (err.data.detail) return err.data.detail;
            const parts = [];
            Object.keys(err.data).forEach(function (k) {
                const v = err.data[k];
                parts.push(`${k}: ${Array.isArray(v) ? v.join(' ') : v}`);
            });
            if (parts.length) return parts.join('; ');
        }
        return fallback;
    }

    function autoSlug(nameEl, slugEl) {
        nameEl.addEventListener('blur', function () {
            if (!slugEl.value.trim()) {
                const s = slugify(nameEl.value);
                if (s) slugEl.value = s;
            }
        });
    }

    async function fetchAllProducts() {
        let all = [];
        let page = 1;
        while (true) {
            const data = await apiJson(`/products/?page=${page}`);
            all = all.concat(data.results);
            if (!data.next) break;
            page += 1;
        }
        return all;
    }

    function catRow(c) {
        return `
        <div class="flex items-center justify-between gap-3 py-3">
            <div class="min-w-0">
                <span class="font-medium">${esc(c.name)}</span>
                <span class="text-sm text-gray-400 ml-2">${esc(c.slug)}</span>
            </div>
            <div class="flex gap-2 shrink-0">
                <button type="button" data-edit-cat="${c.id}" class="text-sm text-indigo-600 hover:underline">Изменить</button>
                <button type="button" data-del-cat="${c.id}" class="text-sm text-red-600 hover:underline">Удалить</button>
            </div>
        </div>`;
    }

    const TYPE_LABELS = { BOOK: 'Книга', MAGAZINE: 'Журнал', NEWSPAPER: 'Газета' };

    function prodRow(p) {
        const img = p.image
            ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" class="w-12 h-12 rounded-lg object-cover bg-gray-100 shrink-0" onerror="this.style.display='none'">`
            : `<div class="w-12 h-12 rounded-lg bg-gray-100 shrink-0"></div>`;
        const cat = categoryMap[p.category] || '—';
        const type = TYPE_LABELS[p.product_type] || p.product_type || '';
        const avail = p.available
            ? '<span class="text-xs text-green-700">в продаже</span>'
            : '<span class="text-xs text-gray-400">скрыт</span>';
        const name = esc(p.name);
        return `
        <div class="flex items-center gap-3 py-3">
            ${img}
            <div class="min-w-0 flex-1">
                <div class="font-medium truncate">${name}</div>
                <div class="text-sm text-gray-500">${esc(type)} · ${esc(cat)} · ${esc(formatPrice(p.price))} · остаток ${esc(p.stock)} · ${avail}</div>
            </div>
            <div class="flex gap-2 shrink-0">
                <button type="button" data-edit-prod="${p.id}" class="text-sm text-indigo-600 hover:underline">Изменить</button>
                <button type="button" data-del-prod="${p.id}" class="text-sm text-red-600 hover:underline">Удалить</button>
            </div>
        </div>`;
    }

    async function loadCategories() {
        catStatus.textContent = 'Загрузка…';
        try {
            const categories = await apiJson('/categories/');
            for (const key in categoryMap) delete categoryMap[key];
            pCategory.innerHTML = '';
            categories.forEach(function (c) {
                categoryMap[c.id] = c.name;
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name;
                pCategory.appendChild(opt);
            });
            catStatus.textContent = '';
            catList.innerHTML = categories.length
                ? categories.map(catRow).join('')
                : '<p class="text-sm text-gray-400 py-3">Категорий пока нет.</p>';
        } catch (e) {
            catStatus.textContent = 'Не удалось загрузить категории.';
        }
    }

    const TYPE_ORDER = { BOOK: 0, MAGAZINE: 1, NEWSPAPER: 2 };

    function sortedProducts() {
        const list = productsCache.slice();
        const by = prodSort.value;
        const cmpName = function (a, b) { return a.name.localeCompare(b.name, 'ru'); };
        const num = function (v) { return Number(v) || 0; };
        switch (by) {
            case 'created_asc': list.reverse(); break;
            case 'name_asc': list.sort(cmpName); break;
            case 'name_desc': list.sort(function (a, b) { return cmpName(b, a); }); break;
            case 'price_asc': list.sort(function (a, b) { return num(a.price) - num(b.price); }); break;
            case 'price_desc': list.sort(function (a, b) { return num(b.price) - num(a.price); }); break;
            case 'stock_asc': list.sort(function (a, b) { return num(a.stock) - num(b.stock); }); break;
            case 'stock_desc': list.sort(function (a, b) { return num(b.stock) - num(a.stock); }); break;
            case 'type': list.sort(function (a, b) {
                const d = (TYPE_ORDER[a.product_type] ?? 9) - (TYPE_ORDER[b.product_type] ?? 9);
                return d !== 0 ? d : cmpName(a, b);
            }); break;
            default: break;
        }
        return list;
    }

    function renderProducts() {
        const list = sortedProducts();
        prodCount.textContent = list.length ? `Всего: ${list.length}` : '';
        prodList.innerHTML = list.length
            ? list.map(prodRow).join('')
            : '<p class="text-sm text-gray-400 py-3">Товаров пока нет.</p>';
    }

    async function loadProducts() {
        prodStatus.textContent = 'Загрузка…';
        try {
            productsCache = await fetchAllProducts();
            for (const key in productMap) delete productMap[key];
            productsCache.forEach(function (p) { productMap[p.id] = p; });
            prodStatus.textContent = '';
            renderProducts();
        } catch (e) {
            prodStatus.textContent = 'Не удалось загрузить товары.';
        }
    }

    function resetCatForm() {
        cId.value = '';
        catForm.reset();
        cSubmit.textContent = 'Добавить';
        cCancel.classList.add('hidden');
    }

    function startEditCat(c) {
        cId.value = c.id;
        cName.value = c.name;
        cSlug.value = c.slug;
        cSubmit.textContent = 'Сохранить';
        cCancel.classList.remove('hidden');
        cName.focus();
    }

    catForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const payload = { name: cName.value.trim(), slug: cSlug.value.trim() };
        const id = cId.value;
        try {
            if (id) {
                await apiJson(`/categories/${id}/`, { method: 'PUT', body: JSON.stringify(payload) });
                toast('Категория обновлена');
            } else {
                await apiJson('/categories/', { method: 'POST', body: JSON.stringify(payload) });
                toast('Категория добавлена');
            }
            resetCatForm();
            await loadCategories();
            await loadProducts();
        } catch (err) {
            toast(errText(err, 'Не удалось сохранить категорию.'), 'error');
        }
    });

    cCancel.addEventListener('click', resetCatForm);

    catList.addEventListener('click', async function (e) {
        const editBtn = e.target.closest('[data-edit-cat]');
        if (editBtn) {
            const id = editBtn.getAttribute('data-edit-cat');
            const name = categoryMap[id];
            try {
                const c = await apiJson(`/categories/${id}/`);
                startEditCat(c);
            } catch (err) {
                toast('Не удалось открыть категорию.', 'error');
            }
            return;
        }
        const delBtn = e.target.closest('[data-del-cat]');
        if (delBtn) {
            const id = delBtn.getAttribute('data-del-cat');
            if (!confirm(`Удалить категорию «${categoryMap[id] || id}»?`)) return;
            try {
                await apiJson(`/categories/${id}/`, { method: 'DELETE' });
                toast('Категория удалена');
                await loadCategories();
                await loadProducts();
            } catch (err) {
                toast(errText(err, 'Не удалось удалить категорию.'), 'error');
            }
        }
    });

    function clearGroup(container) {
        container.querySelectorAll('input').forEach(function (el) {
            if (el.type === 'checkbox') el.checked = false;
            else el.value = '';
        });
        container.querySelectorAll('select').forEach(function (el) {
            el.selectedIndex = 0;
        });
    }

    function updateTypeFields() {
        const t = pType.value;
        const bookVisible = t === 'BOOK';
        const periodicalVisible = t === 'MAGAZINE' || t === 'NEWSPAPER';
        bookFields.classList.toggle('hidden', !bookVisible);
        periodicalFields.classList.toggle('hidden', !periodicalVisible);
        if (!bookVisible) clearGroup(bookFields);
        if (!periodicalVisible) clearGroup(periodicalFields);
    }

    function resetProdForm() {
        pId.value = '';
        prodForm.reset();
        pAvailable.checked = true;
        pSubmit.textContent = 'Добавить товар';
        pCancel.classList.add('hidden');
        pImageHint.classList.add('hidden');
        updateTypeFields();
    }

    function startEditProd(p) {
        pId.value = p.id;
        pCategory.value = p.category;
        pType.value = p.product_type || '';
        pName.value = p.name;
        pSlug.value = p.slug;
        pPrice.value = p.price;
        pStock.value = p.stock;
        pAvailable.checked = p.available;
        pAuthor.value = p.author || '';
        pPublisher.value = p.publisher || '';
        pLanguage.value = p.language || '';
        pMediaFormat.value = p.media_format || 'PRINT';
        pAgeRating.value = p.age_rating || '';
        pCoverType.value = p.cover_type || '';
        pYear.value = p.publication_year || '';
        pPages.value = p.pages || '';
        pIsbn.value = p.isbn || '';
        pIssn.value = p.issn || '';
        pIssueNumber.value = p.issue_number || '';
        pIssueDate.value = p.issue_date || '';
        pDescription.value = p.description || '';
        pImage.value = '';
        pSubmit.textContent = 'Сохранить';
        pCancel.classList.remove('hidden');
        pImageHint.classList.remove('hidden');
        updateTypeFields();
        prodForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    prodForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const fd = new FormData();
        fd.append('category', pCategory.value);
        fd.append('product_type', pType.value);
        fd.append('name', pName.value.trim());
        fd.append('slug', pSlug.value.trim());
        fd.append('description', pDescription.value);
        fd.append('price', pPrice.value);
        fd.append('stock', pStock.value || '0');
        fd.append('available', pAvailable.checked ? 'true' : 'false');
        fd.append('author', pAuthor.value.trim());
        fd.append('publisher', pPublisher.value.trim());
        fd.append('language', pLanguage.value.trim());
        fd.append('media_format', pMediaFormat.value);
        fd.append('age_rating', pAgeRating.value);
        fd.append('cover_type', pCoverType.value);
        fd.append('isbn', pIsbn.value.trim());
        fd.append('issn', pIssn.value.trim());
        fd.append('issue_number', pIssueNumber.value.trim());
        if (pYear.value) fd.append('publication_year', pYear.value);
        if (pPages.value) fd.append('pages', pPages.value);
        if (pIssueDate.value) fd.append('issue_date', pIssueDate.value);
        if (pImage.files[0]) fd.append('image', pImage.files[0]);

        const id = pId.value;
        try {
            if (id) {
                await apiJson(`/products/${id}/`, { method: 'PUT', body: fd });
                toast('Товар обновлён');
            } else {
                await apiJson('/products/', { method: 'POST', body: fd });
                toast('Товар добавлен');
            }
            resetProdForm();
            await loadProducts();
        } catch (err) {
            toast(errText(err, 'Не удалось сохранить товар.'), 'error');
        }
    });

    pCancel.addEventListener('click', resetProdForm);

    prodList.addEventListener('click', async function (e) {
        const editBtn = e.target.closest('[data-edit-prod]');
        if (editBtn) {
            const id = editBtn.getAttribute('data-edit-prod');
            const p = productMap[id];
            if (p) startEditProd(p);
            return;
        }
        const delBtn = e.target.closest('[data-del-prod]');
        if (delBtn) {
            const id = delBtn.getAttribute('data-del-prod');
            const p = productMap[id];
            if (!confirm(`Удалить товар «${p ? p.name : id}»?`)) return;
            try {
                await apiJson(`/products/${id}/`, { method: 'DELETE' });
                toast('Товар удалён');
                await loadProducts();
            } catch (err) {
                toast(errText(err, 'Не удалось удалить товар.'), 'error');
            }
        }
    });

    autoSlug(cName, cSlug);
    autoSlug(pName, pSlug);

    pType.addEventListener('change', updateTypeFields);
    updateTypeFields();

    prodSort.addEventListener('change', renderProducts);

    async function init() {
        try {
            const me = await apiJson('/users/me/');
            if (me.role !== 'ADMIN') {
                denied.classList.remove('hidden');
                return;
            }
        } catch (e) {
            denied.classList.remove('hidden');
            return;
        }
        panel.classList.remove('hidden');
        await loadCategories();
        await loadProducts();
    }

    init();
})();
