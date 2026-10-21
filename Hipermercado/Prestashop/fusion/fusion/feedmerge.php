<?php

    include_once('../../config/config.inc.php');
    include_once('../../init.php');

    $config = json_decode(file_get_contents('config/feedmerge.json'), true);

    $fusion = Module::getInstanceByName('fusion');

    # If config file is empty or invalid, can not run

    if( !$config || empty($config) || !isset($config['token']) || !isset($config['modules']) )
        die('Parameters not configured');

    # Validate acces by token
    if( $config['token'] == false || $config['token'] != Tools::getValue('t') )
        die('Invalid secure token');


    $cron_flag = new \FusionStoreBundle\CronJob\Flag(Context::getContext(), true);
   if($cron_flag->is_running()) {
        
        Mail::Send(
            (int)(Configuration::get('PS_LANG_DEFAULT')),
            'newsletter',
            'Feedmerge cron running already!!',
            array(
                '{firstname}' => '',
                '{lastname}' => '',
                '{message}' => 'Neste momento já se encontra um feedmerge a correr e a flag está activa',
            ),
            'geral@hipermercado.pt',
            null,
            Configuration::get('PS_SHOP_EMAIL'),
            Configuration::get('PS_SHOP_NAME'),
            null,
            null,
            _PS_MAIL_DIR_,
            true
        );


       die('Feedmerge cron running already!!');
   }
   $cron_flag->running();
    
    $feed_file = _PS_ROOT_DIR_.'/modules/fusion/mergedfeed.ffusion';

    $currentBatch = isset($_GET['batch']) ? (int)$_GET['batch'] : 0;
    $usecache = Tools::getValue('usecache', ($currentBatch > 0) ? true : false);

    if( !$usecache )
        file_put_contents($feed_file, '[]');

    $result = true;
    $module_ = [];
    $defaults_categorys = [];

    if (!file_exists('./logs/feedmerge_'.date("Y-m-d").'.log')) {
        touch('./logs/feedmerge_'.date("Y-m-d").'.log');
    }


    if($currentBatch == 0) {
        $log  = date("Y-m-d H:i:s")." --------------INIT FEEDMERGE--------------".PHP_EOL.
            date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL;
        file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    }

    if( !$usecache ){
        foreach ($config['modules'] as $entry) {
            $module_[$entry['module']] = Module::getInstanceByName($entry['module']);
            if( $module_[$entry['module']]->active && $module_[$entry['module']] instanceof FusionStoreBundle\Module\ProductsApiModule ){

                # Get Merged File
                $feedmerged = json_decode(file_get_contents( $feed_file ), true);

                # Get Product Feed from Module
                $feed = $module_[$entry['module']]->getProductsFeed( true, true ); # Force refresh time stamp, ignore cached feed file

                $log  = date("Y-m-d H:i:s")." Supplier: ".$entry['module'].' ('.count($feed).')'.PHP_EOL;
                file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
                foreach ($feed as $key => $product) {
                   
                    if( isset($product['ean13']) && $product['ean13'] != '' && strlen($product['ean13']) == 13 ){
                        if(isset($feedmerged[$product['ean13']])){
                            $price_is_better = ((float)$product['unit_price'] < (float)$feedmerged[$product['ean13']]['unit_price']);
                            $have_more_qty = ((int)$product['quantity'] >= (int)$feedmerged[$product['ean13']]['quantity']);

                            # If price is better and quantity is more than atual
                            # Or atual quantity is Zero
                            # Use the new data from feed
                            if( ( (int)$feedmerged[$product['ean13']]['quantity'] === 0 )
                                || ( $price_is_better && (int)$product['quantity'] > 0 )
                            ){
                                $compare_data = $feedmerged[$product['ean13']]['compare_data'];
                                $feedmerged[$product['ean13']] = $product;
                                $feedmerged[$product['ean13']]['quantity'] = (int)$product['quantity'];
                                $feedmerged[$product['ean13']]['compare_data'] = $compare_data;
                                $feedmerged[$product['ean13']]['module'] = [
                                    'module' => $module_[$entry['module']]->name,
                                    'source' => $module_[$entry['module']]->displayName
                                ];
                            }
                        }else{
                            # Is not present in file, so, Add
                            $feedmerged[$product['ean13']] = $product;
                            $feedmerged[$product['ean13']]['quantity'] = (int)$product['quantity'];
                            $feedmerged[$product['ean13']]['compare_data'] = [];
                            $feedmerged[$product['ean13']]['module'] = [
                                'module' => $module_[$entry['module']]->name,
                                'source' => $module_[$entry['module']]->displayName
                            ];
                        }
                        $feedmerged[$product['ean13']]['compare_data']['module_'.$module_[$entry['module']]->name] = [
                            'quantity' => (int)$product['quantity'],
                            'unit_price' => (float)$product['unit_price'],
                            'wholesale_price' => (float)$product['wholesale_price']
                        ];
                      
                    }
                }

                # Close Merged File
                $result &= file_put_contents($feed_file, json_encode($feedmerged) );
                #$defaults_categorys[] = (int)$module_[$entry['module']]->default_category;
            }
        }
    }

    $productFeed = json_decode(file_get_contents( $feed_file ), true);
    $sizeBatch = 2000; // Tamanho de cada batch
    $totalBatches = ceil(count($productFeed) / $sizeBatch); // Total de batches

    try {
        $log  = date("Y-m-d H:i:s")." Init StockPrice Batch (".$currentBatch." of ".($totalBatches - 1).")".PHP_EOL;
        file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        
        $stockprice = new \FusionStoreBundle\CronJob\StockPrice( Context::getContext() );

        #$stockprice->catDefault($defaults_categorys);
        $stockprice->disableIfNoStock( (bool)Configuration::get('FUSION_DISABLE_OUTSTOCK_PRODUCTS_ON_SYNC', 1) );
        $stockprice->productDataFeed( $productFeed );

        ob_end_clean();
        $stockprice->run();

        $log  = date("Y-m-d H:i:s")." End StockPrice Batch (".$currentBatch." of ".($totalBatches - 1).")".PHP_EOL;
        file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    } catch (\Exception $e) {
        $log  = date("Y-m-d H:i:s")." StockPrice Batch (".$currentBatch.") Exception: (".$_SERVER['REDIRECT_STATUS'].") ".$e->getMessage().PHP_EOL;
        file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    }


    // try {
    //     // $log  = date("Y-m-d H:i:s")." Init FeedGenerator".PHP_EOL;
    //     // file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        
    //     // $FeedGenerator = new \FusionStoreBundle\CronJob\FeedGenerator( Context::getContext() );
    //     // $FeedGenerator->run();

    //     // $log  = date("Y-m-d H:i:s")." End FeedGenerator".PHP_EOL;
    //     // file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    // } catch (\Exception $e) {
    //     $log  = date("Y-m-d H:i:s")." FeedGenerator Exception: (".$_SERVER['REDIRECT_STATUS'].") ".$e->getMessage().PHP_EOL;
    //     file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    // }

    if($currentBatch == ($totalBatches - 1)) {
        $log  = date("Y-m-d H:i:s")." --------------END FEEDMERGE---------------".PHP_EOL;
        file_put_contents('./logs/feedmerge_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    }
    $cron_flag->finish();

    die();

?>
