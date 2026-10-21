// Remove a categoria raiz tecnica "Todas" dos menus publicos, mantendo os filhos navegaveis.
odoo.define('pg_web_attach_pdf_view.hide_todas', [], function () {
    'use strict';

    function normalizeText(text) {
        return (text || '').trim().toLowerCase();
    }

    function removeTodasLinks() {
        const links = document.querySelectorAll('a');
        links.forEach((link) => {
            if (normalizeText(link.textContent) === 'todas') {
                const li = link.closest('li');
                if (li) {
                    const childList = li.querySelector('ul');
                    const parentList = li.parentElement;
                    if (childList && parentList) {
                        while (childList.firstElementChild) {
                            parentList.insertBefore(childList.firstElementChild, li);
                        }
                    }
                    li.remove();
                    return;
                }
                link.remove();
            }
        });

        const options = document.querySelectorAll('select option');
        options.forEach((opt) => {
            if (normalizeText(opt.textContent) === 'todas') {
                opt.remove();
            }
        });
    }

    function init() {
        removeTodasLinks();
        const observer = new MutationObserver(() => {
            removeTodasLinks();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
});
