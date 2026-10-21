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

    $feed_file = _PS_ROOT_DIR_.'/modules/fusion/mergedfeed.ffusion';

    $feedmerged = json_decode(file_get_contents( $feed_file ), true);

    $jsonData = [];
    $jsonData[] = ['id', 'ean13', 'quantity', 'price']; // cabeçalho
    $productCount = 0;

    foreach ($feedmerged as $key => $product) {
        if( $product['module']['module'] === 'inteldisser' ) {
            $id_product = \FusionStoreBundle\Import\ProductSync::findProductByEan( $product['ean13'] );

            if (!empty($id_product) && Validate::isUnsignedInt($id_product)) {
                $prod = new Product($id_product);
                $product_price = $prod->getPrice(true, null, 2);

                $jsonData[] = [
                    $id_product,
                    $product['ean13'],
                    $product['quantity'],
                    $product_price
                ];

                $productCount++;
            }
        }
    }

    if ($productCount > 0) {
        // Criar CSV em memória
        $fp = fopen('php://temp', 'r+');
        foreach ($jsonData as $line) {
            fputcsv($fp, $line);
        }
        rewind($fp);
        $csvContent = stream_get_contents($fp);
        fclose($fp);

        // Preparar anexo como CSV
        $file_attachment = [
            'content' => $csvContent,
            'name' => 'eldisser_products.csv',
            'mime' => 'text/csv',
        ];


        // $file_attachment['content'] = json_encode($jsonData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        // $file_attachment['name'] = 'eldisser_products.json';
        // $file_attachment['mime'] = 'application/json';

        Mail::Send(
            (int)(Configuration::get('PS_LANG_DEFAULT')),
            'newsletter',
            'Produtos Eldisser',
            array(
                '{firstname}' => 'António',
                '{lastname}' => 'Oliveira',
                '{message}' => 'Ficheiro de produtos da Eldisser (CSV em anexo)',
            ),
            'geral@hipermercado.pt',
            null,
            Configuration::get('PS_SHOP_EMAIL'),
            Configuration::get('PS_SHOP_NAME'),
            $file_attachment,
            null,
            _PS_MAIL_DIR_,
            true,
            null,
        );
    }