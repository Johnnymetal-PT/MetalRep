/** @odoo-module **/

const LAZY_SELECTOR = "img.o_pg_lazy_attr_value_img[data-src]";

function revealImage(img) {
    const src = img.dataset.src;
    if (!src || img.dataset.loaded === "1") {
        return;
    }
    img.src = src;
    img.dataset.loaded = "1";
}

function setupLazyLoading(root) {
    const images = Array.from(root.querySelectorAll(LAZY_SELECTOR));
    if (!images.length) {
        return;
    }

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries, obs) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        revealImage(entry.target);
                        obs.unobserve(entry.target);
                    }
                }
            },
            {
                root: null,
                rootMargin: "200px 0px",
                threshold: 0.01,
            }
        );

        for (const img of images) {
            observer.observe(img);
        }
    } else {
        for (const img of images.slice(0, 30)) {
            revealImage(img);
        }
    }
}

function bootstrap() {
    setupLazyLoading(document);

    const mutationObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (!(node instanceof HTMLElement)) {
                    continue;
                }
                if (node.matches?.(LAZY_SELECTOR) || node.querySelector?.(LAZY_SELECTOR)) {
                    setupLazyLoading(node);
                }
            }
        }
    });

    mutationObserver.observe(document.body, {
        childList: true,
        subtree: true,
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
} else {
    bootstrap();
}
