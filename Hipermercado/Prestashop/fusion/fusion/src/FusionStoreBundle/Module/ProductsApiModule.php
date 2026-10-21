<?php

namespace FusionStoreBundle\Module;

use Module;
use Currency;
use Configuration;
use Category;
use Context;
use Tools;
use FusionStoreBundle\CronJob\ProductSync as CronProductSync;
use FusionStoreBundle\Import\ProductModel;
use FusionStoreBundle\Import\ProductSync;
use FusionStoreBundle\MediaPlugins;
use FusionStoreBundle\TranslateEngine\TranslateEngine;
use FusionStoreBundle\Reports\ImportProductReportMaker;
use FusionStoreBundle\ProductsApiModuleAssociations;

/**
 * Fusion Products API Module
 */
class ProductsApiModule extends Module
{
    // default lifetime is 5 hours > 18000 secunds
    public $feed_lifetime = 18000;

    protected $fusion = null;
    protected $FusionModule = null;

    public $default_active = false;
    public $default_category = false;

    protected $translate_engine = false;

    public $associations = [];

    function __construct()
    {
        parent::__construct();

        /* Connect to Fusion Services */
        if( class_exists('FusionStoreBundle\Module\AdminModule') ){
            $this->FusionModule = new \FusionStoreBundle\Module\AdminModule($this, $this->context);
        }

        if(!defined('FUSION_SERVICES_DIR')){
            $this->fusion = Module::getInstanceByName('fusion');
        }

        $this->associations = $this->loadAssociations();
    }

    public function loadAssociations()
    {
        $ProductsApiModuleAssociations = (new ProductsApiModuleAssociations($this, $this->associations));
        return $ProductsApiModuleAssociations->getArray();
    }

    public function saveAssociations()
    {
        $ProductsApiModuleAssociations = (new ProductsApiModuleAssociations($this, $this->associations));
        $ProductsApiModuleAssociations->saveOnline();
        return $ProductsApiModuleAssociations->saveLocal();
    }

    public function getTranslateEngine()
    {
        if( $this->translate_engine instanceof \FusionStoreBundle\TranslateEngine\TranslateEngine ){
            return $this->translate_engine;
        }
        return false;
    }

    public function getContent()
    {
        if( $this->FusionModule === null ){
            die();
        }

        if (((bool) Tools::isSubmit('_action')) == true && Tools::getValue('_action') == 'saveAssociations') {

            $form_data = Tools::getValue('_data');
            $form_data = json_decode($form_data, true);

            if(is_array($form_data) && !empty($form_data)){
                foreach ($form_data as $cate_hash => $data) {
                    $parts = explode('|',$cate_hash);
                    if(!isset($this->associations[$parts[1]])){
                        $this->associations[$parts[1]] = [];
                    }
                    $this->associations[$parts[1]][$parts[0]] = $data;
                }
            }

            $result = $this->saveAssociations();
            ob_end_clean();
            header('Content-Type: application/json');
            echo json_encode([
              'status' => ( $result ? 'OK' : 'FAIL' )
            ]);
            die();
        }
    }

    protected function syncProduct( $entry_key, $default_active = 0, $id_category_default = null, $ignore_if_exist = false, $image_folder = null )
    {
        $api_feed = $this->getProductsFeed( true );

        if(isset($api_feed[$entry_key])){

            $options = Tools::getValue('_options');

            $product_data = $api_feed[$entry_key];

            $product_model = new ProductModel( $product_data );
            $product_model->filterModel();

            $sync_result = (new ProductSync())->setDefaults([
                'active'            => $default_active,
                'default_category'  => Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_'.$this->name, '1')
            ])
            ->setCategoryMatch($this->associations)
            ->createIfNotExist()
            ->syncSource( $this->displayName )
            ->syncModule( $this->name )
            ->behaviorWhenExists( $options )
            ->setTranslateEngine( $this->getTranslateEngine() )
            ->syncProduct( $product_model, true, $ignore_if_exist, $image_folder );

            (new ImportProductReportMaker())
              ->module($this->name)
              ->hash( Tools::getValue('_hash') )
              ->feed($api_feed[$entry_key])
              ->product($product_model)
              ->result($sync_result);

            return $sync_result->getAjaxResponse();
        }
        return false;
    }

    public function getSyncTable( Array $table_header = [] )
    {
        MediaPlugins::load($this->context, 'bs-modal');
        $ignore_products_outofstock = Configuration::get('FS_IMPORT_IGNORE_NON_STOCK_PRODUCTS_'.$this->name, '0');

        $api_feed = $this->getProductsFeed();
        $total_products = count($api_feed);
        $total_products_in_stock = 0;

        foreach ($api_feed as &$value) {
            if($value['quantity'] > 0){
                $value['hide'] =  false;
                $total_products_in_stock ++;
            }else{
                if($ignore_products_outofstock){
                    $value['hide'] =  true;
                }else{
                    $value['hide'] =  false;
                }
            }
        }

        foreach ($api_feed as &$row) {
            if( !isset($row['images'])
            || empty($row['images']) ){
                $row['noimg'] = true;
            }
        }

        if( empty($table_header) ){
            $table_header = [
                'ean13'           => 'EAN13',
                'name_pt'         => 'Name',
                'category'        => 'Category',
                'sub_category'    => 'Sub Category',
                'wholesale_price' => 'Wholesale Price',
                'unit_price'      => 'Price',
                'quantity'        => 'Stock',
            ];
        }

        # gel import form
        $this->context->smarty->assign([
            'total_products'  => $total_products,
            'total_products_in_stock'  => $total_products_in_stock,
            'table_header'    => $table_header,
            'api_feed'        => $api_feed,
            'import_hash'     => md5('hash_'.time())
        ]);

        return $this->FusionModule->render('sync_form.tpl', 'module:fusion/src/FusionStoreBundle/Resources/views/Admin/ProductsApi/');
    }

    public function getFeedCategorys()
    {
        $categorys = array();
        $api_feed = $this->getProductsFeed();

        foreach ($api_feed as $product) {
            $categorys[md5($product['category'])] = [
              'origin'          => $product['category'],
              'target'          => ( isset($this->associations[md5($product['category'])]) ? $this->associations[md5($product['category'])]['target'] : 0 ),
              'shipping'        => ( isset($this->associations[md5($product['category'])]) ? $this->associations[md5($product['category'])]['shipping'] : 0 ),
              'margin'          => ( isset($this->associations[md5($product['category'])]) ? $this->associations[md5($product['category'])]['margin'] : 0 ),
              'extra_margin'    => ( isset($this->associations[md5($product['category'])]) ? $this->associations[md5($product['category'])]['extra_margin'] : 0 ),
              'origin_desc'     => ( isset($this->associations[md5($product['category'])]) ? $this->associations[md5($product['category'])]['origin_desc'] : 0 )
            ];
            if(isset($product['sub_category'])){
              $categorys[md5($product['sub_category'])] = [
                'origin'        => $product['sub_category'],
                'target'        => ( isset($this->associations[md5($product['sub_category'])]) ? $this->associations[md5($product['sub_category'])]['target'] : 0 ),
                'shipping'      => ( isset($this->associations[md5($product['sub_category'])]) ? $this->associations[md5($product['sub_category'])]['shipping'] : 0 ),
                'margin'        => ( isset($this->associations[md5($product['sub_category'])]) ? $this->associations[md5($product['sub_category'])]['margin'] : 0 ),
                'extra_margin'  => ( isset($this->associations[md5($product['sub_category'])]) ? $this->associations[md5($product['sub_category'])]['extra_margin'] : 0 ),
                'origin_desc'   => ( isset($this->associations[md5($product['sub_category'])]) ? $this->associations[md5($product['sub_category'])]['origin_desc'] : 0 )
              ];
            }
        }

        return $categorys;
    }

    public function renderCategoryMatchForm()
    {
        $store_categorys  = Category::getSimpleCategories($this->context->language->id);
        $currency         = Currency::getCurrencyInstance(Configuration::get('PS_CURRENCY_DEFAULT'));
        $this->context->smarty->assign([
            'currency'          => $currency,
            'store_categorys'   => $store_categorys,
            'feed_categorys'    => $this->getFeedCategorys()
        ]);
        return $this->FusionModule->render('category_match.tpl', 'module:fusion/src/FusionStoreBundle/Resources/views/Admin/ProductsApi/');
    }

    public function filterProductPrice( $product )
    {
        if(!isset($product['unit_price']))
            return 0;

        $final_price = (float)$product['unit_price'];

        $increment = 0;

        $discount_from_base = 0;

        if(isset($this->associations[md5($product['category'])])){

            if( isset($this->associations[md5($product['category'])]['origin_desc']) ){
                $origin_desc = (float)$this->associations[md5($product['category'])]['origin_desc'];
                $discount_from_base = $final_price - ($final_price * ((100-$origin_desc) / 100));
            }

            $margin = (float)$this->associations[md5($product['category'])]['margin'];
            $extra_margin = (float)$this->associations[md5($product['category'])]['extra_margin'];
            $increment += (float)$this->associations[md5($product['category'])]['shipping'];
            $increment = $increment + (($increment+$final_price)*(($margin+$extra_margin)/100));
        }

        $sub_increment = 0;

        if( isset($product['sub_category']) && isset($this->associations[md5($product['sub_category'])])){
            if( isset($this->associations[md5($product['sub_category'])]['origin_desc']) ){
                $origin_desc = (float)$this->associations[md5($product['sub_category'])]['origin_desc'];
                $discount_from_base = $final_price - ($final_price * ((100-$origin_desc) / 100));
            }

            $margin = (float)$this->associations[md5($product['sub_category'])]['margin'];
            $extra_margin = (float)$this->associations[md5($product['sub_category'])]['extra_margin'];
            $sub_increment += (float)$this->associations[md5($product['sub_category'])]['shipping'];
            $sub_increment = $sub_increment + (($sub_increment+$final_price)*(($margin+$extra_margin)/100));
        }

        if( $sub_increment > $increment){
            $increment = $sub_increment;
        }

        $final_price = ($final_price-$discount_from_base) + $increment;
        return (float)$final_price;
    }

    public function cronRun()
    {
        $api_feed = $this->getProductsFeed();
        $cron = new CronProductSync( $this->context );
        $cron->module($this);
        $cron->productDataFeed( $api_feed );
        return $cron->run();
    }

}
