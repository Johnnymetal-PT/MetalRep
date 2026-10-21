/** @odoo-module **/

function isDesktopMenuCandidate(node) {
    if (!(node instanceof HTMLElement)) {
        return false;
    }
    if (node.matches('.top_menu, .o_header_mobile_buttons_wrap, .o_navbar_mobile .navbar-nav')) {
        return false;
    }
    if (node.closest('.o_navbar_mobile')) {
        return false;
    }
    if (!node.matches('ul.navbar-nav')) {
        return false;
    }
    return !!node.querySelector(':scope > li.nav-item, :scope > li.dropdown');
}

document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header#top');
    if (!header || header.querySelector('.top_menu')) {
        return;
    }

    const mainNav = header.querySelector('#o_main_nav, .o_main_nav');
    const topMenu = mainNav
        ? [...mainNav.querySelectorAll('ul.navbar-nav')].find(isDesktopMenuCandidate)
        : null;

    if (topMenu) {
        topMenu.classList.add('top_menu');
        if (!topMenu.id) {
            topMenu.id = 'top_menu';
        }
        return;
    }

    header.classList.add('o_no_autohide_menu');
});

