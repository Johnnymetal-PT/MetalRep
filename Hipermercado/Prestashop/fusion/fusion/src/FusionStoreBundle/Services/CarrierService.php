<?php

namespace FusionStoreBundle\Services;

use Product;
use Configuration;
use Context;
use Carrier;
use Cart;
use Address;
use Customer;
use Country;
use Cache;
use Db;
use DbQuery;
use Warehouse;

class CarrierService
{
    private $context;

    public function __construct( Context $context )
    {
        $this->context = $context;
        return $this;
    }

    public static function getBestShippingCost(Product $product, $id_warehouse, $id_contry = null, $id_shop = null, $cart = null, &$error = [])
    {
        $carriers = self::getAvailableCarrierList($product, $id_warehouse, $id_contry, $id_shop, $cart, $error, false);

        if( empty($carriers) ){
            return [];
        }

        $best_price = null;
        $_carrier = [];

        foreach ($carriers as $carrier) {
            if( $carrier['price'] < $best_price || $best_price === null ){
                if( (float)$carrier['price'] > 0 || $carrier['is_free'] ){
                    $best_price = $carrier['price'];
                    $_carrier = $carrier;
                }
            }
        }

        return $_carrier;
    }

    public static function getAvailableCarrierList(Product $product, $id_warehouse, $id_contry = null, $id_shop = null, $cart = null, &$error = [], $only_ids = true)
    {
        static $ps_country_default = null;

        if ($ps_country_default === null) {
            $ps_country_default = Configuration::get('PS_COUNTRY_DEFAULT');
        }

        if (null === $id_shop) {
            $id_shop = Context::getContext()->shop->id;
        }
        if (null === $cart) {
            $cart = Context::getContext()->cart;
        }

        if (null === $error || !is_array($error)) {
            $error = [];
        }

        $products = [[
            'id_product'                => $product->id,
            'id_shop'                   => $id_shop,
            'id_address_delivery'       => 0,
            'id_product_attribute'      => 0,
            'id_customization'          => 0,
            'cart_quantity'             => 1,
            'weight_attribute'          => 0,
            'is_virtual'                => 0,
            'additional_shipping_cost'  => $product->additional_shipping_cost,
            'weight'                    => $product->weight,
        ]];

        $country = new Country($id_contry);
        $id_zone = $country->id_zone;

        // Does the product is linked with carriers?
        $cache_id = 'Carrier::getAvailableCarrierList_' . (int) $product->id . '-' . (int) $id_shop;
        if (!Cache::isStored($cache_id)) {
            $query = new DbQuery();
            $query->select('id_carrier');
            $query->from('product_carrier', 'pc');
            $query->innerJoin(
                'carrier',
                'c',
                'c.id_reference = pc.id_carrier_reference AND c.deleted = 0 AND c.active = 1'
            );
            $query->where('pc.id_product = ' . (int) $product->id);
            $query->where('pc.id_shop = ' . (int) $id_shop);

            $carriers_for_product = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($query);
            Cache::store($cache_id, $carriers_for_product);
        } else {
            $carriers_for_product = Cache::retrieve($cache_id);
        }

        $carrier_list = [];
        if (!empty($carriers_for_product)) {
            //the product is linked with carriers
            foreach ($carriers_for_product as $carrier) { //check if the linked carriers are available in current zone
                if (Carrier::checkCarrierZone($carrier['id_carrier'], $id_zone)) {
                    $carrier_list[$carrier['id_carrier']] = $carrier['id_carrier'];
                }
            }
            if (empty($carrier_list)) {
                return [];
            }//no linked carrier are available for this zone
        }

        // The product is not directly linked with a carrier
        // Get all the carriers linked to a warehouse
        if ($id_warehouse) {
            $warehouse = new Warehouse($id_warehouse);
            $warehouse_carrier_list = $warehouse->getCarriers();
        }

        $available_carrier_list = [];
        $cache_id = 'Carrier::getAvailableCarrierList_getCarriersForOrder_' . (int) $id_zone . '-' . (int) $product->id;
        if (!Cache::isStored($cache_id)) {
            $customer = new Customer($cart->id_customer);
            $carrier_error = [];
            $carriers = self::getCarriersForOrder($id_zone, $customer->getGroups(), $product, $carrier_error, $products);
            Cache::store($cache_id, [$carriers, $carrier_error]);
        } else {
            list($carriers, $carrier_error) = Cache::retrieve($cache_id);
        }

        if( !$only_ids ){
            $carrier_list_detail = [];
            foreach ($carriers as $carrier) {
                $carrier_list_detail[$carrier['id_carrier']] = $carrier;
            }
        }

        $error = array_merge($error, $carrier_error);

        foreach ($carriers as $carrier) {
            $available_carrier_list[$carrier['id_carrier']] = $carrier['id_carrier'];
        }

        if ($carrier_list) {
            $carrier_list = array_intersect($available_carrier_list, $carrier_list);
        } else {
            $carrier_list = $available_carrier_list;
        }

        if (isset($warehouse_carrier_list)) {
            $carrier_list = array_intersect($carrier_list, $warehouse_carrier_list);
        }

        $cart_quantity = 0;
        $cart_weight = 0;

        foreach ($products as $cart_product) {
            if ($cart_product['id_product'] == $product->id) {
                $cart_quantity += $cart_product['cart_quantity'];
            }
            if (isset($cart_product['weight_attribute']) && $cart_product['weight_attribute'] > 0) {
                $cart_weight += ($cart_product['weight_attribute'] * $cart_product['cart_quantity']);
            } else {
                $cart_weight += ($cart_product['weight'] * $cart_product['cart_quantity']);
            }
        }

        if ($product->width > 0 || $product->height > 0 || $product->depth > 0 || $product->weight > 0 || $cart_weight > 0) {
            foreach ($carrier_list as $key => $id_carrier) {
                $carrier = new Carrier($id_carrier);

                // Get the sizes of the carrier and the product and sort them to check if the carrier can take the product.
                $carrier_sizes = [
                    'width' => (int) $carrier->max_width,
                    'height' => (int) $carrier->max_height,
                    'depth' => (int) $carrier->max_depth,
                ];
                $product_sizes = [
                    'width' => (int) $product->width,
                    'height' => (int) $product->height,
                    'depth' => (int) $product->depth,
                ];

                if (($carrier_sizes['width'] > 0 && $carrier_sizes['width'] < $product_sizes['width'])
                    || ($carrier_sizes['height'] > 0 && $carrier_sizes['height'] < $product_sizes['height'])
                    || ($carrier_sizes['depth'] > 0 && $carrier_sizes['depth'] < $product_sizes['depth'])
                ) {
                    $error[$carrier->id] = Carrier::SHIPPING_SIZE_EXCEPTION;
                    unset($carrier_list[$key]);
                }

                if ($carrier->max_weight > 0 && ($carrier->max_weight < $product->weight * $cart_quantity || $carrier->max_weight < $cart_weight)) {
                    $error[$carrier->id] = Carrier::SHIPPING_WEIGHT_EXCEPTION;
                    unset($carrier_list[$key]);
                }
            }
        }

        return $only_ids ? $carrier_list : array_intersect_key($carrier_list_detail, array_flip($carrier_list));
    }


    public static function getCarriersForOrder($id_zone, $groups = null, $product = null, &$error = [], $products)
    {
        $context = Context::getContext();
        $id_lang = $context->language->id;

        if (isset($context->currency)) {
            $id_currency = $context->currency->id;
        }

        $cart = $context->cart;

        if (is_array($groups) && !empty($groups)) {
            $result = Carrier::getCarriers($id_lang, true, false, (int) $id_zone, $groups, Carrier::PS_CARRIERS_AND_CARRIER_MODULES_NEED_RANGE);
        } else {
            $result = Carrier::getCarriers($id_lang, true, false, (int) $id_zone, [Configuration::get('PS_UNIDENTIFIED_GROUP')], Carrier::PS_CARRIERS_AND_CARRIER_MODULES_NEED_RANGE);
        }
        $results_array = [];

        foreach ($result as $k => $row) {
            $carrier = new Carrier((int) $row['id_carrier']);
            $shipping_method = $carrier->getShippingMethod();
            if ($shipping_method != Carrier::SHIPPING_METHOD_FREE) {
                // Get only carriers that are compliant with shipping method
                if (($shipping_method == Carrier::SHIPPING_METHOD_WEIGHT && $carrier->getMaxDeliveryPriceByWeight($id_zone) === false)) {
                    $error[$carrier->id] = Carrier::SHIPPING_WEIGHT_EXCEPTION;
                    unset($result[$k]);

                    continue;
                }
                if (($shipping_method == Carrier::SHIPPING_METHOD_PRICE && $carrier->getMaxDeliveryPriceByPrice($id_zone) === false)) {
                    $error[$carrier->id] = Carrier::SHIPPING_PRICE_EXCEPTION;
                    unset($result[$k]);

                    continue;
                }

                // If out-of-range behavior carrier is set to "Deactivate carrier"
                if ($row['range_behavior']) {
                    // Get id zone
                    if (!$id_zone) {
                        $id_zone = (int) Country::getIdZone((int) Configuration::get('PS_COUNTRY_DEFAULT'));
                    }

                    // Get only carriers that have a range compatible with cart
                    if ($shipping_method == Carrier::SHIPPING_METHOD_WEIGHT
                        && (Carrier::checkDeliveryPriceByWeight($row['id_carrier'], $product->weight, $id_zone) === false)) {
                        $error[$carrier->id] = Carrier::SHIPPING_WEIGHT_EXCEPTION;
                        unset($result[$k]);

                        continue;
                    }

                    if ($shipping_method == Carrier::SHIPPING_METHOD_PRICE
                        && (Carrier::checkDeliveryPriceByPrice($row['id_carrier'], $product->price, $id_zone, $id_currency ?? null) === false)) {
                        $error[$carrier->id] = Carrier::SHIPPING_PRICE_EXCEPTION;
                        unset($result[$k]);

                        continue;
                    }
                }
            }

            $row['name'] = ((string) ($row['name']) != '0' ? $row['name'] : Carrier::getCarrierNameFromShopName());
            $row['price'] = (($shipping_method == Carrier::SHIPPING_METHOD_FREE) ? 0 : $cart->getPackageShippingCost((int) $row['id_carrier'], true, null, $products, $id_zone));
            $row['price_tax_exc'] = (($shipping_method == Carrier::SHIPPING_METHOD_FREE) ? 0 : $cart->getPackageShippingCost((int) $row['id_carrier'], false, null, $products, $id_zone));
            $row['img'] = file_exists(_PS_SHIP_IMG_DIR_ . (int) $row['id_carrier'] . '.jpg') ? _THEME_SHIP_DIR_ . (int) $row['id_carrier'] . '.jpg' : '';

            // If price is false, then the carrier is unavailable (carrier module)
            if ($row['price'] === false) {
                unset($result[$k]);

                continue;
            }
            $results_array[] = $row;
        }

        // if we have to sort carriers by price
        $prices = [];
        if (Configuration::get('PS_CARRIER_DEFAULT_SORT') == Carrier::SORT_BY_PRICE) {
            foreach ($results_array as $r) {
                $prices[] = $r['price'];
            }
            if (Configuration::get('PS_CARRIER_DEFAULT_ORDER') == Carrier::SORT_BY_ASC) {
                array_multisort($prices, SORT_ASC, SORT_NUMERIC, $results_array);
            } else {
                array_multisort($prices, SORT_DESC, SORT_NUMERIC, $results_array);
            }
        }

        return $results_array;
    }

}
