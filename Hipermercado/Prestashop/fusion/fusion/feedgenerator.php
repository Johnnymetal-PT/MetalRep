<?php

  	include_once('../../config/config.inc.php');
  	include_once('../../init.php');

    $cron_flag = (new \FusionStoreBundle\CronJob\Flag(Context::getContext()))->running();

    $FeedGenerator = new \FusionStoreBundle\CronJob\FeedGenerator( Context::getContext() );

    ob_end_clean();
    $FeedGenerator->run();
   	$cron_flag->finish();
    die();

?>
