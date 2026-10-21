<?php

namespace FusionStoreBundle\Widgets;

use Tax;
use Tools;
use Configuration;
use Shop;
use Group;
use Customer;
use Context;
use Language;
use Currency;
use Cart;
use Product;
use Validate;
use Country;
use Warehouse;
use Category;
use Carrier;
use FusionStoreBundle\Tools as FSTools;
use FusionStoreBundle\Services\CarrierService;

class FusionBundleWidget extends WidgetRender
{

    public function __construct( $module, $context = null )
    {
        parent::__construct($module, $context);
        return $this;
    }

    public function getCategoryForMenu( $idCategory, $idLang = false )
    {
        if(!$idLang){
            $idLang = Context::getContext()->language->id;
        }

        $Category = new Category($idCategory, $idLang);

        return [
            'id_parent'     => $Category->id_parent,
            'label'         => $Category->name,
            'description'   => $Category->description,
            'link_rewrite'  => $Category->link_rewrite,
            'image'         => Context::getContext()->link->getCatImageLink($Category->link_rewrite, $idCategory, '0_thumb'),
            'link'          => Context::getContext()->link->getCategoryLink($Category)
        ];
    }

    protected function widgetNewsletterForm(array $configuration = [])
    {
        $template_file = 'widgets/newsletter.tpl';
        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($template_file));
    }

    protected function widgetStoreLocator(array $configuration = [])
    {
        $template_file = 'locator.tpl';
        $renderwhat = isset($configuration['renderwhat']) ? $configuration['renderwhat'] : 'renderWidget';

        if ( !$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($renderwhat.$template_file)) ) {
            $this->context->smarty->assign([
                'renderwhat' => isset($configuration['renderwhat']) ? $configuration['renderwhat'] : 'renderWidget',
                'locator_url' => $this->context->link->getBaseLink().'locator',
                'location_options' => (new \FusionStoreBundle\Locator())->getLocationOptions(),
            ]);
        }

        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($renderwhat.$template_file));
    }

    protected function widgetStoreMenu(array $configuration = [])
    {
        # views/templates/front/
        $template_file = 'menu/menu.tpl';

        $menu_cats = [
          10 => [ 13, 14, 15, 16, 17 ],
          11 => [ 18, 19, 20, 21, 22 ],
          12 => [ 23, 24, 25, 26, 27, 28 ]
        ];

        $storemenu = [];

        foreach ($menu_cats as $id_cat => $subs) {
            $storemenu[$id_cat] = $this->getCategoryForMenu( $id_cat, Context::getContext()->language->id );
            foreach ($subs as $id_subcat) {
                if( !isset($storemenu[$id_cat]['submenu']) ){
                    $storemenu[$id_cat]['submenu'] = [];
                }
                $storemenu[$id_cat]['submenu'][$id_subcat] = $this->getCategoryForMenu( $id_subcat, Context::getContext()->language->id );
            }
        }


        $storemenu[] = [
            'label' => 'Inspiration',
            'link' => '#'
        ];

        $storemenu[] = [
            'label' => 'Mother’s Day',
            'link' => '#'
        ];

        if ( !$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($template_file)) ) {
            $this->context->smarty->assign([
              'storemenu'     => $storemenu,
              'lazysettings'  => [
                  'placeholder' => __PS_BASE_URI__.'img/lazy-placeholder.png',
                  'width'       => '190',
                  'height'      => '190'
              ]
            ]);
        }

        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($template_file));
    }

    protected function widgetProductRatingOnMiniature(array $configuration = [])
    {
        $template_file = 'product_rating_on_miniature.tpl';

        $id_product = $configuration['idproduct'];

        if (!$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file) )) {
            $product_rating = \FusionStoreBundle\Entity\ProductRating::getStarRatingByProductID($id_product);
            $this->context->smarty->assign($product_rating);
        }

        $this->context->smarty->assign([
            'ratings' => true,
            'averageTotal' => 2,
            'interactionsTotal' => 56
        ]);

        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file));
    }

    protected function widgetProductRating(array $configuration = [])
    {
        return $this->widgetProductRatingOnMiniature($configuration);
    }

    protected function widgetProductQuantitySelector(array $configuration = [])
    {
        $template_file = 'product_quantity_selector.tpl';
        $id_product = $configuration['idproduct'];
        $this->context->smarty->assign([
            'specific_prices' => $configuration['qdiscounts']
        ]);
        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file));
    }

    protected function widgetProductAdditionalInfo(array $configuration = [])
    {
        $template_file = 'product_additional_info.tpl';
        $id_product = $configuration['idproduct'];

        if (!$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file) )) {
            $this->context->smarty->assign([
                'free_shipping_over_value' => '149,99€*',
                'delivery_estimate' => 'Monday 14 Feb and Tuesday 15 Feb'
            ]);
        }

        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file));
    }

    protected function widgetShippingCost(array $configuration = [])
    {
        # views/templates/front/
        $template_file = 'widgets/shipping_cost.tpl';
        $id_product = $configuration['idproduct'];

        $context = Context::getContext();

        if( !Validate::isLoadedObject($context->country) ){
            $this->context->country = new Country(Configuration::get('PS_COUNTRY_DEFAULT'));
        }

        $product = new Product((int)$id_product);

        $list = CarrierService::getAvailableCarrierList($product, null, $this->context->country->id, null, null);

        $country_name = (is_array($this->context->country->name)) ? $this->context->country->name[$this->context->language->id] : $this->context->country->name;

        $carrier_list = [];

      	foreach ($list as $carrier) {
            $_ca = new Carrier($carrier);
            $price = $_ca->getDeliveryPriceByWeight($product->weight, $this->context->country->id_zone);

            // Obter a taxa de IVA da transportadora
            $tax = Tax::getCarrierTaxRate($carrier, $this->context->country->id_zone);

            // Calcular o preço com IVA
            $priceWithTax = $price * (1 + $tax / 100);

            $carrier_list[] = [
              'name' => $_ca->name,
              'price' => (!$priceWithTax||$priceWithTax==0) ? 'Portes gratis' : FSTools::displayPrice($priceWithTax)
            ];
        }

        if (!$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($template_file) )) {
            $this->context->smarty->assign([
                'country_name' => $country_name,
                'shipping_options' => $carrier_list
            ]);
        }

        return $this->module->fetch($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file));
    }

}
