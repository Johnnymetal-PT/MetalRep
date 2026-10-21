/** @odoo-module **/
window.__hmdTagLinkLoaded = true;

function normalizeProjectUrl(rawUrl) {
    const cleaned = (rawUrl || '').trim();
    if (!cleaned) {
        return '';
    }
    if (cleaned.startsWith('/') || cleaned.startsWith('http://') || cleaned.startsWith('https://')) {
        return cleaned;
    }
    return `/${cleaned}`;
}

function collectTagUrlsFromDom() {
    const mapping = {};
    const hiddenRoot = document.getElementById('hmd_tag_project_urls');
    if (!hiddenRoot) {
        return mapping;
    }
    hiddenRoot.querySelectorAll('span[data-tag-name][data-project-url]').forEach((node) => {
        const tagName = (node.dataset.tagName || '').trim();
        const url = normalizeProjectUrl(node.dataset.projectUrl || '');
        if (tagName && url) {
            mapping[tagName] = url;
        }
    });
    return mapping;
}

function markTagNodesClickable(urlByTagName, rootNode) {
    const root = rootNode || document;
    const selectors = [
        '.o_product_tags .badge',
        '.o_product_tags .o_tag_badge',
        '.o_product_tags .text-nowrap',
    ].join(', ');

    root.querySelectorAll(selectors).forEach((tagNode) => {
        if (!tagNode || tagNode.closest('a')) {
            return;
        }
        const tagName = (tagNode.textContent || '').trim();
        const url = urlByTagName[tagName];
        if (!url) {
            return;
        }
        tagNode.dataset.hmdProjectUrl = url;
        tagNode.style.cursor = 'pointer';
        tagNode.style.pointerEvents = 'auto';
        tagNode.setAttribute('role', 'link');
        if (!tagNode.hasAttribute('tabindex')) {
            tagNode.setAttribute('tabindex', '0');
        }

        if (!tagNode.dataset.hmdProjectBound) {
            tagNode.dataset.hmdProjectBound = '1';
            tagNode.addEventListener('click', (event) => {
                const targetUrl = tagNode.dataset.hmdProjectUrl;
                if (!targetUrl) {
                    return;
                }
                event.preventDefault();
                event.stopPropagation();
                window.location.href = targetUrl;
            }, true);

            tagNode.addEventListener('keydown', (event) => {
                if (event.key !== 'Enter' && event.key !== ' ') {
                    return;
                }
                const targetUrl = tagNode.dataset.hmdProjectUrl;
                if (!targetUrl) {
                    return;
                }
                event.preventDefault();
                event.stopPropagation();
                window.location.href = targetUrl;
            }, true);
        }
    });
}

function bindGlobalTagClick() {
    if (window.__hmdTagProjectClickBound) {
        return;
    }
    window.__hmdTagProjectClickBound = true;

    const goToUrl = (eventTarget) => {
        const baseTarget = eventTarget instanceof Element ? eventTarget : eventTarget && eventTarget.parentElement;
        if (!baseTarget) {
            return false;
        }
        const tagNode = baseTarget.closest('[data-hmd-project-url]');
        if (!tagNode) {
            return false;
        }
        const url = tagNode.dataset.hmdProjectUrl;
        if (!url) {
            return false;
        }
        window.location.href = url;
        return true;
    };

    document.addEventListener('click', (event) => {
        if (goToUrl(event.target)) {
            event.preventDefault();
            event.stopPropagation();
        }
    }, true);

    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        if (goToUrl(event.target)) {
            event.preventDefault();
            event.stopPropagation();
        }
    }, true);
}

async function fetchTagUrls(productTemplateId) {
    const response = await fetch(`/hmd/product_tag_project_urls/${productTemplateId}`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
    });
    if (!response.ok) {
        return {};
    }
    const payload = await response.json();
    return (payload && payload.tag_urls) || {};
}

function startTagObserver(urlByTagName) {
    const wrap = document.getElementById('wrap') || document.body;
    if (!wrap) {
        return;
    }

    let scheduled = false;
    const reapply = () => {
        if (scheduled) {
            return;
        }
        scheduled = true;
        window.requestAnimationFrame(() => {
            markTagNodesClickable(urlByTagName, wrap);
            scheduled = false;
        });
    };

    const observer = new MutationObserver(reapply);
    observer.observe(wrap, { childList: true, subtree: true });

    // Covers late DOM swaps done shortly after load.
    let attempts = 0;
    const timer = window.setInterval(() => {
        markTagNodesClickable(urlByTagName, wrap);
        attempts += 1;
        if (attempts >= 20) {
            window.clearInterval(timer);
        }
    }, 300);
}

async function makeProductTagsClickable() {
    const productTemplateInput = document.querySelector('#product_details input.product_template_id');
    if (!productTemplateInput) {
        return;
    }

    const productTemplateId = parseInt(productTemplateInput.value, 10);
    if (!productTemplateId) {
        return;
    }

    bindGlobalTagClick();

    let urlByTagName = collectTagUrlsFromDom();
    if (!Object.keys(urlByTagName).length) {
        try {
            urlByTagName = await fetchTagUrls(productTemplateId);
        } catch (_error) {
            urlByTagName = {};
        }
    }

    if (!Object.keys(urlByTagName).length) {
        return;
    }

    markTagNodesClickable(urlByTagName, document);
    startTagObserver(urlByTagName);
}

document.addEventListener('DOMContentLoaded', makeProductTagsClickable);
