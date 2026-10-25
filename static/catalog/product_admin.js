(function () {
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    ready(function () {
        var select = document.getElementById('id_product_type');
        if (!select) return;
        var book = document.querySelector('fieldset.book-fields');
        var periodical = document.querySelector('fieldset.periodical-fields');

        function update() {
            var value = select.value;
            if (book) book.style.display = value === 'BOOK' ? '' : 'none';
            if (periodical) {
                periodical.style.display = (value === 'MAGAZINE' || value === 'NEWSPAPER') ? '' : 'none';
            }
        }

        select.addEventListener('change', update);
        update();
    });
})();
