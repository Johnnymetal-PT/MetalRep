/** @odoo-module alias=theme_alan.ProductQueriesDialog **/

import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

// ─── Product Queries Dialog ─────────────────────────────────────────────────
export class ProductQueriesDialog extends Component {
    static template = "theme_alan.ProductQueries";
    static props = {
        close: Function,
        product_id: Number,
        user_email: String,
        user_phone: String,
        user_id: Number,
        user_name: String,
        is_public_user: Boolean,
        dialog_header: String,
        dialog_header_desc: String,
        acknowledgement_message: String,
    }

    setup() {
        this.state = useState({
            contact_preference: 'Email',
            // Preserve field values across contact preference changes
            name: this.props.is_public_user ? '' : this.props.user_name,
            email: this.props.is_public_user ? '' : this.props.user_email,
            phone: this.props.is_public_user ? '' : this.props.user_phone,
            message: '',
        });
    }

    onContactPreferenceChange(ev) {
        // Save current field values before switching
        const $modal = $(this.__owl__.bdom.parentEl);
        this.state.name = $modal.find("#customer").val();
        this.state.email = $modal.find("#email").val() || this.state.email;
        this.state.phone = $modal.find("#phone").val() || this.state.phone;
        this.state.message = $modal.find("#message").val();

        this.state.contact_preference = ev.target.id;
        // Clear any existing validation errors when preference changes
        $modal.find(".msg, .email, .phone").removeClass("border border-danger");
        $modal.find(".phone-error, .email-error").hide();
    }

    _validatePhone(phone) {
        // Must be at least 6 digits and at most 20 characters, allowing +, spaces, dashes, parentheses
        return /^\+?[\d\s\-().]{6,20}$/.test(phone);
    }

    _validateEmail(email) {
        // Basic email regex: something@domain.tld
        return /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/.test(email);
    }

    send_queries(ev) {
        const $modal = $(this.__owl__.bdom.parentEl);
        const customer_name = $modal.find("#customer").val();
        const email = $modal.find("#email").val();
        const phone = $modal.find("#phone").val();
        const message = $modal.find("#message").val();
        const user_id = $modal.find("#customer_id").val();
        const contact_preference = this.state.contact_preference;

        let hasError = false;

        if (customer_name === '') {
            $modal.find(".name").addClass("border border-danger");
            hasError = true;
        }

        if (message === '') {
            $modal.find(".msg").addClass("border border-danger");
            hasError = true;
        }

        if (contact_preference === 'Email' || contact_preference === 'Both') {
            if (!email) {
                $modal.find(".email").addClass("border border-danger");
                hasError = true;
            } else if (!this._validateEmail(email)) {
                $modal.find(".email").addClass("border border-danger");
                $modal.find(".email-error").text(_t('Please enter a valid email address.')).show();
                hasError = true;
            }
        }

        if (contact_preference === 'Phone' || contact_preference === 'Both') {
            if (!phone) {
                $modal.find(".phone").addClass("border border-danger");
                hasError = true;
            } else if (!this._validatePhone(phone)) {
                $modal.find(".phone").addClass("border border-danger");
                $modal.find(".phone-error").text(_t("Please enter a valid phone number (6–20 characters, digits, +, spaces, dashes allowed).")).show();
                hasError = true;
            }
        }

        if (hasError) { return; }

        const context = {
            message,
            customer_name,
            user_id,
            email,
            phone,
            product_id: this.props.product_id,
            contact_preference,
        };

        rpc('/send_queries_mail', { ...context, _t: Date.now() })
            .then((res) => {
                if (res && res.success === false) {
                    let msg = _t("Something went wrong");
                    if (res.error_code === 'already_submitted') {
                        msg = _t("You have already submitted an inquiry for this product with this email or phone in the last 24 hours.");
                    } else if (res.message) {
                        msg = res.message;
                    }
                    $modal.find(".queries-container").hide();
                    $modal.find("#error-message .error-text")
                        .text(msg);
                    $modal.find("#error-message").removeClass("o_hidden");
                    return;
                }
                $modal.find(".queries-container").hide();
                $modal.find("#thank-you").removeClass("o_hidden");

            })
            .catch((err) => {
                let msg = _t("Something went wrong");
                if (err && err.data && err.data.message) {
                    msg = err.data.message;
                }
                $modal.find(".queries-container").hide();
                $modal.find("#error-message .error-text")
                    .text(msg);
                $modal.find("#error-message").removeClass("o_hidden");
            });
        setTimeout(() => {
            this.props.close();
        }, 2000);
    }

    _onChangeInput() {
        const $modal = $(this.__owl__.bdom.parentEl);
        $modal.find(".name, .msg, .email, .phone").removeClass("border border-danger");
        $modal.find(".phone-error, .email-error").hide();
    }
}

export default {
    ProductQueriesDialog,
};
