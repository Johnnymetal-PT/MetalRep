import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";

// ─── B2B Document Upload Validation ─────────────────────────────────────────────────
export class B2BDocumentUploadValidation extends Interaction {
    static selector = ".b2b_document_upload_section";

    setup() {
        // File upload validation
        const fileInput = this.el.querySelector("#document_attachment");
        const helpText = this.el.querySelector(".form-text");

        if (fileInput) {
            fileInput.addEventListener("change", (ev) => {
                const file = ev.target.files[0];
                this._clearErrors(fileInput, helpText);
                if (file) {
                    const allowedExtensions = ["pdf", "jpg", "jpeg", "png"];
                    const fileName = file.name.toLowerCase();
                    const fileExt = fileName.split(".").pop();
                    if (!allowedExtensions.includes(fileExt)) {
                        this._showError(
                            fileInput,
                            helpText,
                            _t("Invalid file type. Please upload PDF, JPG, JPEG, or PNG only.")
                        );
                        ev.target.value = "";
                        return;
                    }
                    if (file.size > 10 * 1024 * 1024) {
                        this._showError(
                            fileInput,
                            helpText,
                            _t("File size exceeds 10 MB. Please upload a smaller document.")
                        );
                        ev.target.value = "";
                        return;
                    }
                }
            });
        }
        this._setupCountryStateFilter();
    }

    _setupCountryStateFilter() {
        const countrySelect = document.querySelector("#country_id");
        const stateSelect = document.querySelector("#state_id");
        if (countrySelect && stateSelect) {
            countrySelect.addEventListener("change", async (ev) => {
                const countryId = ev.target.value;
                stateSelect.innerHTML = '<option value="">Select State</option>';
                if (!countryId) {
                    stateSelect.disabled = true;
                    return;
                }
                stateSelect.disabled = true;
                const loadingOption = document.createElement("option");
                loadingOption.textContent = "Loading states...";
                stateSelect.appendChild(loadingOption);
                try {
                    const result = await rpc("/b2b/get_states", {
                        country_id: parseInt(countryId),
                    });
                    stateSelect.innerHTML = '<option value="">Select State</option>';

                    if (result && result.length > 0) {
                        result.forEach(state => {
                            const option = document.createElement("option");
                            option.value = state.id;
                            option.textContent = state.name;
                            stateSelect.appendChild(option);
                        });
                        stateSelect.disabled = false;
                    } else {
                        const noStateOption = document.createElement("option");
                        noStateOption.textContent = "No states available";
                        noStateOption.disabled = true;
                        stateSelect.appendChild(noStateOption);
                        stateSelect.disabled = true;
                    }
                } catch (error) {
                    console.error("Error fetching states:", error);
                    stateSelect.innerHTML = '<option value="">Select State</option>';
                    const errorOption = document.createElement("option");
                    errorOption.textContent = "Error loading states";
                    errorOption.disabled = true;
                    stateSelect.appendChild(errorOption);
                }
            });

            // Disable state select initially if no country is selected
            if (!countrySelect.value) {
                stateSelect.disabled = true;
            }
        } else {
            console.error("Country or State select not found!");
        }
    }

    _showError(fileInput, helpText, message) {
        let errorMsg = this.el.querySelector(".file-size-error");
        if (!errorMsg) {
            errorMsg = document.createElement("div");
            errorMsg.classList.add("file-size-error", "text-danger", "mt-1");
            this.el.appendChild(errorMsg);
        }
        errorMsg.textContent = message;
        fileInput.classList.add("is-invalid");
        helpText.classList.add("text-danger");
    }

    _clearErrors(fileInput, helpText) {
        const existingError = this.el.querySelector(".file-size-error");
        if (existingError) existingError.remove();
        fileInput.classList.remove("is-invalid");
        helpText.classList.remove("text-danger");
    }
}

registry.category("public.interactions").add("theme_alan.b2b_document_upload_validation", B2BDocumentUploadValidation);