<?php

namespace FusionStoreBundle\ProductFeeds\Feeds;

use SimpleXMLElement;
use Product;
use Image;
use Tools;
use Validate;
use Country;
use StockAvailable;
use PrestaShop\PrestaShop\Core\Localization\Locale;
use PrestaShop\PrestaShop\Adapter\Product\PriceFormatter;
use FusionStoreBundle\Services\CarrierService;

class GoogleMerchants extends \FusionStoreBundle\ProductFeeds\ProductsFeed
{
    public $header_content_type = 'text/xml';

    public $root_elem = '<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0" />';

    private $match_param = [
        'condition' => [
            'new' => 'new',
            'used' => 'used',
            'refurbished' => 'refurbished',
        ]
    ];

    public function __construct( $feed_name, $feed_token )
    {
        parent::__construct( $feed_name, $feed_token );
        $this->feed_link = $this->context->link->getBaseLink() . 'feeds/googlemerchants-' . $feed_name . '-' . $feed_token . '.xml';
    }

    public function feed()
    {
        $priceFormatter = new PriceFormatter();

        $xml = new SimpleXMLElement($this->root_elem);

        $xml->addChild('channel');
        $xml->channel->addChild('title', $this->feed_name);
        $xml->channel->addChild('link', $this->feed_link);
        $xml->channel->addChild('description', $this->feed_description);

        $counter = 0;

        $countrys = Country::getCountries($this->context->language->id, true);

        foreach ($this->feed_data as $_product) {
            $product = new Product( (int)$_product['id_product'], true, $this->id_lang );
            if($product->active){
                $image = Image::getCover( $product->id );

                if( (int)$product->quantity > 1 ){
                    $availability = 'in stock';
                }else{
                    $availability = 'out of stock';
                }

                $availability = 'in stock';

                $product_price = $product->getPrice(true, false);

                $xml->channel->addChild('item');
                $xml->channel->item[$counter]->addChild( 'g:g:id'          , $product->id );
                $xml->channel->item[$counter]->addChild( 'g:g:title'       , $product->name );
                $xml->channel->item[$counter]->addChild( 'g:g:description' , strip_tags($product->description) );
                $xml->channel->item[$counter]->addChild( 'g:g:product_type', $this->getCategories($product) );
                $xml->channel->item[$counter]->addChild( 'g:g:link'        , $this->context->link->getProductLink($product, null, null, null, $this->id_lang) );
                $xml->channel->item[$counter]->addChild( 'g:g:image_link'  , $this->context->link->getImageLink($product->link_rewrite, $image['id_image'], 'home_default') );
                $xml->channel->item[$counter]->addChild( 'g:g:availability', $availability );
                $xml->channel->item[$counter]->addChild( 'g:g:condition'   , $this->match_param['condition'][$product->condition] );
                $xml->channel->item[$counter]->addChild( 'g:g:price'       , Tools::ps_round($product_price,2) . ' ' . $this->context->currency->iso_code );
                $xml->channel->item[$counter]->addChild( 'g:g:brand'       , isset($product->brand)?$product->brand:'' );
                $xml->channel->item[$counter]->addChild( 'g:g:gtin'        , $product->ean13 );
                $xml->channel->item[$counter]->addChild( 'g:g:age_group'   , 'adult' );

                $_shipping = [];

                /*foreach ($countrys as $country) {

                    $carrier = CarrierService::getBestShippingCost($product, null, $country['id_country']);

                    if( !empty($carrier) ){
                        if( (int)$carrier['id_carrier'] == 75 ){
                            $carrier['price'] = '25';
                        }

                        $_shipping[$counter] = $xml->channel->item[$counter]->addChild( 'g:g:shipping' );
                        $_shipping[$counter]->addChild( 'g:g:country', $country['iso_code'] );
                        $_shipping[$counter]->addChild( 'g:g:region', '' );
                        $_shipping[$counter]->addChild( 'g:g:service', 'Express' );
                        $_shipping[$counter]->addChild( 'g:g:price', $carrier['price'] . ' EUR' );
                        $_shipping[$counter]->addChild( 'g:g:min_handling_time', '1' );
                        $_shipping[$counter]->addChild( 'g:g:max_handling_time', '5' );
                        $_shipping[$counter]->addChild( 'g:g:min_transit_time', '1' );
                        $_shipping[$counter]->addChild( 'g:g:max_transit_time', '5' );
                    }
                }*/

                $counter ++;
            }
        }

        return $xml->asXML();
    }

}
