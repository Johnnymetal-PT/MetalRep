<?php

  	include_once('../../config/config.inc.php');
  	include_once('../../init.php');

    $cron_flag = (new \FusionStoreBundle\CronJob\Flag(Context::getContext()))->running();

    $query = 'UPDATE `'._DB_PREFIX_.'product` as p
    INNER JOIN `'._DB_PREFIX_.'fusion_sync` AS fs ON p.`id_product` = fs.`id_product`
    INNER JOIN `'._DB_PREFIX_.'product_shop` AS ps ON p.`id_product` = ps.`id_product`
	INNER JOIN `'._DB_PREFIX_.'stock_available` AS sa ON p.`id_product` = sa.`id_product`
    SET p.`active` = 0, ps.`active` = 0 WHERE fs.`skip_product` != 1 AND sa.`quantity` <= 0';

    $update_result = Db::getInstance()->execute($query);

    if($update_result){
        echo 'Inspector run success';
    }

   	$cron_flag->finish();
    die();

?>
