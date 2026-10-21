<?php

namespace FusionStoreBundle\Services;

use Context;
use Module;
use Meta;
use Hook;
use Configuration;
use Tools;
use PrestaShopException;
use ZipArchive;
use FusionStoreBundle\Tools as FusionTools;
use RecursiveIteratorIterator;
use RecursiveDirectoryIterator;

/**
 *
 */
class AdminModuleService
{
    public static $services;

    private $fusion_services = '';

    private $module = null;

    private $settings = null;

    private $certkey = null;

    private $native_modules = [
      'emarketing',
      'ps_mbo',
      'ps_facebook',
      'ps_checkout',
      'ps_metrics',
      'ps_dataprivacy',
      'ps_languageselector',
      'gamification',
      'psaddonsconnect',
      'welcome',
    ];

    # Normal not used Modules
    private $hide_modules_on_list = [
      'posthemeoptions',
      'ps_advertising',
      'ps_themecusto',
      'ps_customersignin',
      'ps_languageselector',
      'ps_currencyselector',
      'ps_customeraccountlinks',
      'ps_faviconnotificationbo'
    ];

    # Non Configurable modules
    private $hide_nc_modules_on_list = [
      'gridhtml',
      'statscheckup',
      'ps_dataprivacy',
      'statsregistrations',
      'statsproduct',
      'statscarrier',
      'statscatalog',
      'graphnvd3',
      'statspersonalinfos',
      'statsbestcategories',
      'statsbestcustomers',
      'statsbestsuppliers',
      'statsbestvouchers',
      'statsequipment',
      'statsnewsletter',
      'statsorigin',
      'pagesnotfound',
      'dashactivity',
      'statsforecast',
      'dashgoals',
      'dashproducts',
      'dashtrends',
      'sekeywords',
      'statssearch',
      'ps_eventbus',
      'statsbestproducts',
      'statsstock',
      'statsdata',
      'statssales',
      'statslive',
      'statsvisits'
    ];

    public function __construct( Module $module )
    {
        $this->module = $module;
        $config_file = Configuration::get('FUSION_SERVICES_SETTINGS');
        $this->settings = unserialize($config_file);
    }

    public function init()
    {
        return true;
        if( !file_exists(FUSION_SERVICES_DIR.'.certkey') )
            return false;
        $certkey = file_get_contents(FUSION_SERVICES_DIR.'.certkey');
        if( strlen($certkey) < 10 )
            return false;
        $this->certkey = $certkey;
        return true;
    }

    public function getCertKey()
    {
        return $this->certkey;
    }

    public function generateCert( $domain, $certkey, $secret_key = false )
    {
        $this->certkey = $certkey;
        $result = file_put_contents(FUSION_SERVICES_DIR.'.certkey', $this->certkey);
        return $result;
    }

    public function getConfig( $key )
    {
        if( isset($this->settings[$key]) ){
            return $this->settings[$key];
        }else{
            return false;
        }
    }

    public function setConfig( $key, $value )
    {
        $this->settings[$key] = $value;
        return Configuration::updateValue('FUSION_SERVICES_SETTINGS', serialize($this->settings));
    }

    # since 1.1.1
    public function getEntityStatus()
    {
        $entitieins = [];
        $entities = Tools::getValue('entities');
        $FusionModule = new \FusionStoreBundle\Module\AdminModule($this->module);
        if(!empty($entities)){
            foreach ($entities as $entity_name) {
                if($FusionModule->getEntity($entity_name)){
                    $entitieins[] = $entity_name;
                }
            }
        }
        return ['entities'=>$entitieins];
    }

    public function getHooksStatus()
    {
        $hooksins = [];
        foreach (Hook::getHookModuleList() as $row) {
            foreach ($row as $hookdata) {
                if($hookdata['name'] == 'fusion'){
                    $hooksins[] = Hook::getNameById($hookdata['id_hook']);
                }
            }
        }
        return ['hooks'=>$hooksins];
    }

    protected function doEntitiesActions($dowhat){
        if( Tools::isSubmit('targetwhat') ){
            $targetwhat = Tools::getValue('targetwhat');
            if( Tools::getValue('tokenfs') == md5($targetwhat) ){
                $FusionModule = new \FusionStoreBundle\Module\AdminModule($this->module);
                if( $dowhat == 'install_entities' ){
                    return $FusionModule->installEntity([$targetwhat]);
                }else{
                    return $FusionModule->uninstallEntity([$targetwhat]);
                }
            }
        }
        return false;
    }

    protected function doHooksActions($dowhat){
        if( Tools::isSubmit('targetwhat') ){
            $targetwhat = Tools::getValue('targetwhat');
            if( $dowhat == 'install_hooks' ){
                if( in_array($targetwhat, $this->module->hooks_register) ){
                    return $this->module->registerHook($targetwhat);
                }else if( Tools::getValue('tokenfs') == md5($targetwhat) ){
                    if($this->module->registerHook($targetwhat)){
                        FusionTools::logException( 'Hook: '.$targetwhat.' installed.', 1, true );
                        return true;
                    }
                    return false;
                }
                return false;
            }else{
                if( in_array($targetwhat, $this->module->hooks_register) ){
                    return $this->module->unregisterHook($targetwhat);
                }else if( Tools::getValue('tokenfs') == md5($targetwhat) ){
                    if($this->module->unregisterHook($targetwhat)){
                        FusionTools::logException( 'Hook: '.$targetwhat.' removed.', 1, true );
                        return true;
                    }
                    return false;
                }
                return false;
            }
        }
        return false;
    }

    public function fusionAction( $dowhat )
    {
        $result = true;

        if( $dowhat == 'disable_native_modules' ){
            $result &= Module::disableAllByName( $this->native_modules );
        }else if( $dowhat == 'install_entities' || $dowhat == 'uninstall_entities' ){
            $result = $this->doEntitiesActions($dowhat);
        }else if( $dowhat == 'install_hooks' || $dowhat == 'uninstall_hooks' ){
            $result = $this->doHooksActions($dowhat);
        }else if( $dowhat == 'remove_store_faqs_tab' ){
            if( version_compare(_PS_VERSION_, '1.7.0') < 0 ){
                echo 'Store needs update! Version 1.7.0 min required';
                die();
            }
            $result &= FusionTools::uninstallTab('AdminFusionStoreFaqs');
        }else if( $dowhat == 'install_store_faqs_tab' ){
            if( version_compare(_PS_VERSION_, '1.7.0') < 0 ){
                echo 'Store needs update! Version 1.7.0 min required';
                die();
            }
            $result &= FusionTools::addTab($this->module->name, 'FAQ\'s', 'AdminFusionStoreFaqs', FusionTools::getIdTabFromClassName('AdminParentThemes'),'', true);
        }else if( $dowhat == 'remove_import_report_tab' ){
            if( version_compare(_PS_VERSION_, '1.7.0') < 0 ){
                echo 'Store needs update! Version 1.7.0 min required';
                die();
            }
            $result &= FusionTools::uninstallTab('AdminFusionImportReport');
        }else if( $dowhat == 'install_import_report_tab' ){
            if( version_compare(_PS_VERSION_, '1.7.0') < 0 ){
                echo 'Store needs update! Version 1.7.0 min required';
                die();
            }
            $result &= FusionTools::addTab($this->module->name, 'Import Reports', 'AdminFusionImportReport', FusionTools::getIdTabFromClassName('AdminAdvancedParameters'),'', true);
        }else if( $dowhat == 'uninstall_native_modules' ){
            if( !empty($this->native_modules) ){
                foreach ($this->native_modules as $module_native) {
                    if( $module_instance = Module::getInstanceByName($module_native) ){
                        $result &= $module_instance->uninstall();
                        if(!$result){
                          echo 'Fail in '.$module_native.' module';
                          die();
                        }
                    }
                }
            }
        }else if( $dowhat == 'fusion_staff_report' ){
            if( file_exists(_PS_ROOT_DIR_.'/modules/fusion.zip') ){
                @unlink(_PS_ROOT_DIR_.'/modules/fusion.zip');
            }
        }else if( $dowhat == 'fusion_staff_verify' ){

            if( file_exists(_PS_ROOT_DIR_.'/modules/fusion.zip') ){
                @unlink(_PS_ROOT_DIR_.'/modules/fusion.zip');
            }

            $rootPath = realpath(_PS_ROOT_DIR_.'/modules/fusion/');

            // Initialize archive object
            $zip = new ZipArchive();
            $zip->open(_PS_ROOT_DIR_.'/modules/fusion.zip', ZipArchive::CREATE | ZipArchive::OVERWRITE);

            $files = new RecursiveIteratorIterator(
                new RecursiveDirectoryIterator($rootPath),
                RecursiveIteratorIterator::LEAVES_ONLY
            );

            foreach ($files as $name => $file)
            {
              if (!$file->isDir()){
                  $filePath = $file->getRealPath();
                  $relativePath = substr($filePath, strlen($rootPath) + 1);
                  $zip->addFile($filePath, $relativePath);
              }
            }
            $zip->close();
            $result = true;
        }else if( $dowhat == 'check_updates' ){
            if( $this->lookForAutoUpdates(true) === false ){
                $result = false;
            }else{
                $result = true;
            }
        }else if( $dowhat == 'do_bulk_actions' ){
            if( is_dir(FUSION_SERVICES_DIR.'bulk/modules/') ){
                if ($handle = opendir( FUSION_SERVICES_DIR.'bulk/modules/' )) {
                    while (false !== ($entry = readdir($handle))) {
                        if ($entry != "." && $entry != "..") {
                            @rename(  _PS_ROOT_DIR_.'/modules/'.$entry, FUSION_SERVICES_DIR.'bulk/modules/'.$entry );
                        }
                    }
                    closedir($handle);
                }
            }
        }
        return $result;
    }

    public function lookForAutoUpdates( $force_check = false )
    {
        return true;
        if(!$force_check){
            if( isset($_COOKIE["lastupdate_check"]) && (time()-(int)$_COOKIE["lastupdate_check"]) <= (3600 * 12) ){
                return;
            }
        }

        try {
            if( !$are_updates = FusionTools::simplexml_load_file($this->fusion_services.'/module-updater/'.$this->module->name.'/'.$this->certkey.'?v='.$this->module->version.'&t='.time())){
                throw new \PrestaShopException("Updates Check timeout", 2);
                return true;
            }
        } catch (\Exception $e) {
            FusionTools::logException( $e->getMessage(), 2, true );
        }

        setcookie('lastupdate_check', time(), time() + (86400 * 30), "/");

        $success = true;

        if( $are_updates && $are_updates->data != 'INVALID_REQUEST'){
            $are_updates = json_encode($are_updates->data);
            $are_updates = json_decode($are_updates, true);

            if( isset($are_updates[$this->module->name]) ){

                $file = $this->fusion_services.'/get-update/'.$are_updates[$this->module->name]['hash'].'/'.$this->certkey;
                $newFile = _PS_CACHE_DIR_.$are_updates[$this->module->name]['hash'].'.zip';

                $handle = curl_init($file);
                curl_setopt($handle,  CURLOPT_RETURNTRANSFER, TRUE);

                /* Get the HTML or whatever is linked in $url. */
                $response = curl_exec($handle);

                /* Check for 404 (file not found). */
                $httpCode = curl_getinfo($handle, CURLINFO_HTTP_CODE);

                try {
                    if( $httpCode == 200 ) {
                        if ( !copy($file, $newFile) ) {
                            throw new \PrestaShopException("Failed to download update package", 2);
                            return false;
                        }

                        $zip = new ZipArchive();
                        if ($zip->open($newFile, ZIPARCHIVE::CREATE)!==TRUE) {
                            throw new \PrestaShopException("Cannot open update package", 2);
                            return false;
                        }

                        if( !is_writable(_PS_CACHE_DIR_.'fusion-temp/') ){
                            mkdir(_PS_CACHE_DIR_.'fusion-temp/');
                        }

                        $zip->extractTo(_PS_CACHE_DIR_.'fusion-temp/');
                        $zip->close();

                        $fileSystem = new \Symfony\Component\Filesystem\Filesystem();

                        if( file_exists(_PS_CACHE_DIR_.'fusion-temp/.version') && $version_check = file_get_contents(_PS_CACHE_DIR_.'fusion-temp/.version') ){
                            if((string)$version_check !== (string)$this->module->version){
                                $fileSystem->mirror(_PS_CACHE_DIR_.'fusion-temp/', FUSION_SERVICES_DIR);
                                $success &= Module::upgradeModuleVersion('fusion', $version_check);
                            }
                        }

                        $fileSystem->remove([$newFile, _PS_CACHE_DIR_.'fusion-temp/']);

                        return $success;
                    }else{
                        throw new \PrestaShopException("Update package not found", 1);
                    }
                } catch (\PrestaShopException $e) {
                    FusionTools::logException( $e->getMessage(), 2, true );
                }

                curl_close($handle);

                return true;
            }
        }
    }

    public function hideModulesOnList()
    {
        $hidde = [];

        if( $this->getConfig('modules_hide_nonconfigurable') ){
            foreach ($this->hide_nc_modules_on_list as $module_name) {
                $hidde[] = '.module-item[data-tech-name="'.$module_name.'"]';
            }
        }
        if( $this->getConfig('modules_hide_basic') ){
            foreach ($this->hide_modules_on_list as $module_name) {
                $hidde[] = '.module-item[data-tech-name="'.$module_name.'"]';
            }
        }

        if( $this->getConfig('modules_hide_extra_active') ){
            if( $extra = $this->getConfig('modules_hide_extra') ){
                $hide_extra = explode(",", $extra);
                if( !empty($hide_extra) ){
                    foreach ($hide_extra as $module_name) {
                        $hidde[] = '.module-item[data-tech-name="'.$module_name.'"]';
                    }
                }
            }
        }

        return implode( ",", $hidde ) . '{ display:none !important; }';
    }
}
