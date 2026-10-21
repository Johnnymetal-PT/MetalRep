function validateTotalOrder(){
    if( prestashop.cart.totals.total.amount >= 1000 ){
        $('[name="vat_number"]').attr('required', true);
        if(!checkVat()){
            alert('Para compras superiores a 1000€, é necessario preencher o NIF.');
            $('#checkout-addresses-step').trigger('click');
        }
    }
}

function checkVat(){
    var have_vat = false;
    $.each(prestashop.customer.addresses, function (i,address) {
        if(address.vat_number!=''){
            have_vat = true;
        }
    });
    return have_vat;
}

$( document ).ready(function() {
    if(prestashop.page.page_name == 'checkout'){
        setTimeout(validateTotalOrder, 800);
    }
});