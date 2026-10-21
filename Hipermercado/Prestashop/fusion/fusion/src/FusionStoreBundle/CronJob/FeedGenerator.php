<?php

namespace FusionStoreBundle\CronJob;

use Context;
use PrestaShop\PrestaShop\Adapter\Product\PriceFormatter;
use SimpleXMLElement;
use Product;
use Category;
use Image;
use Validate;
use Module;
use DbQuery;
use Db;
use Tools;

class FeedGenerator
{
    protected $rustart = null;

    protected $context = null;

    protected $product_feed = null;

    protected $feed_file = _PS_ROOT_DIR_.'/products_feed.xml';

    public function __construct( Context $context )
    {
        $this->context = $context;
        $this->rustart = getrusage();
        $this->time_start = microtime(true);
    }

    protected function getCategories( $product )
    {
        $cat = new Category($product->id_category_default, $this->context->language->id );
        if( Validate::isLoadedObject($cat) ){
            return $cat->name;
        }
        return '';
    }

    public function run()
    {
        if (!file_exists(_PS_ROOT_DIR_.'/modules/fusion/logs/feedgenerator_'.date("Y-m-d").'.log')) {
            touch(_PS_ROOT_DIR_.'/modules/fusion/logs/feedgenerator_'.date("Y-m-d").'.log');
        }
        
        $log  = date("Y-m-d H:i:s")." --------------INIT FEEDGENERATOR--------------".PHP_EOL.
                date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedgenerator_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        
        try {
            $priceFormatter = new PriceFormatter();

            $xml = new SimpleXMLElement('<products></products>');

            $sql = new DbQuery();
            $sql->select('p.`id_product`');
            $sql->from('product', 'p');
            $sql->leftJoin('product_shop', 'ps', 'ps.id_product = p.id_product');
            $sql->where('p.`active` = 1 AND ps.`active` = 1 AND p.`price` > 0' );
            $products = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

            $counter = 0;

            foreach ($products as $_product) {

                $product = new Product( (int)$_product['id_product'], true, $this->context->language->id );

                if( (bool)$product->active ){
                    $image = Image::getCover( $product->id );

                    $product_price = $product->getPrice(true, false);
                    $regular_price = $product->getPrice(true, null, 6, null, false, false, 1, false);

                    $xml->addChild('product');
                    $xml->product[$counter]->addChild( 'id'             , $product->id );
                    $xml->product[$counter]->addChild( 'title'          , htmlspecialchars($product->name) );
                    $xml->product[$counter]->addChild( 'reference'      , htmlspecialchars($product->reference) );
                    $xml->product[$counter]->addChild( 'description'    , strip_tags($product->description) );
                    $xml->product[$counter]->addChild( 'description_short', strip_tags($product->description_short) );
                    $xml->product[$counter]->addChild( 'category'       , $this->getCategories($product) );
                    $xml->product[$counter]->addChild( 'price_formated' , Tools::ps_round($product_price,2) . ' ' . $this->context->currency->iso_code );
                    $xml->product[$counter]->addChild( 'price'          , Tools::ps_round($product_price,2));
                    
                    $xml->product[$counter]->addChild( 'regular_price'          , Tools::ps_round($regular_price,2));
                    $xml->product[$counter]->addChild( 'regular_price_formated' , Tools::ps_round($regular_price,2) . ' ' . $this->context->currency->iso_code );

                    $xml->product[$counter]->addChild( 'base_price_formated' , Tools::ps_round($product->base_price,2) . ' ' . $this->context->currency->iso_code );
                    $xml->product[$counter]->addChild( 'base_price'          , Tools::ps_round($product->base_price,2));
                    $xml->product[$counter]->addChild( 'delivery_time'          , '3');
                    $xml->product[$counter]->addChild( 'currency'       , $this->context->currency->iso_code );
                    $xml->product[$counter]->addChild( 'quantity'       , $product->quantity );
                    $xml->product[$counter]->addChild( 'ean13'          , $product->ean13 );
                    $xml->product[$counter]->addChild( 'brand'          , htmlspecialchars($product->manufacturer_name) );
                    $xml->product[$counter]->addChild( 'link'           , $this->context->link->getProductLink($product, null, null, null, $this->context->language->id) );
                    $xml->product[$counter]->addChild( 'image_link'     , $this->context->link->getImageLink($product->link_rewrite, $image['id_image'], 'home_default') );
                    $counter ++;
                }
            }

            $feed_xml = $xml->asXML();

            file_put_contents($this->feed_file, $feed_xml);
        } catch (\Exception $e) {
            $log  = date("Y-m-d H:i:s")." FeedGenerator CronJob Exception: ".$e->getMessage().PHP_EOL;
            file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
            file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedgenerator_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        }

        $time_end = microtime(true);
        $execution_time = ($time_end - $this->time_start);

        $log  = date("Y-m-d H:i:s")." --------------END FEEDGENERATOR---------------".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedgenerator_'.date("Y-m-d").'.log', $log, FILE_APPEND);

        $ru = getrusage();
        echo "Find " . ($counter+1) .
            " products\n";
        echo "This process used " . $this->rutime($ru, $this->rustart, "utime") .
            " ms for its computations\n";
        echo "It spent " . $this->rutime($ru, $this->rustart, "stime") .
            " ms in system calls\n";
        echo " Execution time " . $execution_time .
            " s\n";
    }

    # Script end
    protected function rutime($ru, $rus, $index) {
        return ($ru["ru_$index.tv_sec"]*1000 + intval($ru["ru_$index.tv_usec"]/1000))
         -  ($rus["ru_$index.tv_sec"]*1000 + intval($rus["ru_$index.tv_usec"]/1000));
    }

}
