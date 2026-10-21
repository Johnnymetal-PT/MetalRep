/** @odoo-module alias=theme_alan.alan_select_search */
import { rpc } from "@web/core/network/rpc";
import { debounce } from "@web/core/utils/timing";

/**
 * Fetch data for one or more models.
 */
export async function fetchData(term, models = [], options = {}) {
    try {
        const modelList = Array.isArray(models) ? models : [models];
        const response = await rpc("/select/data/fetch", {
            terms: term,
            searchIn: JSON.stringify(modelList),
            ...(options.extraParams || {}),
        });
        return (response || []).map((item) => ({
            id: item.id,
            name: item.name,
            image: item.image || null,
            extra: item.extra || null,
        }));
    } catch (error) {
        console.error("fetchData error:", error);
        return [];
    }
}

function defaultRenderItem(item, onSelect) {
    const li = document.createElement("li");
    li.className = "p-2 cursor-pointer alan-select-item d-flex align-items-center";
    li.style.borderBottom = "1px solid #eee";
    li.onmouseover = () => (li.style.backgroundColor = "#f0f0f0");
    li.onmouseout = () => (li.style.backgroundColor = "");
    // Use mousedown so it fires before the input's blur event hides the dropdown
    li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        onSelect(item);
    });

    if (item.image) {
        const img = document.createElement("img");
        img.src = item.image;
        img.alt = item.name;
        img.className = "me-2 rounded";
        img.style.width = "40px";
        img.style.height = "40px";
        img.style.objectFit = "cover";
        li.appendChild(img);
    }

    const span = document.createElement("span");
    span.textContent = item.name;
    li.appendChild(span);
    return li;
}

export class AlanSelectSearch {
    constructor(inputEl, model, onSelect, options = {}) {
        if (!inputEl) {
            console.error("AlanSelectSearch: Input element not found.");
            return;
        }

        this.inputEl = inputEl;
        this.model = model;
        this.onSelectCallback = onSelect;
        this.options = options;
        this.fetcher = options.fetcher || ((term, models) => fetchData(term, models, this.options));
        this.renderItem = options.renderItem || defaultRenderItem;
        this.debounceTime = options.debounceTime || 300;

        this.dropdown = null;
        this.debouncedSearch = null;
        this._hideHandler = null;

        this._init();
    }

    _init() {
        // Create dropdown element
        this.dropdown = document.createElement("ul");
        this.dropdown.className = "alan-select-dropdown position-absolute bg-white border shadow-sm rounded top-100 w-100";
        this.dropdown.style.listStyle = "none";
        this.dropdown.style.padding = "0";
        this.dropdown.style.margin = "0";
        this.dropdown.style.maxHeight = "200px";
        this.dropdown.style.overflowY = "auto";
        this.dropdown.style.zIndex = "9999";
        this.dropdown.style.display = "none";

        const wrapper = this.inputEl.closest(".alan-search-wrapper") || this.inputEl.parentNode;
        if (getComputedStyle(wrapper).position === "static") {
            wrapper.style.position = "relative";
        }
        wrapper.appendChild(this.dropdown);

        // Attach debounced search on every input event
        this.debouncedSearch = debounce(this._performSearch.bind(this), this.debounceTime);
        this.inputEl.addEventListener("input", this.debouncedSearch);

        // Hide dropdown on outside click
        this._hideHandler = (ev) => {
            if (this.dropdown && !this.dropdown.contains(ev.target) && ev.target !== this.inputEl) {
                this.dropdown.style.display = "none";
            }
        };
        document.addEventListener("click", this._hideHandler);

        // Start with empty input
        this.inputEl.value = "";
    }

    handleSelect(item) {
        // Notify the caller with the selected record
        if (this.onSelectCallback) {
            this.onSelectCallback(item);
        }
        // Clear input and hide dropdown — search is immediately ready for next query
        this.inputEl.value = "";
        if (this.dropdown) {
            this.dropdown.style.display = "none";
            this.dropdown.innerHTML = "";
        }
        this.inputEl.focus();
    }

    _renderNoResults() {
        const li = document.createElement("li");
        li.className = "p-2 text-muted alan-select-no-results";
        li.textContent = "No results found.";
        li.style.userSelect = "none";
        li.style.cursor = "default";
        return li;
    }

    renderDropdown(items) {
        if (!this.dropdown) return;
        this.dropdown.innerHTML = "";
        if (!items || !items.length) {
            this.dropdown.appendChild(this._renderNoResults());
            this.dropdown.style.display = "block";
            return;
        }
        items.forEach((item) => {
            const li = this.renderItem(item, this.handleSelect.bind(this));
            this.dropdown.appendChild(li);
        });
        this.dropdown.style.display = "block";
    }

    async _performSearch(ev) {
        if (!this.dropdown) return;
        const term = ev.target.value.trim();
        if (term.length < 1) {
            this.dropdown.style.display = "none";
            return;
        }
        const items = await this.fetcher(term, this.model);
        if (!this.dropdown) return;
        this.renderDropdown(items);
    }

    destroy() {
        if (this.debouncedSearch) {
            this.inputEl.removeEventListener("input", this.debouncedSearch);
            this.debouncedSearch = null;
        }
        if (this._hideHandler) {
            document.removeEventListener("click", this._hideHandler);
            this._hideHandler = null;
        }
        if (this.dropdown && this.dropdown.parentNode) {
            this.dropdown.parentNode.removeChild(this.dropdown);
        }
        this.dropdown = null;
    }
}