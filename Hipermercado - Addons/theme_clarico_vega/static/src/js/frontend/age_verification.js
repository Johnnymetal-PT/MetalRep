/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

// Age Verification Widget for LS Website
publicWidget.registry.AgeVerificationEpt = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    
    async start() {
        await this._super(...arguments);
        console.log("Age Verification | Initializing process");

        try {
            const config = await rpc('/age_verification/init');

            if (config && config.is_enable_age_verification) {
                const cookieValue = this.getCookie("age_verified");
                const hasVerified = cookieValue === "true";

                if (!hasVerified) {
                    setTimeout(() => {
                        this.showAgeVerificationModal(config);
                    }, 100);
                }
            }
        } catch (error) {
            console.error("Age Verification | Error initializing:", error);
        }
    },
    
    showAgeVerificationModal(config) {
        console.log("Age Verification | Called");
        
        // Check if jQuery is available
        if (typeof $ === 'undefined') {
            console.error("Age Verification | jQuery is not available");
            return;
        }
        
        // Add blur effect
        //document.body.classList.add("ls-age-verification-blur");
        
        // Prepare logo
        let logoHtml = '';
        if (config.background_image) {
            logoHtml = `<div class="tcv-age-verification-logo">
                <img src="data:image/png;base64,${config.background_image}" alt="Logo" class="img-fluid"/>
            </div>`;
        }

        const modalHtml = `
            <div class="modal fade tcv-age-verification-modal-wrapper" id="ageVerificationModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content tcv-age-verification-content" style="background-color: ${config.background_color};">
                        ${logoHtml}

                        <div class="tcv-age-verification-message">
                            <div class="tcv-age-verification-text">
                                ${config.message}
                            </div>
                        </div>
                        
                        <div class="tcv-age-verification-buttons">
                            <button class="btn tcv-age-btn-no" style="background-color: ${config.no_button_color} !important; color: ${config.no_button_text_color} !important;" id="ageVerifyNo">
                                ${'NO'}
                            </button>
                            <button class="btn tcv-age-btn-yes" style="background-color: ${config.yes_button_color} !important; color: ${config.yes_button_text_color} !important;" id="ageVerifyYes">
                                ${'YES'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append modal to body
        $('body').append(modalHtml);
        console.log("Age Verification | Modal appended");
        
        // Show modal
        if (typeof bootstrap !== 'undefined') {
            const modalElement = document.getElementById('ageVerificationModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement, {
                    backdrop: 'static',
                    keyboard: false
                });
                modal.show();
            }
        } else {
            $('#ageVerificationModal').modal({
                backdrop: 'static',
                keyboard: false
            });
            $('#ageVerificationModal').modal('show');
        }
        
        // Handle Yes button
        $('#ageVerifyYes').on('click', async () => {
            console.log("Age Verification | Yes button clicked");
            
            // Set cookie
            this.setCookie("age_verified", "true", 30);
            console.log("Age Verification | Cookie set: age_verified=true");
            
            // Verify cookie was set
            const cookieCheck = this.getCookie("age_verified");
            console.log("Age Verification | Cookie verification:", cookieCheck);
            
            // Record verification
            try {
                await rpc("/age_verification/confirm", {
                    verified: true,
                });
                console.log("Age Verification | Age verification confirmed on server");
            } catch (error) {
                console.error("Age Verification | Error recording age verification:", error);
            }
            
            // Remove blur and close modal
            // document.body.classList.remove("ls-age-verification-blur");
            
            // Close modal
            $('#ageVerificationModal').modal('hide');
            
            // Clean up after modal animation completes
            setTimeout(() => {
                $('#ageVerificationModal').remove();
                $('.modal-backdrop').remove();
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
            }, 300);
        });
        
        // Handle No button
        $('#ageVerifyNo').on('click', () => {
            console.log("Age Verification | No button clicked");
            
            // Show warning message
            const warningHtml = `
                <div class="alert mb-3 alert-warning tcv-age-verification-warning" style="text-align: center; background-color: ${config.background_color};">
                    ${config.warning}
                </div>
            `;
            if ($('.tcv-age-verification-warning').length === 0) {
                $('.tcv-age-verification-buttons').before(warningHtml);
            }
            
            // Record the rejection
            try {
                rpc("/age_verification/confirm", {
                    verified: false,
                });
            } catch (error) {
                console.error("Age Verification | Age verification rejection:", error);
            }
        });
    },
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },
    
    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        const cookieString = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
        document.cookie = cookieString;
        console.log("Age Verification | Setting cookie:", cookieString);
    }
});

// Make sure widget is loaded
console.log("Age verification loaded");

// Export the widget
export default publicWidget.registry.LSAgeVerification; 