/** @odoo-module **/

function getFirstVisibleOption(select) {
    return Array.from(select.options).find(
        (opt) => !opt.hidden && !opt.disabled && opt.style.display !== "none"
    );
}

function getEffectiveSelectedOption(select) {
    const selected = select.options[select.selectedIndex];
    const selectedIsVisible =
        selected && !selected.hidden && !selected.disabled && selected.style.display !== "none";
    if (selectedIsVisible) {
        return selected;
    }
    const fallback = getFirstVisibleOption(select);
    if (fallback) {
        select.value = fallback.value;
    }
    return fallback || null;
}

function updateVisibility(wrapper) {
    const select = wrapper.querySelector(".pg_attr_hidden_select");
    const items = wrapper.querySelectorAll(".pg_attr_dropdown_item");
    if (!select || !items.length) {
        return;
    }
    const optionsByValue = new Map(Array.from(select.options).map((opt) => [opt.value, opt]));
    for (const item of items) {
        const option = optionsByValue.get(item.dataset.valueId);
        const isHidden = !option || option.hidden || option.disabled || option.style.display === "none";
        item.classList.toggle("d-none", isHidden);
    }
}

function updateSelectedState(wrapper) {
    const select = wrapper.querySelector(".pg_attr_hidden_select");
    const label = wrapper.querySelector(".pg_attr_dropdown_value_label");
    const img = wrapper.querySelector(".pg_attr_dropdown_value_img");
    const items = wrapper.querySelectorAll(".pg_attr_dropdown_item");
    if (!select || !label || !img) {
        return;
    }

    const selectedOption = getEffectiveSelectedOption(select);
    if (!selectedOption) {
        return;
    }
    const selectedValue = selectedOption.value;
    const selectedLabel = selectedOption.dataset.valueName || selectedOption.textContent.trim() || "Select...";
    label.textContent = selectedLabel;

    let selectedImage = selectedOption.dataset.imageUrl || "";
    for (const item of items) {
        const isActive = item.dataset.valueId === selectedValue;
        item.classList.toggle("active", isActive);
        if (isActive && item.dataset.imageUrl) {
            selectedImage = item.dataset.imageUrl;
        }
    }

    if (selectedImage) {
        img.src = selectedImage;
        img.classList.remove("d-none");
    } else {
        img.removeAttribute("src");
        img.classList.add("d-none");
    }
}

function closeDropdown(wrapper) {
    const dropdown = wrapper.querySelector(".pg_attr_image_dropdown");
    const toggle = wrapper.querySelector(".pg_attr_dropdown_toggle");
    const menu = wrapper.querySelector(".pg_attr_dropdown_menu");
    if (!dropdown || !toggle || !menu) {
        return;
    }
    if (window.bootstrap?.Dropdown) {
        const instance =
            window.bootstrap.Dropdown.getInstance(toggle) ||
            window.bootstrap.Dropdown.getOrCreateInstance(toggle);
        instance.hide();
        return;
    }
    dropdown.classList.remove("show");
    menu.classList.remove("show");
    toggle.setAttribute("aria-expanded", "false");
}

function initWrapper(wrapper) {
    if (!wrapper || wrapper.dataset.pgDropdownInit === "1") {
        return;
    }
    wrapper.dataset.pgDropdownInit = "1";

    const select = wrapper.querySelector(".pg_attr_hidden_select");
    const toggle = wrapper.querySelector(".pg_attr_dropdown_toggle");
    const items = wrapper.querySelectorAll(".pg_attr_dropdown_item");
    if (!select || !toggle || !items.length) {
        return;
    }

    for (const item of items) {
        item.addEventListener("click", (ev) => {
            ev.preventDefault();
            const valueId = item.dataset.valueId;
            if (!valueId) {
                return;
            }
            if (select.value !== valueId) {
                select.value = valueId;
                select.dispatchEvent(new Event("change", { bubbles: true }));
            } else {
                updateSelectedState(wrapper);
            }
            closeDropdown(wrapper);
        });
    }

    select.addEventListener("change", () => {
        updateVisibility(wrapper);
        updateSelectedState(wrapper);
    });

    const observer = new MutationObserver(() => {
        updateVisibility(wrapper);
        updateSelectedState(wrapper);
    });
    observer.observe(select, {
        attributes: true,
        childList: true,
        subtree: true,
        attributeFilter: ["style", "disabled", "hidden", "selected"],
    });

    updateVisibility(wrapper);
    updateSelectedState(wrapper);
    // Re-apply after website_sale variant scripts update selects on load/hash change.
    setTimeout(() => {
        updateVisibility(wrapper);
        updateSelectedState(wrapper);
    }, 0);
}

function initAllWrappers(root = document) {
    const wrappers = root.querySelectorAll(".pg_attr_dropdown_wrapper");
    for (const wrapper of wrappers) {
        initWrapper(wrapper);
    }
}

initAllWrappers(document);
document.addEventListener("DOMContentLoaded", () => {
    initAllWrappers(document);
    const bodyObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const addedNode of mutation.addedNodes) {
                if (!(addedNode instanceof Element)) {
                    continue;
                }
                if (addedNode.matches(".pg_attr_dropdown_wrapper")) {
                    initWrapper(addedNode);
                } else {
                    initAllWrappers(addedNode);
                }
            }
        }
    });
    bodyObserver.observe(document.body, { childList: true, subtree: true });
});
