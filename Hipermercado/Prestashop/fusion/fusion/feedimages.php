<?php
    include_once('../../config/config.inc.php');
    include_once('../../init.php');

    $GLOBALS['images_imported'] = [];
    $GLOBALS['images_imported_counter'] = [];

    function checkRemoteFile($url)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL,$url);
        // don't download content
        curl_setopt($ch, CURLOPT_NOBODY, 1);
        curl_setopt($ch, CURLOPT_FAILONERROR, 1);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);

        $result = curl_exec($ch);
        curl_close($ch);
        if($result !== FALSE)
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    function syncImages($id_product, $product_images)
    {

      if(!empty($product_images)){

        $GLOBALS['images_imported'][$id_product] = 1;
        $GLOBALS['images_imported_counter'][$id_product] = 1;

        $image_count = 1;

        $final_images = array();

        foreach ($product_images as $product_image) {

          if($GLOBALS['images_imported'][$id_product] == 1){
              $cover = 1;
          }else{
              $cover = 0;
          }

          $imageNew = new Image();
          $imageNew->id_product = $id_product;
          $imageNew->position = $GLOBALS['images_imported_counter'][$id_product];
          $imageNew->cover = $cover;

          if ( $imageNew->add() ) {
            $newPath = $imageNew->getPathForCreation();

            if( !copy($product_image, $newPath . '.jpg') ){
              throw new PrestaShopException("Unable to copy image to destination folder");
            }

            $final_images[] = $imageNew->id;
          }
          $GLOBALS['images_imported_counter'][$id_product]++;
          $GLOBALS['images_imported'][$id_product]++;
          $image_count++;
        }
        return generateProductImages( $final_images );
      }
      return true;
    }

    function generateProductImages($images)
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
                return false;
              }
              if ($generate_hight_dpi_images) {
                if (!ImageManager::resize($existing_img, $dir . $imageNew->getExistingImgPath() . '-' . stripslashes($imageType['name']) . '2x.jpg', (int) $imageType['width'] * 2, (int) $imageType['height'] * 2)) {
                  return false;
                }
              }
            }
          }
        }
      }
      return true;
    }


    $config = json_decode(file_get_contents('config/feedmerge.json'), true);

    # If config file is empty or invalid, can not run
    if( !$config || empty($config) || !isset($config['token']) || !isset($config['modules']) )
       die('Parameters not configured');

    # Validate acces by token
    if( $config['token'] == false || $config['token'] != Tools::getValue('t') )
       die('Invalid secure token');

    $cron_flag = (new \FusionStoreBundle\CronJob\Flag(Context::getContext()))->running();

    $result = true;
    $counter = 0;
    $counter_2 = 0;

    if (!file_exists('./logs/feedimages_'.date("Y-m-d").'.log')) {
        touch('./logs/feedimages_'.date("Y-m-d").'.log');
    }
    
    $log  = date("Y-m-d H:i:s")." --------------INIT FEEDIMAGES--------------".PHP_EOL.
            date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL;
    file_put_contents('./logs/feedimages_'.date("Y-m-d").'.log', $log, FILE_APPEND);

    foreach ($config['modules'] as $entry) {
        $module = null;
        $module = Module::getInstanceByName($entry['module']);

        if( $module->active && $module instanceof FusionStoreBundle\Module\ProductsApiModule ){

            # Get Product Feed from Module
            $feed = $module->getProductsFeed( true, true ); # Force refresh time stamp, ignore cached feed file

            foreach ($feed as $key => $product) {
                try {
                    if( isset($product['ean13']) ){
                        $id_product = \FusionStoreBundle\Import\ProductSync::findProductByEan( $product['ean13'] );

                        if( $id_product ){

                            $sql = new DbQuery();
                            $sql->select('`id_product`');
                            $sql->from('image');

                            $sql->where('`id_product` = '.(int)$id_product );
                            $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

                            if(!$result && empty($result) && isset($product['images']) && $product['images'] != '' && $product['images'] != ' ' ){

                                $product_images = array();
                                $images = $product['images'];

                                if( !is_array( $images ) ){
                                    $images = explode(',',$images);
                                }
                                echo "product data";
                                var_dump($product['images']);

                                if( !empty($images) ){
                                    echo "Result images: ";
                                    var_dump($result);
                                    
                                    foreach ($images as $image) {
                                        if(!empty($image)){
                                            $image = trim($image);

                                            if( checkRemoteFile($image) ){
                                                if( $image_file = file_get_contents($image) ){
                                                    $image_path = _PS_TMP_IMG_DIR_.md5($image).'.jpg';
                                                    file_put_contents($image_path, $image_file);
                                                    $product_images[] = $image_path;
                                                }
                                            }else{
                                                echo "not found";
                                                var_dump($image);
                                            }
                                        }
                                    }
                                }

                                if(!empty($product_images)){
                                    $counter_2 ++;
                                }

                                syncImages($id_product, $product_images);
                                $counter ++;
                            }
                        }
                    }
                } catch (\Exception $e) {
                    $log  = date("Y-m-d H:i:s")." Feedimages Exception: ".$e->getMessage().PHP_EOL;
                    file_put_contents('./logs/feedimages_'.date("Y-m-d").'.log', $log, FILE_APPEND);
                }
            }
        }
    }

    $log  = date("Y-m-d H:i:s")." --------------END FEEDIMAGES---------------".PHP_EOL;
    file_put_contents('./logs/feedimages_'.date("Y-m-d").'.log', $log, FILE_APPEND);

    #ob_end_clean();
    echo "Find ".$counter." products with no image. ";
    echo "Update ".$counter_2." products images";
    $cron_flag->finish();
    die();

?>
