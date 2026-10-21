<?php

namespace FusionStoreBundle\CronJob;

use Context;
use Module;
use DbQuery;
use Configuration;
use Db;
use FusionStoreBundle\Import\ProductModel;
use FusionStoreBundle\Import\ProductSync as ImportProductSync;
use FusionStoreBundle\Reports\ImportProductReportMaker;
use Product;

class ProductSync
{
    protected $rustart = null;

    protected $context = null;

    protected $module = null;

    protected $product_feed = null;

    protected $hash = null;

    public function __construct( Context $context )
    {
        $this->context = $context;
        $this->rustart = getrusage();
        $this->hash = md5(time());
    }

    public function module( Module $module )
    {
        $this->module = $module;
    }

    public function productDataFeed( Array $product_data_feed )
    {
        $this->product_feed = $product_data_feed;
        return $this;
    }

    protected function create_product( $product )
    {
        $default_active = $this->module->default_active;
        $ignore_if_exist = true;

        $options = [
            'product_name'    => true,
            'product_info'    => true,
            'product_prices'  => true,
            'images'          => true,
            'categories'      => true
        ];

        $product_model = new ProductModel( $product );
        $product_model->filterModel();

        $sync_result = (new ImportProductSync())->setDefaults([
            'active'            => $default_active,
            'default_category'  => Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_'.$this->module->name, '1')
        ])
        ->setCategoryMatch($this->module->associations)
        ->createIfNotExist()
        ->syncSource( $this->module->displayName )
        ->syncModule( $this->module->name )
        ->behaviorWhenExists( $options )
        ->setTranslateEngine( $this->module->getTranslateEngine() )
        ->syncProduct( $product_model, true, $ignore_if_exist );


        (new ImportProductReportMaker())
          ->module($this->module->name)
          ->hash($this->hash)
          ->feed($product)
          ->product($product_model)
          ->result($sync_result);

        $log  = date("Y-m-d H:i:s")." ProductSync Create (".$product['reference'].") getAjaxResponse: ".json_encode($sync_result->getAjaxResponse()).PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);

        return $sync_result->getAjaxResponse();
    }

    public function run()
    {
        if (!file_exists(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log')) {
            touch(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log');
        }
        
        $log  = date("Y-m-d H:i:s")." --------------INIT PRODUCTSYNC--------------".PHP_EOL.
                date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL.
                date("Y-m-d H:i:s")." Supplier: ".$this->module->displayName.PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);

        $find = 0;
        $find_update = 0;
        $find_create = 0;
        foreach ($this->product_feed as $key => $product) {
            if(isset($product['ean13']) && strlen($product['ean13']) == 13){

                $sql = new DbQuery();
                $sql->select('p.`id_product`, p.`wholesale_price`, ps.`wholesale_price` as wholesale_price_shop, st.`quantity`, fs.`module`');
                $sql->from('product', 'p');
                $sql->leftJoin('product_shop', 'ps', 'ps.id_product = p.id_product');
                $sql->leftJoin('stock_available', 'st', 'st.id_product = p.id_product');
                $sql->leftJoin('fusion_sync', 'fs', 'fs.id_product = p.id_product');
                $sql->where('p.`ean13` = \'' . pSQL($product['ean13']) . '\'' );
                $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->getRow($sql);

                if( $result && isset($result['id_product']) ){
                    # Product already exists
                    try {
                        $update = 0;
                        $prod = new Product( (int)$result['id_product'], true, $this->context->language->id );
                        switch ($this->module->name) {
                            case 'intmacorlux':
                            case 'intsorefoz':
                            case 'intexperteletro':
                            case 'intociostock':
                            case 'intdepau':
                            case 'intauferma':
                                if(empty($prod->name) && isset($product['name_pt']) && !empty($product['name_pt'])) {
                                    echo 'Product id: '.(int)$result['id_product'].': name: '.$product['name_pt'].PHP_EOL;
                                    $prod->name = $this->encodeHtmlText($product['name_pt']);
                                    $update = 1;
                                }
                                if(empty($prod->description) && isset($product['description_pt']) && !empty($product['description_pt'])) {
                                    echo 'Product id: '.(int)$result['id_product'].PHP_EOL;
                                    $prod->description = $this->encodeHtmlText($product['description_pt']);
                                    $update = 1;
                                }
                                if(empty($prod->description_short) && isset($product['description_short_pt']) && !empty($product['description_short_pt'])) {
                                    echo 'Product id: '.(int)$result['id_product'].PHP_EOL;
                                    $prod->description_short = $this->encodeHtmlText($product['description_short_pt']);
                                    $update = 1;
                                }
                                break;
                            case 'intorima':
                                if(empty($prod->name) && isset($product['description']) && !empty($product['description'])) {
                                    echo 'Product id: '.(int)$result['id_product'].': name: '.$product['description'].PHP_EOL;
                                    $prod->name = $this->encodeHtmlText($product['description']);
                                    $update = 1;
                                }
                                if(empty($prod->description) && isset($product['details']) && !empty($product['details'])) {
                                    echo 'Product id: '.(int)$result['id_product'].PHP_EOL;
                                    $prod->description = $this->encodeHtmlText($product['details']);
                                    $update = 1;
                                }
                                // if(empty($prod->description_short) && !empty($product['details'])) {
                                //     $prod->description_short = $product['details'];
                                //     $update = 1;
                                // }
                                break;
                            case 'intlimifield':
                                break;
                            default:
                                break;
                        }

                        if($update) {
                            $prod->save();
                            $find_update++;
                        }
                        
                        $find ++;
                    } catch (\Exception $e) {
                        $log  = date("Y-m-d H:i:s")." ProductSync Update Exception: ".$e->getMessage().PHP_EOL;
                        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
                    }
                    
                }else{
                    try {
                        $find_create ++;
                        $create_product = $this->create_product( $product );
                    } catch (\Exception $e) {
                        $log  = date("Y-m-d H:i:s")." ProductSync (".$product['reference'].") Create Exception: ".$e->getMessage().PHP_EOL;
                        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
                    }
                }
            }
        }


        $ru = getrusage();
        echo "Find " . $find .
            " products for update\n";
        echo "Create " . $find_create .
            " products\n";
        echo "Update " . $find_update .
            " products\n";
        echo "This process used " . $this->rutime($ru, $this->rustart, "utime") .
            " ms for its computations\n";
        echo "It spent " . $this->rutime($ru, $this->rustart, "stime") .
            " ms in system calls\n";

        $log  = date("Y-m-d H:i:s")." Find ". $find ." products for update".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        $log  = date("Y-m-d H:i:s")." Create ". $find_create ." products".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        $log  = date("Y-m-d H:i:s")." Update ". $find_update ." products".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        $log  = date("Y-m-d H:i:s")." This process used ". $this->rutime($ru, $this->rustart, "utime") ." ms for its computations".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        $log  = date("Y-m-d H:i:s")." It spent ". $this->rutime($ru, $this->rustart, "stime") ." ms in system calls".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        $log  = date("Y-m-d H:i:s")." --------------END PRODUCTSYNC---------------".PHP_EOL;
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/productsync_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    }

    protected function encodeHtmlText($text)
    {
        $text = preg_replace_callback("/(&#[0-9]+;)/", function($m) { return mb_convert_encoding($m[1], "UTF-8", "HTML-ENTITIES"); }, $text);
        return utf8_decode($text);
    }

    // Script end
    protected function rutime($ru, $rus, $index) {
        return ($ru["ru_$index.tv_sec"]*1000 + intval($ru["ru_$index.tv_usec"]/1000))
         -  ($rus["ru_$index.tv_sec"]*1000 + intval($rus["ru_$index.tv_usec"]/1000));
    }

}
