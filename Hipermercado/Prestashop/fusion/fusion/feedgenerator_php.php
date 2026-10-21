<?php

include_once('../../config/config.inc.php');
include_once('../../init.php');

$sql = new DbQuery();
$sql->select('p.`id_product`');
$sql->from('product', 'p');
$sql->leftJoin('product_shop', 'ps', 'ps.id_product = p.id_product');
$sql->where('p.`active` = 1 AND ps.`active` = 1 AND p.`price` > 0' );
$products = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

die(var_dump(count($products)));