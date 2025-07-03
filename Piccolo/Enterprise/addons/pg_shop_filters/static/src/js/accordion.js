document.addEventListener('DOMContentLoaded', function () {
    function setupAccordion(accordionItems, headerSelector, contentSelector) {
        accordionItems.forEach(function (item) {
            var contents = item.querySelectorAll(contentSelector);
            contents.forEach(function (content) {
                content.style.display = 'none';
            });

            var header = item.querySelector(headerSelector);
            if (header) {
                header.addEventListener('click', function () {
                    contents.forEach(function (content) {
                        if (content.style.display === 'none') {
                            content.style.display = 'block';
                        } else {
                            content.style.display = 'none';
                        }
                    });

                    // Toggle the 'active' class on click
                    header.classList.toggle('active');
                });
            }
        });
    }

    // Handle the existing structure
    var collapseContainer1 = document.getElementById('wsale_products_attributes_collapse');
    if (collapseContainer1) {
        var accordionItems1 = collapseContainer1.querySelectorAll('.accordion-item.nav-item.mb-1.border-0');
        setupAccordion(accordionItems1, 'h6.mb-3', '.form-check.mb-1');
    }

    // Handle the second structure
    var collapseContainer2 = document.querySelector('.js_attributes.d-flex.flex-column');
    if (collapseContainer2) {
        var accordionItems2 = collapseContainer2.querySelectorAll('.accordion-item.border-top-0.order-2');
        setupAccordion(accordionItems2, '.accordion-header', '.accordion-body');
    }

    // Handle the new structure
    var collapseContainer3 = document.querySelector('.products_categories.mb-3');
    if (collapseContainer3) {
        var accordionItems3 = collapseContainer3.querySelectorAll('.nav-item');
        accordionItems3.forEach(function (item) {
            var header = item.querySelector('h6.o_categories_collapse_title');
            var radioButton = item.querySelector('.form-check-input');

            // Check the class of the item to determine if it should have a radio button
            if (!item.classList.contains('mb-1')) {
                if (radioButton) {
                    radioButton.parentElement.style.display = 'none';
                }
            }

            if (header) {
                header.addEventListener('click', function () {
                    var contents = item.querySelectorAll('.form-check.d-inline-block');
                    contents.forEach(function (content) {
                        if (content.style.display === 'none') {
                            content.style.display = 'block';
                        } else {
                            content.style.display = 'none';
                        }
                    });

                    // Toggle the 'active' class on click
                    header.classList.toggle('active');
                });
            }
        });
    }

    // Handle the new elements
    function addActiveClassOnClick(selector) {
        document.querySelectorAll(selector).forEach(function (element) {
            element.addEventListener('click', function () {
                element.classList.toggle('active');
            });
        });
    }

    addActiveClassOnClick('.wsale_products_categories_list .accordion-collapse > .nav-item > .accordion-header');
    addActiveClassOnClick('.wsale_products_categories_list .accordion-collapse .accordion-collapse > .nav-item > .d-flex');
    addActiveClassOnClick('.wsale_products_categories_list .nav-item.mb-1 > .d-flex');
});

function toggleAttributes() {
    var attributesDiv = document.getElementById('wsale_products_attributes_collapse');
    var toggleButtonSymbol = document.querySelector('#toggleAttributesButton .symbol');
    if (attributesDiv.style.display === 'none' || attributesDiv.style.display === '') {
        attributesDiv.style.display = 'block';
        toggleButtonSymbol.innerHTML = '-';
    } else {
        attributesDiv.style.display = 'none';
        toggleButtonSymbol.innerHTML = '+';
    }
}
