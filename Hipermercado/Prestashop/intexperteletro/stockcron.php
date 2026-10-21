<?php

	include_once('../../config/config.inc.php');
	include_once('../../init.php');

	$module = Module::getInstanceByName('intexperteletro');
  $module->cronRun();

?>
