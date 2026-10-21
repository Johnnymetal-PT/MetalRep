<?php

    include_once('../../config/config.inc.php');
    include_once('../../init.php');

    $cron_flag = (new \FusionStoreBundle\CronJob\Flag(Context::getContext()))->running();
    
    /*$sql = new DbQuery();
    $sql->select('p.`id_product`, fs.`date_upd`');
    $sql->from('product', 'p');
    $sql->leftJoin('fusion_sync', 'fs', 'fs.id_product = p.id_product');
    $sql->where('p.`active` = 1 AND fs.`date_upd` <= \'' . date('Y-m-d H:i:s', strtotime("-13 hours")) . '\'' );
    $sql->orderBy('fs.`date_upd`');
    $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);*/
    
    if (!file_exists('./logs/feedinspector_'.date("Y-m-d").'.log')) {
        touch('./logs/feedinspector_'.date("Y-m-d").'.log');
    }
    
    $log  = date("Y-m-d H:i:s")." --------------INIT FEEDINSPECTOR--------------".PHP_EOL.
            date("Y-m-d H:i:s")." User: ".$_SERVER['REMOTE_ADDR'].PHP_EOL;
    file_put_contents('./logs/feedinspector_'.date("Y-m-d").'.log', $log, FILE_APPEND);

    try {
        $query = 'UPDATE `'._DB_PREFIX_.'product` as p
        INNER JOIN `'._DB_PREFIX_.'fusion_sync` AS fs ON p.`id_product` = fs.`id_product`
        INNER JOIN `'._DB_PREFIX_.'product_shop` AS ps ON p.`id_product` = ps.`id_product`
        INNER JOIN `'._DB_PREFIX_.'stock_available` AS sa ON p.`id_product` = sa.`id_product`
        SET sa.`quantity` = 0, p.`active` = 0, ps.`active` = 0 WHERE fs.`skip_product` != 1 AND fs.`date_upd` <= \'' . date('Y-m-d H:i:s', strtotime("-24 hours")) . '\'';

        $update_result = Db::getInstance()->execute($query);

        if($update_result){
            echo 'Inspector run success';
        }
    } catch (\Exception $e) {
        $log  = date("Y-m-d H:i:s")." Feedinspector Exception: ".$e->getMessage().PHP_EOL;
        file_put_contents('./logs/feedinspector_'.date("Y-m-d").'.log', $log, FILE_APPEND);
    }

    $log  = date("Y-m-d H:i:s")." --------------END FEEDINSPECTOR---------------".PHP_EOL;
    file_put_contents('./logs/feedinspector_'.date("Y-m-d").'.log', $log, FILE_APPEND);    

    $cron_flag->finish();
    die();

?>
