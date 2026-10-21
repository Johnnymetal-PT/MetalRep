<?php

namespace FusionStoreBundle\CronJob;

use Context;
use Module;
use DbQuery;
use Db;
use Manufacturer;
use Supplier;
use ProductSupplier;
use Product;
use FusionStoreBundle\Import\ProductModel;
use FusionStoreBundle\Import\ProductSync as ImportProductSync;

class StockPrice
{
    protected $rustart = null;

    protected $context = null;

    protected $product_feed = null;

    protected $defaults_categorys = null;

    protected $disable_products_out_of_stock = false;

    protected $assoc_supplier = true;

    public function __construct( Context $context )
    {
        $this->context = $context;
        $this->rustart = getrusage();
    }

    public function productDataFeed( Array $product_data_feed )
    {
        $this->product_feed = $product_data_feed;
        return $this;
    }

    public function disableIfNoStock( Bool $disable_products_out_of_stock )
    {
        $this->disable_products_out_of_stock = $disable_products_out_of_stock;
        return $this;
    }

    public function catDefault( Array $defaults_categorys )
    {
        $this->defaults_categorys = $defaults_categorys;
        return $this;
    }

    public function run()
    {
        $currentBatch = isset($_GET['batch']) ? (int)$_GET['batch'] : 0;

        // Configurações do Batch
        $sizeBatch = 2000; // Tamanho de cada batch
        $totalBatches = ceil(count($this->product_feed) / $sizeBatch); // Total de batches
        // $currentBatch = $this->getProgress(); // Carrega o último batch processado

        try {

            if ($currentBatch >= $totalBatches) {
                http_response_code(200); // OK
                echo "Processamento concluído.\n";
                exit;
            }

            // Calcula os itens do batch atual
            $init = $currentBatch * $sizeBatch;
            $end = min(($init + $sizeBatch), count($this->product_feed));
            $productsBatch = array_slice($this->product_feed, $init, $end - $init);

            // Processa os itens do batch
            echo "Processando batch {$currentBatch}...\n";
            foreach ($productsBatch as $product) {
                echo "Processando item: ".$product['ean13']."\n";
                $this->processProduct($product);
            }

            // Informa o próximo batch a ser processado
            $nextBatch = $currentBatch + 1;
            if ($nextBatch < $totalBatches) {
                echo "Batch {$currentBatch} concluído. Próximo batch: {$nextBatch}.\n";
                $this->saveProgress($nextBatch);
                http_response_code(202); // Accepted (indica que ainda há trabalho)
            } else {
                echo "Todos os batches foram processados.\n";
                if( file_exists(_PS_ROOT_DIR_.'/modules/fusion/logs/feedmergeCurrentBatch.txt') ){
                    @unlink(_PS_ROOT_DIR_.'/modules/fusion/logs/feedmergeCurrentBatch.txt'); // Remove o progresso ao finalizar
                }
                http_response_code(200); // OK
            }

        } catch (\Exception $e) {

            Mail::Send(
                (int)(Configuration::get('PS_LANG_DEFAULT')),
                'newsletter',
                'ALERTA - Erro ao correr o Feedmerge!',
                array(
                    '{firstname}' => 'Batch => ',
                    '{lastname}' => $currentBatch . ' de ' . $totalBatches,
                    '{message}' => "Erro: {$e->getMessage()}",
                ),
                'geral@hipermercado.pt',
                null,
                Configuration::get('PS_SHOP_EMAIL'),
                Configuration::get('PS_SHOP_NAME'),
                null,
                null,
                _PS_MAIL_DIR_,
                true,
                null,
                'joao.rosa@pipecodes.com'
            );


            echo "Erro: {$e->getMessage()}\n";
            echo "Progresso salvo. Reinicie o script para continuar.\n";
            $this->saveProgress($currentBatch + 1);
        }

        $ru = getrusage();
        // echo "Update " . $count_update .
        //     " products\n";
        echo "This process used " . $this->rutime($ru, $this->rustart, "utime") .
            " ms for its computations\n";
        echo "It spent " . $this->rutime($ru, $this->rustart, "stime") .
            " ms in system calls\n";
    }

    private function processProduct($product) {
        try {
            if( isset($product['ean13']) && $product['ean13'] != '' && strlen($product['ean13']) == 13 ){

                $sql = new DbQuery();
                $sql->select('p.`id_product`, p.`id_manufacturer`, p.`id_supplier`, ps.`id_category_default`, p.`out_of_stock`');
                $sql->from('product', 'p');
                $sql->leftJoin('product_shop', 'ps', 'ps.id_product = p.id_product');
                $sql->where('p.`ean13` = \'' . pSQL($product['ean13']) . '\'' );
                $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->getRow($sql);

                if( $result && isset($result['id_product']) ){

                    $fsync = \FusionStoreBundle\Entity\FusionSync::getByProductID( (int)$result['id_product'] );
                    
                    if( (bool)$fsync->skip_product == false ){

                        # Fix price
                        $wholesale_price= str_replace(',','.',$product['wholesale_price']);
                        $unit_price = str_replace(',','.',$product['unit_price']);
                        $quantity = $product['quantity'];

                        if( ($this->disable_products_out_of_stock && (int) $quantity == 0)  || ((float)$unit_price == 0) ){
                            $extra_sql = ' p.`active` = 0, ps.`active` = 0 ';
                        }else{
                            $extra_sql = ' p.`active` = 1, ps.`active` = 1 ';
                        }

                        if( (int) $quantity === 0 &&  (int) $result['out_of_stock'] !== 1 ){
                            $extra_sql .= ', p.`visibility` = \'none\', ps.`visibility` = \'none\' ';
                        }else{
                            $extra_sql .= ', p.`visibility` = \'both\', ps.`visibility` = \'both\' ';
                        }

                        $query = 'UPDATE `'._DB_PREFIX_.'product` as p
                        INNER JOIN `'._DB_PREFIX_.'product_shop` AS ps ON p.`id_product` = ps.`id_product`
                        INNER JOIN `'._DB_PREFIX_.'stock_available` AS sa ON p.`id_product` = sa.`id_product`
                        SET p.`wholesale_price` = '.(float)$wholesale_price.', p.`price` = '.(float)$unit_price.',
                        ps.`wholesale_price` = '.(float)$wholesale_price.', ps.`price` = '.(float)$unit_price.',
                        sa.`quantity` = '.$quantity.', '.$extra_sql.' WHERE p.`id_product` = '.(int)$result['id_product'].'; ';

                        $update_result_p = Db::getInstance()->execute($query);

                        # Update Fusion Entry
                        if( !$fsync ){
                            $fsync = new \FusionStoreBundle\Entity\FusionSync();
                            $fsync->id_product = $result['id_product'];
                        }
                        
                        $fsync->module = $product['module']['module'];
                        $fsync->source = $product['module']['source'];

                        $update_result = $fsync->save();

                        if( is_array($this->defaults_categorys) && !empty($this->defaults_categorys) ){
                            if( in_array( (int)$result['id_category_default'], $this->defaults_categorys) ){
                                # produto ainda na categoria por ativar,
                                $query = 'UPDATE `'._DB_PREFIX_.'product` as p
                                INNER JOIN `'._DB_PREFIX_.'product_shop` AS ps ON p.`id_product` = ps.`id_product`
                                SET p.`active` = 0, ps.`active` = 0 WHERE p.`id_product` = '.(int)$result['id_product'].';';
                                $update_result &= Db::getInstance()->execute($query);
                            }
                        }

                        if( is_array($product['brand']) && isset($product['brand']['Valor']) ){
                            $brand = $product['brand']['Valor'];
                        }else{
                            $brand = $product['brand'];
                        }

                        # Assign Brand if not exists
                        if( !$result['id_manufacturer'] && $brand != ''){
                            $id_manufacturer = Manufacturer::getIdByName($brand);
                            if( !$id_manufacturer ){
                                $Manufacturer = new Manufacturer();
                                $Manufacturer->name = $product['brand'];
                                $Manufacturer->save();
                                $id_manufacturer = $Manufacturer->id;
                            }
                            $obj_product = new Product($result['id_product']);
                            $obj_product->id_manufacturer = $id_manufacturer;
                            $obj_product->save();
                        }

                        if( $this->assoc_supplier && isset($result['id_supplier']) ){

                            $id_supplier = Supplier::getIdByName($product['module']['source']);

                            # If not exist, create supplier
                            if( !$id_supplier ){
                                $Supplier = new Supplier();
                                $Supplier->name = $product['module']['source'];
                                $Supplier->active = 1;
                                $Supplier->save();
                                $id_supplier = $Supplier->id;
                            }

                            // build query
                            $query = new DbQuery();
                            $query->select('ps.id_product_supplier, ps.id_product');
                            $query->from('product_supplier', 'ps');
                            $query->where('ps.id_product = ' . (int) $result['id_product']);

                            $supplier_result = Db::getInstance(_PS_USE_SQL_SLAVE_)->getRow($query);

                            if( $supplier_result ){
                                $ProductSupplier = new ProductSupplier((int)$supplier_result['id_product_supplier']);
                                $ProductSupplier->id_supplier = $id_supplier;
                            }else{
                                $ProductSupplier = new ProductSupplier();
                                $ProductSupplier->id_product = $result['id_product'];
                                $ProductSupplier->id_product_attribute = 0;
                                $ProductSupplier->id_supplier = $id_supplier;
                            }

                            $ProductSupplier->product_supplier_price_te = (float)$unit_price;
                            $ProductSupplier->save();

                            $reference = $product['reference'];

                            $product_query = 'UPDATE `'._DB_PREFIX_.'product` as p
                            SET p.`id_supplier` = '.(int)$id_supplier.',
                            
                            p.`supplier_reference` = \''.$reference.'\'
                            WHERE p.`id_product` = '.(int)$result['id_product'].'; ';

                            $update_result &= Db::getInstance()->execute($product_query);
                        }

                        //$image_result = $this->fixImageProblems( $product, $result );
                    }
                }
            }
        } catch (\Exception $e) {
            $log  = date("Y-m-d H:i:s")." StockPrice Supplier Exception: ".$e->getMessage().PHP_EOL;
            file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        }
    }

    // Função para salvar a posição do batch atual
    private function saveProgress($currentBatch) {
        file_put_contents(_PS_ROOT_DIR_.'/modules/fusion/logs/feedmergeCurrentBatch.txt', $currentBatch);
    }

    private function fixImageProblems( $product, $result )
    {
        $id_product = $result['id_product'];
        $query = new DbQuery();
        $query->select('*');
        $query->from('image');
        $query->where('id_product = ' . (int) $id_product);

        $result = Db::getInstance()->executeS($query);
        if( $result ){
            return true;
        }

        $product_images = [];
        $images = (isset($product['images']) && !empty($product['images'])) ? $product['images'] : [];
      	if(!is_array($images)){
          	$images = explode(',',$images);
        }

        if(!empty($images)){
            foreach ($images as $image) {
                if( $this->checkRemoteFile($image) && @getimagesize($image) ){
                  if($image_file = file_get_contents($image) ){
                        $image_path = _PS_TMP_IMG_DIR_.md5($image).'.jpg';
                        file_put_contents($image_path, $image_file);
                        $product_images[] = $image_path;
                    }
                }
            }
        }

      	if(!empty($product_images)){
          	return ImportProductSync::syncImages($id_product, $product_images);
        }

      	return true;
    }

    protected function checkRemoteFile($url) {
		if (!$fp = curl_init($url)) return false;
		return true;
  	}

    # Script end
    protected function rutime($ru, $rus, $index) {
        return ($ru["ru_$index.tv_sec"]*1000 + intval($ru["ru_$index.tv_usec"]/1000))
         -  ($rus["ru_$index.tv_sec"]*1000 + intval($rus["ru_$index.tv_usec"]/1000));
    }

}
