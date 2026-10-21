<?php

use FusionStoreBundle\ProductFeeds\Feeds\GoogleMerchants;
use FusionStoreBundle\ProductFeeds\Feeds\Converter;

class FusionShoppingFeedsModuleFrontController extends ModuleFrontController
{
    public $ssl = true;

    public $customer_access = true;

    private $feed_response_type = 'xml';

    public function __construct()
    {
        parent::__construct();
    }

    public function init()
    {
        parent::init();
        $this->feed_response_type = Tools::getValue('feed_response_type');
    }

    public function initContent()
    {
        $feed_engine = Tools::getValue('feed_engine');
        $feed_name = Tools::getValue('feed_name');
        $feed_token = Tools::getValue('feed_token');

        if( !$this->isFeedOnCache($feed_engine, $feed_name, $feed_token)){
            switch ($feed_engine) {
                case 'googlemerchants':
                    $feed = (new GoogleMerchants($feed_name, $feed_token));
                    break;

                case 'facebook':
                    $feed = (new FaceBook($feed_name, $feed_token));
                    break;

                default:
                    $feed = [ 'error' => 'Invalid feed engine' ];
                    break;
            }
        }else{
            #$feed = $this->getFromCache($feed_engine, $feed_name, $feed_token);
        }

        if( is_object($feed) && $this->feed_response_type == 'xml' ){
            #$this->storeInCache( $feed_engine, $feed_name, $feed_token, $feed->feed(), $feed->header_content_type );
            $this->displayFeed( $feed->feed(), $feed->header_content_type );
        }

        die();
    }

    private function isFeedOnCache( $feed_engine, $feed_name, $feed_token )
    {
        $cacheid = md5($feed_engine.$feed_name.$feed_token);
        return false;

    }

    private function storeInCache( $feed_engine, $feed_name, $feed_token, $feed, $header_content_type )
    {
    }

    private function getFromCache( $feed_engine, $feed_name, $feed_token )
    {
        $cache_file = $this->isFeedOnCache( $feed_engine, $feed_name, $feed_token );

        if($cache_file !==false){
            $cache_data = file_get_contents($cache_file);
            $cache_data = base64_decode($cache_data);
            return;
        }

    }

    private function displayFeed( $output, $header_content_type) {
        header('Content-Type: ' . $header_content_type);
        header('Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0');
        echo $output;
    }
}
