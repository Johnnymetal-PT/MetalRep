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

    // $cron_flag = (new \FusionStoreBundle\CronJob\Flag(Context::getContext()))->running();

    $feed_file = _PS_ROOT_DIR_.'/modules/fusion/mergedfeed.ffusion2';

    $usecache = Tools::getValue('usecache', false);

    if( !$usecache )
        file_put_contents($feed_file, '[]');

    $result = true;
    $module_ = [];
    $defaults_categorys = [];

    if( !$usecache ){
        foreach ($config['modules'] as $entry) {
            $module_[$entry['module']] = Module::getInstanceByName($entry['module']);
            if( $module_[$entry['module']]->active && $module_[$entry['module']] instanceof FusionStoreBundle\Module\ProductsApiModule ){
                
                # Get Merged File
                $feedmerged = json_decode(file_get_contents( $feed_file ), true);

                # Get Product Feed from Module
                $feed = $module_[$entry['module']]->getProductsFeed( true, true ); # Force refresh time stamp, ignore cached feed file
                print_r( "Supplier: ".$entry['module'].' ('.count($feed).')'.PHP_EOL );
                
                foreach ($feed as $key => $product) {
                   
                    if( isset($product['ean13']) && $product['ean13'] != '' && strlen($product['ean13']) == 13 && $product['ean13'] == '3838782640445'){

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

    die(print_r( json_decode(file_get_contents( $feed_file ), true) ));

    // $stockprice = new \FusionStoreBundle\CronJob\StockPrice( Context::getContext() );

    // #$stockprice->catDefault($defaults_categorys);
    // $stockprice->disableIfNoStock( (bool)Configuration::get('FUSION_DISABLE_OUTSTOCK_PRODUCTS_ON_SYNC', 1) );
    // $stockprice->productDataFeed( json_decode(file_get_contents( $feed_file ), true) );

    // ob_end_clean();
    // $stockprice->run();


    // $FeedGenerator = new \FusionStoreBundle\CronJob\FeedGenerator( Context::getContext() );
    // $FeedGenerator->run();

    // $cron_flag->finish();

    die();

?>
