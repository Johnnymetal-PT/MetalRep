/** @odoo-module **/

// Widget backend que combina BinaryField do Odoo com <model-viewer> para preview 3D.

import { registry } from "@web/core/registry";
import { isBinarySize } from "@web/core/utils/binary";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { _t } from "@web/core/l10n/translation";
import { BinaryField, binaryField } from "@web/views/fields/binary/binary_field";

class ModelViewerField extends BinaryField {
    static template = "pg_3d_viewer.ModelViewerField";
    static props = {
        ...(BinaryField.props || {}),
        style: { type: String, optional: true },
        fileNameField: { type: String, optional: true },
    };

    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    get viewerUrl() {
        const value = this.props.record?.data?.[this.props.name];
        if (!value) {
            return "";
        }
        if (isBinarySize(value)) {
            const resId = this.props.record?.resId;
            if (!resId) {
                return "";
            }
            return url("/web/content", {
                model: this.props.record.resModel,
                id: resId,
                field: this.props.name,
            });
        }
        return `data:${this.sourceMimeType};base64,${value}`;
    }

    get fileName() {
        return this.props.record?.data?.[this.props.fileNameField] || "";
    }

    get fileExtension() {
        const filename = this.fileName;
        if (!filename || !filename.includes(".")) {
            return "";
        }
        return filename.split(".").pop().toLowerCase();
    }

    get sourceMimeType() {
        const mimeByExtension = {
            glb: "model/gltf-binary",
            gltf: "model/gltf+json",
            fbx: "application/octet-stream",
            dxf: "application/dxf",
        };
        return mimeByExtension[this.fileExtension] || "application/octet-stream";
    }

    get canRenderInModelViewer() {
        return ["", "glb", "gltf"].includes(this.fileExtension);
    }

    get viewerStyle() {
        return this.props.style || "";
    }

    onToggleFullscreen(ev) {
        const container = ev.currentTarget?.closest(".o_model_viewer_container") || this.el;
        const modelViewerElem = container ? container.querySelector("model-viewer") : null;
        if (!modelViewerElem) {
            return;
        }
        const isFullscreenAvailable =
            document.fullscreenEnabled ||
            document.mozFullScreenEnabled ||
            document.webkitFullscreenEnabled ||
            document.msFullscreenEnabled ||
            false;
        if (!isFullscreenAvailable) {
            console.error("ERROR: full screen not supported by web browser");
            return;
        }
        const fullscreenElement =
            document.fullscreenElement ||
            document.mozFullScreenElement ||
            document.webkitFullscreenElement ||
            document.msFullscreenElement;
        if (fullscreenElement) {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            return;
        }
        if (modelViewerElem.requestFullscreen) {
            modelViewerElem.requestFullscreen();
        } else if (modelViewerElem.mozRequestFullScreen) {
            modelViewerElem.mozRequestFullScreen();
        } else if (modelViewerElem.webkitRequestFullscreen) {
            modelViewerElem.webkitRequestFullscreen();
        } else if (modelViewerElem.msRequestFullscreen) {
            modelViewerElem.msRequestFullscreen();
        }
    }

    onViewerError() {
        if (this.notification) {
            this.notification.add(_t("Could not display the selected model."), {
                title: _t("3D model"),
                type: "danger",
            });
        }
    }
}

const modelViewerField = {
    ...binaryField,
    component: ModelViewerField,
    extractProps: ({ attrs, options }) => ({
        ...(binaryField.extractProps ? binaryField.extractProps({ attrs, options }) : {}),
        style: attrs?.style,
        fileNameField: attrs?.filename,
    }),
};

registry.category("fields").add("model_viewer", modelViewerField);

export default ModelViewerField;
