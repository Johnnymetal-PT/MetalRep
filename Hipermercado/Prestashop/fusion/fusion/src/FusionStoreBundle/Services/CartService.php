<?php

namespace FusionStoreBundle\Services;

use Validate;
use Cart;
use Context;

/**
 *
 */
class CartService
{
    private $context;

    public function __construct( Context $context )
    {
        $this->context = $context;
        return $this;
    }

    public function addProductToCart( $idProduct, $idProductAttribute = null )
    {
        if (Validate::isLoadedObject($this->context->cart)) {
            $this->context->cart->updateQty(1, $idProduct, $idProductAttribute);
        } else {
            $cart = new Cart();
            $cart->id_currency = $this->context->currency->id;
            $cart->id_lang = $this->context->language->id;
            $cart->save();
            $this->context->cart = $cart;
            $this->context->cart->updateQty(1, $idProduct, $idProductAttribute);
            $this->context->cookie->id_cart = $cart->id;
        }
        return true;
    }
}
