<?php
include_once('../../config/config.inc.php');
include_once('../../init.php');

use PrestaShop\PrestaShop\Adapter\Import\ImportDataFormatter;
use PrestaShop\PrestaShop\Core\ConfigurationInterface;

$sql = new DbQuery();
$sql->select('p.`id_product`, pl.`link_rewrite`, pl.`name`');
$sql->from('product', 'p');
$sql->leftJoin('product_shop', 'ps', 'ps.id_product = p.id_product');
$sql->leftJoin('product_lang', 'pl', 'pl.id_product = p.id_product');
$sql->where('p.`active` = 1 AND ps.`active` = 1 AND pl.`link_rewrite` REGEXP \'[^a-zA-Z0-9-_]|^$\' AND pl.`id_lang` = 1 ' );
$result = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

if (!file_exists('./logs/fixurl_'.date("Y-m-d").'.log')) {
    touch('./logs/fixurl_'.date("Y-m-d").'.log');
}


$log  = date("Y-m-d H:i:s")." --------------INIT FIXURL--------------".PHP_EOL.
        date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL;
file_put_contents('./logs/fixurl_'.date("Y-m-d").'.log', $log, FILE_APPEND);


if($result){
    Configuration::updateGlobalValue('PS_ALLOW_ACCENTED_CHARS_URL', 0);
    
    $counter = 0;

    foreach ($result as $key => $product) {

        try {
            if($product['name']) {
                $_product = new Product($product['id_product']);

                $dataFormatter = new ImportDataFormatter(
                    new FusionStoreBundle\Import\ConfigurationAdapter(),
                    new \PrestaShop\PrestaShop\Adapter\Tools()
                );

                foreach (Language::getIDs(false) as $id_lang) {
                    $rewrite = $dataFormatter->createFriendlyUrl($product['name'], $id_lang);
                    $_product->link_rewrite[$id_lang] = preg_replace('/\s+/u', '', $rewrite);
                }

                $_product->save();
                $counter++;
            }
        } catch (\Exception $e) {
            $log  = date("Y-m-d H:i:s")." Fixurl Exception: ".$e->getMessage().PHP_EOL;
            file_put_contents('./logs/fixurl_'.date("Y-m-d").'.log', $log, FILE_APPEND);
        }
    }

    echo "Fix ".$counter." product links";
    Configuration::updateGlobalValue('PS_ALLOW_ACCENTED_CHARS_URL', 1);
}

$log  = date("Y-m-d H:i:s")." --------------END FIXURL---------------".PHP_EOL;
file_put_contents('./logs/fixurl_'.date("Y-m-d").'.log', $log, FILE_APPEND);

die();

?>
