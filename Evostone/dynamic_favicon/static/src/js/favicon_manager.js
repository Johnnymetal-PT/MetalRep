/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";

const dynamicFaviconService = {
    dependencies: [],
    async start(env, services) {
        function updateFavicon() {
            const companyId = session.company_id || 'default';
            
            let link = document.querySelector("link[rel='shortcut icon']");
            if (!link) {
                link = document.createElement('link');
                link.type = 'image/x-icon';
                link.rel = 'shortcut icon';
                document.head.appendChild(link);
            }
            
            link.href = `/web/favicon.ico?company=${companyId}&t=${new Date().getTime()}`;
        }
        
        updateFavicon();
        
        // Only try to hook into company switching if the company service exists
        if (services.company) {
            const originalSwitchCompany = services.company.setCompanies;
            if (originalSwitchCompany) {
                services.company.setCompanies = function(...args) {
                    const result = originalSwitchCompany.apply(this, args);
                    updateFavicon();
                    return result;
                };
            }
        }
        
        return {
            updateFavicon,
        };
    },
};

registry.category("services").add("dynamic_favicon", dynamicFaviconService);