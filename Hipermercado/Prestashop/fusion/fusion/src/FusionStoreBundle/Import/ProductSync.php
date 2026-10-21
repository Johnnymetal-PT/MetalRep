<?php

namespace FusionStoreBundle\Import;

use PrestaShop\PrestaShop\Adapter\Import\ImportDataFormatter;
use PrestaShop\PrestaShop\Core\ConfigurationInterface;
use FusionStoreBundle\Entity\FusionSync;
use FusionStoreBundle\Reports\ImportProductReport;
use FusionStoreBundle\TranslateEngine\TranslateEngine;
use PrestaShopException;
use Exception;
use Configuration;
use Manufacturer;
use Product;
use Combination;
use Feature;
use FeatureValue;
use AttributeGroup;
use ProductAttributeCore;
use ProductAttribute;
use Attribute;
use Hook;
use Category;
use Tag;
use Search;
use Shop;
use StockAvailable;
use TaxManagerFactory;
use Context;
use Address;
use Validate;
use Tools;
use Language;
use Db;
use DbQuery;
use Image;
use ImageType;
use ImageManager;
use TaxRulesGroup;
use AdminImportControllerCore;

class ProductSync
{

    public static $image_import_folder = null;

    protected static $process_feed_log = array();

    private $context;

    private $sync_source = false;

    private $sync_module = false;

    private $defaults = [
        'active' => true,
        'id_category' => 1
    ];

    private $only_sync_stock = false;

    private $category_association = false;

    private $translate_engine = false;

    public $sync_images = false;

    public function __construct()
    {
        $this->context = Context::getContext();
        $this->report = new ImportProductReport();
    }

    public function onlySyncStock()
    {
        $this->only_sync_stock = true;
        return $this;
    }

    public function behaviorWhenExists($options)
    {
        if( is_array($options) ){
            $this->updateProductName      = (isset($options['product_name'])) ? !filter_var($options['product_name'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateProductInfo      = (isset($options['product_info'])) ? !filter_var($options['product_info'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateProductPrices    = (isset($options['product_prices'])) ? !filter_var($options['product_prices'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateImages           = (isset($options['images'])) ? !filter_var($options['images'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateCategories       = (isset($options['categories'])) ? !filter_var($options['categories'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateCombinations     = (isset($options['combinations'])) ? !filter_var($options['combinations'],FILTER_VALIDATE_BOOLEAN) : true;
            $this->updateFeatures         = (isset($options['features'])) ? !filter_var($options['features'],FILTER_VALIDATE_BOOLEAN) : true;
        }
        return $this;
    }

    public function createIfNotExist()
    {
        return $this;
    }

    public function syncSource($source)
    {
        $this->sync_source = $source;
        return $this;
    }

    public function syncModule($module)
    {
        $this->sync_module = $module;
        return $this;
    }

    public function updateSyncFusionTable( $id_product )
    {
        if( $this->sync_source !== false || $this->sync_module != false ){
            $fusion_sync = FusionSync::getByProductID($id_product);

            if(!$fusion_sync){
                $fusion_sync = new FusionSync();
                $fusion_sync->id_product = $id_product;
            }

            $fusion_sync->source = $this->sync_source;
            $fusion_sync->module = $this->sync_module;

            $fusion_sync->save();
        }
    }

    public function setDefaults( Array $defaults = [])
    {
        if( !empty($defaults) ){
            foreach ($defaults as $key => $value) {
                $this->defaults[$key] = $value;
            }
        }
        return $this;
    }

    public function setCategoryMatch( Array $category_association = [])
    {
        $this->category_association = $category_association;
        return $this;
    }

    protected static function priceCalculation( $product, $price, $remove_tax = false, $id_address = null, $decimals = 6)
    {
      static $address = null;
      static $context = null;

      if ($context == null) {
        $context = Context::getContext()->cloneContext();
      }

      $cur_cart = $context->cart;

      if (!$id_address && Validate::isLoadedObject($cur_cart)) {
        $id_address = $cur_cart->{Configuration::get('PS_TAX_ADDRESS_TYPE')};
      }

      // retrieve address informations
      $address = Address::initialize($id_address, true);

      if ($address === null) {
        if (is_object($context->cart) && $context->cart->{Configuration::get('PS_TAX_ADDRESS_TYPE')} != null) {
          $id_address = $context->cart->{Configuration::get('PS_TAX_ADDRESS_TYPE')};
          $address = new Address($id_address);
        } else {
          $address = new Address();
        }
      }

      // Tax
      $tax_manager = TaxManagerFactory::getManager($address, Product::getIdTaxRulesGroupByIdProduct((int) $product->id, $context) );
      $product_tax_calculator = $tax_manager->getTaxCalculator();

      $price = $remove_tax ? $product_tax_calculator->removeTaxes($price) : $product_tax_calculator->addTaxes($price);
      $price = Tools::ps_round($price, $decimals);

      return $price;
    }

    public static function findProductByName( $name )
    {
      $result = Db::getInstance()->executeS('
          SELECT p.`id_product`, pl.*
          FROM `' . _DB_PREFIX_ . 'product` p
          LEFT JOIN `' . _DB_PREFIX_ . 'product_lang` pl ON (p.`id_product` = pl.`id_product`)
          WHERE pl.`name` LIKE \'' .$name. '\' and pl.`id_lang` = 3 LIMIT 1
      ');

      if($result)
        return $result[0]['id_product'];
      return false;
    }

    public static function findProductByEan( $ean13 )
    {
      $result = Db::getInstance()->executeS('
          SELECT `id_product`
          FROM `' . _DB_PREFIX_ . 'product`
          WHERE `ean13` = \'' .pSQL($ean13) . '\' LIMIT 1
      ');
      if($result)
        return $result[0]['id_product'];
      return false;
    }

    public static function findProductByReference( $reference )
    {
      $result = Db::getInstance()->executeS('
          SELECT `id_product`
          FROM `' . _DB_PREFIX_ . 'product`
          WHERE `reference` = \'' .pSQL($reference) . '\' LIMIT 1
      ');
      if($result)
        return $result[0]['id_product'];
      return false;
    }

    public static function fixProductName( $string )
    {
      $string = str_replace('#', '', $string);
      $string = str_replace('\'', '', $string);
      $string = str_replace('"', '', $string);
      $string = str_replace('>', '-', $string);
      $string = str_replace('<', '-', $string);
      $string = trim($string);
      return $string;
    }

    private function updateStock( $product_id, $quantity )
    {
        # quantity
        if( (int)$quantity != 0 ){
            $product = new Product( $product_id );
            if( Validate::isLoadedObject($product) ){
                $product->quantity = (int) $quantity;
                $product->update();
            }
            StockAvailable::setQuantity($product_id, 0, (int) $quantity );
            return true;
        }else{
            // Allow to order the product when out of stock?
            $stock = new StockAvailable( StockAvailable::getStockAvailableIdByProductId($product_id));
            $stock->out_of_stock = 1;
            return $stock->update();
        }
    }

    public function syncProduct( $model, $sync_images = false, $ignore_if_exist = false, $image_folder = null )
    {
        $dataFormatter = new ImportDataFormatter(
            new ConfigurationAdapter(),
            new \PrestaShop\PrestaShop\Adapter\Tools()
        );

        $sync_images = $this->updateImages;

        $result = true;
        $id_product = false;

        if( $model->get('ean13', 0) != '' )
            $id_product = self::findProductByEan( $model->get('ean13',0) );

        if( $id_product && $ignore_if_exist ){
            $this->report->result($result);
            $this->report->log('Product '.$model->get('name', $this->context->language->id).' already exist ID:' . $id_product);
            $this->report->ignore(true);
            return $this->report;
        }

        if( ($id_product && $ignore_if_exist) || ($id_product && $this->only_sync_stock) ){
            self::$process_feed_log[] = 'Product '.$model->get('name', $this->context->language->id).' already exist ID:' . $id_product;

            if($this->only_sync_stock){
                $stock_ok = $this->updateStock( $id_product, $model->get('quantity') );
                self::$process_feed_log[] = 'Update Stock, '.($stock_ok?'Ok':'Fail');
            }

            $this->report->result($result);
            $this->report->log( implode('; <br>', self::$process_feed_log) );
            return $this->report;
        }

        if( strlen($model->get('ean13', 0)) > 13 ){
            $this->report->log('Ignore  '.$model->get('ean13', 0).', EAN13 is invalid!');
            $this->report->alert( 'ean13', 'EAN13 is invalid', true );
            $this->report->result(false);
            return $this->report;
        }

        if(!$id_product){
            $only_update_data = false;
            $sync_images = true;
        }else{
            $only_update_data = true;
        }

        $product = new Product( $id_product );

        foreach ($model->product_data as $prop => $value) {
            if($prop == 'ean13' && $value != ''){
                # ean13
                $product->ean13 = $value[0];
                $this->report->alert( 'ean13', $product->ean13);
            }else if($prop == 'wholesale_price' && $value != ''){
                if( !$only_update_data || ($id_product && $this->updateProductPrices) ){
                    $product->wholesale_price = $model->get('wholesale_price');
                    $this->report->alert( 'wholesale_price', $product->wholesale_price);
                }
            }else if($prop == 'unit_price_tax' && $value != ''){
                # price params
                if( !$only_update_data || ($id_product && $this->updateProductPrices) ){
                    if( $model->get('tax_rules_group') != '' || $model->get('tax_rules_group') != false ){
                        $product->id_tax_rules_group = TaxRulesGroup::getIdByName($model->get('tax_rules_group'));
                    }else{
                        $product->id_tax_rules_group = 1;
                    }
                    $product->price = $value; #self::priceCalculation( $product, $value, true );
                    $this->report->alert( 'id_tax_rules_group', $product->id_tax_rules_group);
                    $this->report->alert( 'price', $product->price);
                  }
            }else if($prop == 'link_rewrite'){
                #link_rewrite
                foreach (Language::getIDs(false) as $id_lang) {
                    if( $value[$id_lang] != '' && isset($product->link_rewrite[$id_lang]) ){
                        $product->link_rewrite[$id_lang] = $value[$id_lang];
                    }else if(isset($product->link_rewrite[$id_lang])){
                        $product->link_rewrite[$id_lang] = $product->link_rewrite[$id_lang] != '' ? $product->link_rewrite[$id_lang] : $dataFormatter->createFriendlyUrl($model->get('name', $id_lang));
                    }
                }
            }else if($prop == 'supplier' && $value != ''){
                # Manufacturer
                $id_manufacturer = Manufacturer::getIdByName($value);
                if( !$id_manufacturer ){
                    $Manufacturer = new Manufacturer();
                    $Manufacturer->name = $value;
                    $Manufacturer->save();
                    $id_manufacturer = $Manufacturer->id;
                }
                $product->id_manufacturer = $id_manufacturer;
            }else if($prop == 'name' || $prop == 'description' || $prop == 'description_short'){
                # Product name or discriptions
                if( $prop == 'name' ){
                  if( !$only_update_data || ($id_product && $this->updateProductName) ){
                      $product->{$prop} = $this->trans($value, $prop);
                      if($id_product)
                          $this->report->log( 'Update product name' );
                  }
                }
                if( $prop == 'description' || $prop == 'description_short' ){
                  if( !$only_update_data || ($id_product && $this->updateProductInfo) ){
                      $product->{$prop} = $this->trans($value, $prop);

                      if($id_product)
                          $this->report->log( 'Update product description' );
                  }
                }
            }else if($prop == 'quantity' || $prop == 'tags' || $prop == 'images'){



            }else if($prop == 'brand' && $value != ''){
                # Manufacturer
                $id_manufacturer = Manufacturer::getIdByName($value);
                if( !$id_manufacturer ){
                    $Manufacturer = new Manufacturer();
                    $Manufacturer->name = $value;
                    $Manufacturer->save();
                    $id_manufacturer = $Manufacturer->id;
                }
                $product->id_manufacturer = $id_manufacturer;
            }else{
                if(property_exists($product, $prop)){
                    if( (is_array($value) && !empty($value)) || ($value != '') ){
                        $product->{$prop} = $value;
                    }
                }
            }
        }

        $product->active = $this->defaults['active'];

        try {
            $result &= $product->save();
            if( !$result ){
                throw new Exception("Fail on update product");
            }
        } catch (\Exception $e) {
            $this->report->result(false);
            $this->report->log($e->getMessage() . ' Name: '.$product->name[$this->context->language->id]);
            return $this->report;
        }

        if( $id_product ){
            $this->report->log( 'Start update product ID:' . $product->id );
        }else{
            $this->report->log( 'Create product ID:' . $product->id );
        }

        $this->updateSyncFusionTable( $product->id );

        if( !$only_update_data || ($id_product && $this->updateCategories) ){

            // Category params
            $ids_categories = [];

            $category_hash = (strlen($model->get('category'))>1) ? md5($model->get('category')) : false;
            if( $category_hash && isset($this->category_association[$category_hash]) ){
                $product->id_category_default = $this->category_association[$category_hash]['target'];
                $ids_categories[] = $product->id_category_default;
            }

            $sub_category_hash = (strlen($model->get('sub_category'))>1) ? md5($model->get('sub_category')) : false;
            $containsCategory = count(array_intersect([$this->category_association[$sub_category_hash]['target']], $ids_categories)) === count([$this->category_association[$sub_category_hash]['target']]);
            if( $sub_category_hash && isset($this->category_association[$sub_category_hash]) && !$containsCategory ){
                $ids_categories[] = $this->category_association[$sub_category_hash]['target'];
            }

            if( !empty($ids_categories) ){
                $product->deleteCategories();
                $category_assoc = $product->addToCategories($ids_categories);
                $this->report->log( 'Cat. IDs: ' . implode(',',$ids_categories) );
                $this->report->alert( 'categorys', count($ids_categories).' categorys' );
            }else{
                $product->deleteCategories();
                $product->id_category_default = (int)$this->defaults['default_category'];
                $category_assoc = $product->addToCategories([(int)$this->defaults['default_category']]);
                $this->report->log( 'Cat. IDs: ' . $this->defaults['default_category'] );
                $this->report->alert( 'categorys', 'Product without categories', true);
            }

            if( !$product->id_category_default || (int)$product->id_category_default < 1){
                $product->id_category_default = 1;
            }

            if($category_assoc){
                $this->report->log( 'Associated Categories' );
                $this->report->log( 'Cat. Default: '.$product->id_category_default );
            }
        }

        # Save weight params
        $product->weight = ($model->get('weight') > 0) ? $model->get('weight') : $product->weight;

        if( (float)$product->weight <= 0 ){
            $this->report->alert( 'weight', 'Product weight is 0', true );
        }else{
            $this->report->alert( 'weight', 'Product weight is ' . $product->weight );
        }

        $result &= $product->save();

        if( $result ){

            # quantity
            $this->updateStock( $product->id, $model->get('quantity') );

            # tags
            if( $model->get('tags') != '' ){
                foreach ($product->name as $id_lang => $name) {
                    Tag::addTags($id_lang, $product->id, $model->get('tags'));
                }
            }else{
                $this->report->alert( 'tags', 'Product without tags' );
            }

            # Images
            if( $sync_images ){
                if( is_array($model->get('combinations')) && !empty($model->get('combinations')) ){
                    #$this->imageFinder( $product, $image_folder, $model->get('images') );
                }else{
                    $this->imageFinder( $product, $image_folder, $model->get('images') );
                }
            }

            # Features
            if( !$only_update_data || ($id_product && $this->updateFeatures) ){
                if( is_array($model->get('features')) && !empty($model->get('features')) ){
                    foreach ($model->get('features') as $feature) {
                        $this->report->log( 'Try to add feature ' . $feature['name'] . ' - '.$feature['value'] );
                        self::addFeatures( $product->id, $feature['name'], $feature['value'], $this->report );
                    }
                    $this->report->alert( 'features', count($model->get('features')).' features' );
                }else{
                    $this->report->alert( 'features', 'Product without features', true );
                }
            }

            # Attributes & Combinations
            if( !$only_update_data || ($id_product && $this->updateCombinations) ){
                if( is_array($model->get('combinations')) && !empty($model->get('combinations')) ){
                    $this->createCombinations($product->id, $model->get('combinations'), $image_folder, $only_update_data);
                    $this->report->alert( 'combinations', count($model->get('combinations')).' combinations' );
                }else{
                    $this->report->alert( 'combinations', 'Product without combinations', true );
                }
            }

            # product visibility
            if (in_array($product->visibility, array('both', 'search')) && Configuration::get('PS_SEARCH_INDEXATION')) {
                Search::indexation(false, $product->id);
            }
        }

        # end
        $result &= self::callExternalSyncHooks( $model, $product, $this->report, $this, $only_update_data );

        self::$process_feed_log[] = '-------------------------------';
        $this->report->log(implode('; <br>', self::$process_feed_log));
        self::$process_feed_log = array();

        return $this->report;
    }

    protected function imageFinder( $product, $image_folder, $images = [] )
    {
        $product_images = array();

        if( empty($images) ){
            // check in uploads folder
            for ($i=1; $i <= 10 ; $i++) {
                $image_path = $image_folder.$product->ean13.'_'.sprintf('%03d', $i).'.jpg';
                if(file_exists($image_path)){
                    $product_images[] = $image_path;
                }
            }
        }else{
            foreach ($images as $image) {
                if(!empty($image)){
                    if( $image_folder != null && file_exists( $image_folder . $image . '.jpg') ){
                        $product_images[] = $image_folder . $image . '.jpg';
                    }else if( $image_folder != null && file_exists( $image_folder . $image . '.JPG') ){
                        $product_images[] = $image_folder . $image . '.JPG';
                    }else if( $image_folder != null && file_exists( $image_folder . $image . '.jpeg') ){
                        $product_images[] = $image_folder . $image . '.jpeg';
                    }else if( $image_folder != null && file_exists( $image_folder . $image . '.JPEG') ){
                        $product_images[] = $image_folder . $image . '.JPEG';
                    }else if( $image_folder != null && file_exists( $image_folder . $image . '.png') ){
                        $product_images[] = $image_folder . $image . '.png';
                    }else if( $image_folder != null && file_exists( $image_folder . $image . '.PNG') ){
                        $product_images[] = $image_folder . $image . '.PNG';
                    }else if( $this->checkRemoteFile($image) ){
                        if( $image_file = file_get_contents($image) ){
                            $image_path = _PS_TMP_IMG_DIR_.md5($image).'.jpg';
                            file_put_contents($image_path, $image_file);
                            $product_images[] = $image_path;
                        }
                    }
                }
            }
        }

        if( !empty($product_images) && $product->id ){
            $product->deleteImages();
            $this->report->log( 'Deleted old images');
            foreach ($product_images as $image) {
                self::$process_feed_log[] = 'Add: '.$image;
            }
        }

        try{
            $create_images = self::syncImages($product->id, $product_images);
        } catch (\Exception $e) {
            #$this->report->alert( 'images', 'Fail create images' );
            #self::$process_feed_log[] = 'Fail create images';
            #$product->deleteImages();
            $create_images = true;
            $this->report->log( $e->getMessage() );
            $this->report->alert( 'images', 'Duplicate entry', true );
            $this->report->log( 'Warnings when create images. Try disable debug mode.');
        }

        if( empty($product_images) ){
            $this->report->alert( 'images', 'No images', true );
        }else if($create_images){
            $this->report->alert( 'images', 'Create '.count($product_images).' images' );
        }else{
            $this->report->alert( 'images', 'Fail create images' );
        }

        if($create_images){
            $this->report->log( 'New images created' );
        }
    }

    protected function createCombinations( $id_product, Array $combinations, $image_folder = false, $only_update_data = false )
    {
        if (!Combination::isFeatureActive()) {
            return true;
        }

        $CombinationImport = new CombinationImport($id_product);
        $CombinationImport->combinations = $combinations;

        $CombinationImport->setMask(['group', 'attribute', 'reference', 'ean13', 'price', 'quantity', 'weight']);
        $CombinationImport->imageFolder($image_folder);
        $result = $CombinationImport->import( ($only_update_data?$this->updateImages:true) );

        if( $result > 0 ){
            $this->sync_images = false;
        }

        $this->report->log('Create '.$result.' combinations');
    }

    protected static function createFeatures( $id_product, $name, $report = false )
    {
        $Feature = new Feature();
        foreach (Language::getIDs(false) as $id_lang) {
            $Feature->name[$id_lang] = $name;
        }
        return $Feature->save();
    }

    protected static function createFeaturesValue( $id_product, $value, $report = false )
    {
        // Feature doesn't exist, create it
        $feature_value = new FeatureValue();
        $feature_value->id_feature = (int) $idFeature;
        #$feature_value->custom = true;
        $feature_value->value = array_fill_keys(Language::getIDs(false), $value);
        $feature_value->add();

        if( $report!==false )
            $report->log( 'Feature '.$feature['value'].' created id:' . $feature_value->id );

        return $feature_value->id;
    }

    protected static function addFeatures( $id_product, $name, $value, $report = false )
    {
        $features = Feature::getFeatures( Context::getContext()->language->id );
        $find = false;
        foreach ($features as $feature) {
            if( strtoupper($feature['name']) == strtoupper($name) ){
                $find = true;
            }
        }

        if( !Validate::isGenericName($name) ){
            $report->log( 'Features '.$name.' have invalid name' );
            $report->alert( 'features', 'Features '.$name.' have invalid name' );
            return false;
        }

        if( !Validate::isGenericName($value) ){
            $report->log( 'Features value '.$value.' have invalid name' );
            $report->alert( 'features', 'Features value '.$value.' have invalid name' );
            return false;
        }

        if( !$find ){
            if( $report!==false )
                $report->log( 'Features '.$name.' not exist' );

            if( self::createFeatures($id_product, $name, $report) ){
                if( $report!==false )
                    $report->log( 'Fail create feature'.$name.'' );
            }
        }

        $features = Feature::getFeatures( Context::getContext()->language->id );
        $idLang = Context::getContext()->language->id;

        foreach ($features as $feature) {
            if( strtoupper($feature['name']) == strtoupper($name) ){
                $find = true;
                $idFeature = $feature['id_feature'];
                $idFeatureValue = Db::getInstance()->getValue('
                SELECT fv.`id_feature_value`
                FROM ' . _DB_PREFIX_ . 'feature_value fv
                LEFT JOIN ' . _DB_PREFIX_ . 'feature_value_lang fvl ON (fvl.`id_feature_value` = fv.`id_feature_value` AND fvl.`id_lang` = ' . (int) $idLang . ')
                WHERE `value` = \'' . pSQL($value) . '\'
                AND fv.`id_feature` = ' . (int) $idFeature . '
                AND fv.`custom` = 0
                GROUP BY fv.`id_feature_value`');
                if(!$idFeatureValue){
                    #$idFeatureValue = self::createFeaturesValue( $id_product, $value, $report );
                    $idFeatureValue = FeatureValue::addFeatureValueImport($idFeature, $value, $id_product, $idLang);
                }
                if( $idFeatureValue && $report!==false ){
                    $report->log( 'Feature '.$name . ' - ' . $value.' added' );
                }
                Product::addFeatureProductImport($id_product, $idFeature, $idFeatureValue);
            }
        }
    }

    protected static function callExternalSyncHooks( $model, $product, $report, $psync, $only_update_data )
    {
        $hook_result = Hook::exec('syncEntryProduct', array( 'model' => $model, 'product' => $product, 'report' => $report, 'psync' => $psync, 'only_update_data' => $only_update_data ));

        if( is_string($hook_result) && $hook_result != '' ){
            self::$process_feed_log[] = $hook_result;
        }
        return true;
    }

    public static function syncImages($id_product, $product_images)
    {
        if(!empty($product_images)){
            $final_images = array();
            foreach ($product_images as $key => $product_image) {
                $imageNew = new Image();
                $imageNew->id_product   = $id_product;
                $imageNew->position     = ((int)$key + 1);
                $imageNew->cover        = ( (int)$key === 0 ? true : false );
                if ( $imageNew->save() ) {
                    $newPath = $imageNew->getPathForCreation();
                    if( !copy($product_image, $newPath . '.jpg') ){
                      throw new PrestaShopException("Unable to copy image to destination folder");
                    }
                    $final_images[] = $imageNew->id;
                }
                unset($imageNew);
            }
            return self::generateProductImages( $final_images );
        }
        return true;
    }

    public static function generateProductImages($images)
    {
        $generate_hight_dpi_images = (bool) Configuration::get('PS_HIGHT_DPI');
        $imagesTypes = ImageType::getImagesTypes('products');
        $dir = _PS_PROD_IMG_DIR_;
        foreach ($images as $image) {
            $imageNew = new Image($image);
            $existing_img = $dir . $imageNew->getExistingImgPath() . '.jpg';

            if (file_exists($existing_img) && filesize($existing_img)) {
                foreach ($imagesTypes as $imageType) {
                    if (!file_exists($dir . $imageNew->getExistingImgPath() . '-' . stripslashes($imageType['name']) . '.jpg')) {
                        if (!ImageManager::resize($existing_img, $dir . $imageNew->getExistingImgPath() . '-' . stripslashes($imageType['name']) . '.jpg', (int) $imageType['width'], (int) $imageType['height'])) {
                            self::$process_feed_log[] = 'Fail resize image';
                            return false;
                        }
                        if ($generate_hight_dpi_images) {
                            if (!ImageManager::resize($existing_img, $dir . $imageNew->getExistingImgPath() . '-' . stripslashes($imageType['name']) . '2x.jpg', (int) $imageType['width'] * 2, (int) $imageType['height'] * 2)) {
                                self::$process_feed_log[] = 'Fail generate hight dpi image';
                                return false;
                            }
                        }
                    }
                }
            }
        }
        return true;
    }

    protected function checkRemoteFile($url)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL,$url);
        // don't download content
        curl_setopt($ch, CURLOPT_NOBODY, 1);
        curl_setopt($ch, CURLOPT_FAILONERROR, 1);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);

        $result = curl_exec($ch);
        curl_close($ch);
        if($result !== FALSE){
            return true;
        } else {
            return false;
        }
    }

    private function trans( $txt, $prop )
    {
        if( is_array($txt) ){
            foreach ($txt as &$value) {
                $value = $this->trans( $value, $prop );
            }
        }else{
            if( $this->translate_engine && $this->translate_engine->can($prop) ){
                $txt = $this->translate_engine->translate($txt);
                // Converter entidades HTML para caracteres
                $txt = html_entity_decode($txt, ENT_QUOTES, 'UTF-8');
                // Garantir que o texto esteja em UTF-8
                $txt = mb_convert_encoding($txt, 'UTF-8', 'UTF-8');
            }
        }
        return $txt;
    }

    public function setTranslateEngine( $engine )
    {
        $this->translate_engine = $engine;
        return $this;
    }
}
