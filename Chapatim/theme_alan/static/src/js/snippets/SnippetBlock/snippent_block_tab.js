
import { closest } from "@web/core/utils/ui";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { BlockTab } from "@html_builder/sidebar/block_tab";
import { SnippetBuilder } from "../SnippetBuilder/SnippetBuilder";
import { useDragAndDrop } from "@html_editor/utils/drag_and_drop";
import { getCSSVariableValue } from "@html_editor/utils/formatting";
import { WebsiteBuilder } from "../WebsiteBuilder/website_builder_dialog";
import { HomePageDemoWizard } from "../HomePageDemo/HomePageDemo";
import { closestScrollableY, getScrollingElement, isScrollableY } from "@web/core/utils/scrolling";

// ─── Add Alan Website Builder/ Dynamic Snippets Block Tab ───────────────────────────────────────────
patch(BlockTab.prototype, {
    openSnippetDialog(snippet, snippetEl) {
        if (snippet.name == "as_snippet_builder") {
            const snippet_type = snippetEl.getAttribute("data-as-snippet") || "";
            const DynamicSnippetLists = registry.category("snippet_builder").get("as_snippet_tabs");
            const MegamenuSnippetLists = registry.category("snippet_builder").get("as_megamenu_snippet_tabs");
            const SnippetLists = snippet_type === "as_mega_menu" ? MegamenuSnippetLists : DynamicSnippetLists;
            const config_data = undefined;
            this.dialog.add(SnippetBuilder, {
                snippets: SnippetLists,
                target: snippetEl,
                config_data: config_data,
                record_ids: [],
                snippet_type: snippet_type,
            });
        }
        else if (snippet.name == "as_home_page_demo") {
            this.dialog.add(HomePageDemoWizard, {
                snippetEl: snippetEl,
            });
        }
        else {
            const SnippetTabs = registry.category("website_builder").get("as_snippet_categories");
            this.dialog.add(WebsiteBuilder, {
                tabs: SnippetTabs,
                snippet: snippet,
                snippetEl: snippetEl,
                confirm: () => resolve(true),
                cancel: () => resolve(false),
            })
        }
    },


    insertSnippetAtClosestDropzone(snippet, snippetEl) {
        const baseSectionEl = snippet.content.cloneNode(true);
        const selectors = this.shared.dropzone.getSelectors(baseSectionEl);
        const dropzoneEls =
            this.shared.dropzone.activateDropzones(selectors);
        this.editable
            .querySelectorAll(".oe_drop_zone")
            .forEach((dropzoneEl) => dropzoneEl.classList.add("invisible"));

        const iframeWindow = this.document.defaultView;
        const viewPortCenterPoint = {
            x: iframeWindow.innerWidth / 2,
            y: iframeWindow.innerHeight / 2,
        };
        const validDropzoneEls = dropzoneEls.filter(
            (el) =>
                el.getBoundingClientRect().top >= viewPortCenterPoint.y / 2
        );
        const closestDropzoneEl =
            closest(validDropzoneEls, viewPortCenterPoint) ||
            dropzoneEls.at(-1);

        // Insert the selected snippet.
        closestDropzoneEl.after(snippetEl);
        this.shared.dropzone.removeDropzones();
        this.openSnippetDialog(snippet, snippetEl);
        return snippetEl
    },

    makeSnippetDraggable() {
        let dropzoneEls = [];
        let dragAndDropResolve;

        let snippet, snippetEl, isSnippetGroup, isAlanSnippetBlock;
        const iframeWindow =
            this.document.defaultView !== window ? this.document.defaultView : false;

        const scrollingElement = () => {
            let scrollingElement =
                this.shared.dropzone.getDropRootElement() ||
                getScrollingElement(this.document) ||
                this.editable.querySelector(".o_editable");
            if (!isScrollableY(scrollingElement)) {
                scrollingElement =
                    closestScrollableY(this.document.defaultView.frameElement) ?? scrollingElement;
            }
            return scrollingElement;
        };

        const dragAndDropOptions = {
            ref: { el: this.blockTabRef.el },
            iframeWindow,
            cursor: "move",
            el: this.blockTabRef.el,
            elements: ".o_snippet.o_draggable",
            scrollingElement,
            handle: ".o_snippet_thumbnail:not(.o_we_ongoing_insertion .o_snippet_thumbnail)",
            dropzones: () => dropzoneEls,
            helper: ({ element, helperOffset }) => {
                snippet = element;
                const draggedEl = element.cloneNode(true);
                draggedEl
                    .querySelectorAll(
                        ".o_snippet_thumbnail_title, .o_snippet_thumbnail_area, .rename-delete-buttons"
                    )
                    .forEach((el) => el.remove());
                draggedEl.style.position = "fixed";
                document.body.append(draggedEl);
                // Center the helper on the thumbnail image.
                const thumbnailImgEl = element.querySelector(".o_snippet_thumbnail_img");
                helperOffset.x = thumbnailImgEl.offsetWidth / 2;
                helperOffset.y = thumbnailImgEl.offsetHeight / 2;
                return draggedEl;
            },
            onDragStart: ({ element }) => {
                const dragAndDropProm = new Promise(
                    (resolve) => (dragAndDropResolve = () => resolve())
                );
                this.shared.operation.next(async () => await dragAndDropProm, {
                    withLoadingEffect: false,
                });
                const restoreDragSavePoint = this.shared.history.makeSavePoint();
                this.cancelDragAndDrop = () => {
                    this.shared.dropzone.removeDropzones();
                    // Undo the changes needed to ease the drag and drop.
                    this.dragState.restoreCallbacks?.forEach((restore) => restore());
                    restoreDragSavePoint();
                };
                this.hideSnippetToolTip?.();

                this.document.body.classList.add("oe_dropzone_active");
                this.state.ongoingInsertion = true;

                this.dragState = {};
                dropzoneEls = [];

                // Stop marking the elements with mutations as dirty and make
                // some changes on the page to ease the drag and drop.
                const restoreCallbacks = [];
                for (const prepareDrag of this.env.editor.getResource("on_prepare_drag_handlers")) {
                    const restore = prepareDrag();
                    restoreCallbacks.unshift(restore);
                }
                this.dragState.restoreCallbacks = restoreCallbacks;

                const category = element.closest(".o_snippets_container").id;
                const id = element.dataset.id;
                snippet = this.snippetModel.getSnippet(category, id);
                snippetEl = snippet.content.cloneNode(true);
                isSnippetGroup = category === "snippet_groups";
                isAlanSnippetBlock = category === "alan_snippets_block";

                // Check if the snippet is inline. Add it temporarily to the
                // page to compute its style and get its `display` property.
                this.document.body.appendChild(snippetEl);
                const snippetStyle = window.getComputedStyle(snippetEl);
                const isInlineSnippet = snippetStyle.display.includes("inline");
                snippetEl.remove();

                // Color-customize the snippet dynamic SVGs with the current
                // theme colors.
                const dynamicSvgEls = [
                    ...snippetEl.querySelectorAll(
                        'img[src^="/html_editor/shape/"], img[src^="/web_editor/shape/"]'
                    ),
                ];
                dynamicSvgEls.forEach((dynamicSvgEl) => {
                    const colorCustomizedURL = new URL(
                        dynamicSvgEl.getAttribute("src"),
                        window.location.origin
                    );
                    colorCustomizedURL.searchParams.forEach((value, key) => {
                        const match = key.match(/^c([1-5])$/);
                        if (match) {
                            colorCustomizedURL.searchParams.set(
                                key,
                                getCSSVariableValue(
                                    `o-color-${match[1]}`,
                                    this.document.defaultView.getComputedStyle(
                                        this.document.documentElement
                                    )
                                )
                            );
                        }
                    });
                    dynamicSvgEl.src = colorCustomizedURL.pathname + colorCustomizedURL.search;
                });

                // The dragged element may change while dragging.
                Object.assign(this.dragState, { draggedEl: snippetEl, snippetEl, snippet });

                // Add the dropzones.
                const withGrids =
                    !isSnippetGroup &&
                    (this.env.editor.config.isMobileView(this.editable) ? "filterOnly" : true);
                const selectors = this.shared.dropzone.getSelectors(snippetEl, false, withGrids);
                dropzoneEls = this.shared.dropzone.activateDropzones(selectors, {
                    toInsertInline: isInlineSnippet,
                });

                this.env.editor.dispatchTo("on_snippet_dragged_handlers", {
                    snippetEl,
                    dragState: this.dragState,
                });
            },
            dropzoneOver: ({ dropzone }) => {
                const dropzoneEl = dropzone.el;
                if (isSnippetGroup) {
                    dropzoneEl.classList.add("o_dropzone_highlighted");
                    this.dragState.currentDropzoneEl = dropzoneEl;
                    return;
                }
                dropzoneEl.after(this.dragState.draggedEl);
                dropzoneEl.classList.add("invisible");
                this.dragState.currentDropzoneEl = dropzoneEl;

                this.env.editor.dispatchTo("on_snippet_over_dropzone_handlers", {
                    snippetEl,
                    dragState: this.dragState,
                });
            },
            onDrag: ({ x, y }) => {
                if (!this.dragState.currentDropzoneEl) {
                    return;
                }

                this.env.editor.dispatchTo("on_snippet_move_handlers", {
                    snippetEl,
                    dragState: this.dragState,
                    x,
                    y,
                });
            },
            dropzoneOut: ({ dropzone }) => {
                const dropzoneEl = dropzone.el;
                if (isSnippetGroup) {
                    dropzoneEl.classList.remove("o_dropzone_highlighted");
                    this.dragState.currentDropzoneEl = null;
                    return;
                }

                this.env.editor.dispatchTo("on_snippet_out_dropzone_handlers", {
                    snippetEl,
                    dragState: this.dragState,
                });

                this.dragState.draggedEl.remove();
                dropzoneEl.classList.remove("invisible");
                this.dragState.currentDropzoneEl = null;
            },
            onDragEnd: async ({ x, y, helper }) => {
                this.document.body.classList.remove("oe_dropzone_active");
                let currentDropzoneEl = this.dragState.currentDropzoneEl;
                const isDroppedOver = !!currentDropzoneEl;

                // If the snippet was dropped outside of a dropzone, find the
                // dropzone that is the nearest to the dropping point.
                if (!currentDropzoneEl) {
                    const blockTabLeft = this.blockTabRef.el.getBoundingClientRect().left;
                    if (y > 3 && x + helper.getBoundingClientRect().height < blockTabLeft) {
                        const closestDropzoneEl = closest(dropzoneEls, { x, y });
                        if (closestDropzoneEl) {
                            currentDropzoneEl = closestDropzoneEl;
                        }
                    }
                }

                if (currentDropzoneEl) {
                    let draggedEl = this.dragState.draggedEl;
                    if (isDroppedOver) {
                        this.env.editor.dispatchTo("on_snippet_dropped_over_handlers", {
                            droppedEl: draggedEl,
                            dragState: this.dragState,
                        });
                    } else {
                        currentDropzoneEl.after(draggedEl);
                        this.env.editor.dispatchTo("on_snippet_dropped_near_handlers", {
                            droppedEl: draggedEl,
                            dropzoneEl: currentDropzoneEl,
                            dragState: this.dragState,
                        });
                    }
                    // The dragged element may have changed, so get it again.
                    draggedEl = this.dragState.draggedEl;

                    // In order to mark only the concerned elements as dirty,
                    // remove the element, then replay the drop after
                    // re-allowing to mark dirty.
                    draggedEl.remove();

                    // Undo the changes needed to ease the drag and drop and
                    // re-allow to mark dirty.
                    this.dragState.restoreCallbacks.forEach((restore) => restore());
                    this.dragState.restoreCallbacks = null;

                    // Replay the drop.
                    currentDropzoneEl.after(draggedEl);
                    this.shared.dropzone.removeDropzones();

                    // Process the dropped element.
                    if (isAlanSnippetBlock) {
                        this.openSnippetDialog(snippet, snippetEl);
                    }
                    else if (!isSnippetGroup) {
                        await this.processDroppedSnippet(snippetEl);
                        delete this.cancelDragAndDrop;
                    } else {
                        this.shared.operation.next(
                            async () => {
                                await this.onSnippetGroupDrop(snippet, snippetEl);
                            },
                            {
                                withLoadingEffect: false,
                                shouldInterceptClick: true,
                            }
                        );
                    }
                } else {
                    this.cancelDragAndDrop();
                    delete this.cancelDragAndDrop;
                }

                this.state.ongoingInsertion = false;
                dragAndDropResolve();
            },
        };

        this.draggableComponent = useDragAndDrop(dragAndDropOptions);
    },

    onSnippetGroupClick(snippet) {
        if (snippet.name == "website_builder" || snippet.name == "as_snippet_builder" || snippet.name == "as_home_page_demo") {
            let snippetEl = snippet.content.cloneNode(true);
            this.insertSnippetAtClosestDropzone(snippet, snippetEl);
        }
        else {
            this.shared.operation.next(
                async () => {
                    this.cancelDragAndDrop = this.shared.history.makeSavePoint();
                    this.dragState = {};
                    let snippetEl;
                    const baseSectionEl = snippet.content.cloneNode(true);
                    this.state.ongoingInsertion = true;
                    await new Promise((resolve) => {
                        this.snippetModel.openSnippetDialog(
                            snippet,
                            {
                                onSelect: (snippet) => {
                                    snippetEl = snippet.content.cloneNode(true);

                                    // Add the dropzones corresponding to a section and
                                    // make them invisible.
                                    const selectors = this.shared.dropzone.getSelectors(baseSectionEl);
                                    const dropzoneEls =
                                        this.shared.dropzone.activateDropzones(selectors);
                                    this.editable
                                        .querySelectorAll(".oe_drop_zone")
                                        .forEach((dropzoneEl) => dropzoneEl.classList.add("invisible"));

                                    // Find the dropzone closest to the center of the
                                    // viewport and not located in the top quarter of
                                    // the viewport.
                                    const iframeWindow = this.document.defaultView;
                                    const viewPortCenterPoint = {
                                        x: iframeWindow.innerWidth / 2,
                                        y: iframeWindow.innerHeight / 2,
                                    };
                                    const validDropzoneEls = dropzoneEls.filter(
                                        (el) =>
                                            el.getBoundingClientRect().top >= viewPortCenterPoint.y / 2
                                    );
                                    const closestDropzoneEl =
                                        closest(validDropzoneEls, viewPortCenterPoint) ||
                                        dropzoneEls.at(-1);

                                    // Insert the selected snippet.
                                    closestDropzoneEl.after(snippetEl);
                                    this.shared.dropzone.removeDropzones();
                                    return snippetEl;
                                },
                                onClose: () => {
                                    resolve();
                                },
                            },
                            this.env.editor
                        );
                    });

                    if (snippetEl) {
                        await scrollTo(snippetEl, { extraOffset: 50 });
                        await this.processDroppedSnippet(snippetEl);
                    }
                    this.state.ongoingInsertion = false;
                    delete this.cancelDragAndDrop;
                },
                {
                    withLoadingEffect: false,
                    shouldInterceptClick: true,
                }
            );
        }
    }
});

BlockTab.template = "theme_alan.BlockTab";
