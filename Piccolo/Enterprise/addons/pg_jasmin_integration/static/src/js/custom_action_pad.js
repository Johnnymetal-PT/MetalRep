/** /pg_jasmin_integration/static/src/js/custom_action_pad.js */
odoo.define('@pg_jasmin_integration/js/custom_action_pad', [], function(require) {
    'use strict';

    //console.log('CustomActionPad script loaded'); // Confirm script is loaded

    // State to track if we need to activate the invoice button
    let shouldActivateInvoice = false;

    document.addEventListener('DOMContentLoaded', function() {
        //console.log('DOM fully loaded and parsed');

        // Use MutationObserver to detect changes in the DOM
        const observer = new MutationObserver(function(mutationsList, observer) {
            for (let mutation of mutationsList) {
                if (mutation.type === 'childList') {
                    // Look for the "Pay" button every time the DOM is mutated
                    const payButton = document.querySelector(".pay.validation.pay-order-button");
                    if (payButton) {
                        //console.log('Pay button found via MutationObserver, overriding click handler');

                        payButton.onclick = function() {
                            //console.log('Custom Pay Button Clicked!'); // Confirm the click event
                            //alert('Custom Pay Button Clicked!');

                            // Set state to activate the invoice button on the next screen
                            shouldActivateInvoice = true;

                            // Call function to activate Set Partner button and select client
                            activateSetPartner();
                        };

                        observer.disconnect(); // Stop observing after setting up the handler
                        break; // Exit the loop since we've handled our case
                    }
                }
            }
        });

        // Start observing the target node for configured mutations
        observer.observe(document.body, { childList: true, subtree: true });

        // Additional observer to handle the Payment Screen load
        const paymentScreenObserver = new MutationObserver(function(mutationsList, observer) {
            for (let mutation of mutationsList) {
                if (mutation.type === 'childList' && shouldActivateInvoice) {
                    // Look for the "Invoice" button on the Payment Screen
                    const invoiceButton = document.querySelector(".button.js_invoice");
                    if (invoiceButton && !invoiceButton.classList.contains('highlight')) {
                        //console.log('Activating Invoice button on Payment Screen');
                        invoiceButton.click(); // Simulate click on Invoice button
                        shouldActivateInvoice = false; // Reset state after activation
                        observer.disconnect(); // Stop observing after activation
                    }
                }
            }
        });

        // Start observing the Payment Screen for the "Invoice" button
        paymentScreenObserver.observe(document.body, { childList: true, subtree: true });
    });

    function activateSetPartner() {
        //console.log('Activating Set Partner Button');

        // Simulate a click on the "Set Partner" button
        const setPartnerButton = document.querySelector(".button.set-partner");
        if (setPartnerButton) {
            //console.log('Set Partner button found, triggering click');
            setPartnerButton.click();

        } else {
            console.log('Set Partner button not found');
        }
    }
});
