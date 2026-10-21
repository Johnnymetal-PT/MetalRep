<?php

include_once('../../config/config.inc.php');
include_once('../../init.php');

use PrestaShop\PrestaShop\Adapter\Import\ImportDataFormatter;
use PrestaShop\PrestaShop\Core\ConfigurationInterface;

$sql = new DbQuery();
$sql->select('p.`id_product`, p.`id_category_default`');
$sql->from('product', 'p');
$sql->leftJoin('category_product', 'pc', 'pc.id_product = p.id_product');
$sql->where('p.`id_category_default` >= 0' );
$result = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

if($result){

    $counter = 0;

    foreach ($result as $key => $product) {
        $_sql = new DbQuery();
        $_sql->select('`id_product`, `id_category`');
        $_sql->from('category_product');
        $_sql->where('`id_product` = '.(int)$product['id_product']);
        $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($_sql);

        if(!$result){
            # Product without categories
            $_product = new Product($product['id_product']);
            if($_product->addToCategories([$product['id_category_default']]))
          	   $counter++;
        }
    }

    echo "Fix ".$counter." product without categories";
}

die();

?>
