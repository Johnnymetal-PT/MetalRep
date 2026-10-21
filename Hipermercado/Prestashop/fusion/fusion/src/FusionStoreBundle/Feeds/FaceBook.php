<?php

namespace FusionStoreBundle\Feeds;

use SimpleXMLElement;
use Product;
use Category;
use Image;
use Tools;
use Validate;
use StockAvailable;
use PrestaShop\PrestaShop\Core\Localization\Locale;
use PrestaShop\PrestaShop\Adapter\Product\PriceFormatter;

class FaceBook extends GoogleMerchants
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
        $this->feed_link = $this->context->link->getBaseLink() . 'feeds/facebook-' . $feed_name . '-' . $feed_token . '.xml';
    }
}
