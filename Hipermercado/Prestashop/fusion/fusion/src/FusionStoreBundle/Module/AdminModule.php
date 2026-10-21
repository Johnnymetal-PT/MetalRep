<?php

namespace FusionStoreBundle\Module;

use Db;
use DbQuery;
use Module;
use Context;
use Validate;
use ObjectModel;

/**
 *
 */
class AdminModule
{
    protected $module = null;

    protected $context = null;

    protected $smarty = null;

    protected $fusion = null;

    protected $hooks_register = [];

    function __construct( Module $module, Context $context = null)
    {
        $this->module = $module;

        // Load context and smarty
        $this->context = $context ? $context : Context::getContext();
        if (is_object($this->context->smarty)) {
            $this->smarty = $this->context->smarty->createData($this->context->smarty);
        }

        if(!defined('FUSION_SERVICES_DIR')){
            $this->fusion = Module::getInstanceByName('fusion');
        }
    }

    public function registerHooks()
    {
        $sucess = true;
        if(!empty($this->hooks_register)){
            foreach ( $this->hooks_register as $hook_name ) {
                $sucess &= $this->module->registerHook($hook_name);
            }
        }
        return $sucess;
    }

    public function unregisterHooks()
    {
        $sucess = true;
        if(!empty($this->hooks_register)){
            foreach ( $this->hooks_register as $hook_name ) {
                $sucess &= $this->module->unregisterHook($hook_name);
            }
        }
        return $sucess;
    }

    public function pushHooks( Array $hooks_register = [])
    {
        if( !empty($hooks_register) ){
          $this->hooks_register = $hooks_register;
        }else{
          $this->hooks_register = $this->module->hooks_register;
        }
        return $this->registerHooks();
    }

    public function pullHooks( Array $hooks_register = [] )
    {
        if( !empty($hooks_register) ){
          $this->hooks_register = $hooks_register;
        }else{
          $this->hooks_register = $this->module->hooks_register;
        }
        return $this->unregisterHooks();
    }

    public function render( String $file, $path = false )
    {
        if( $path == false ){
          $path = $this->module->getLocalPath().'views/templates/';
        }
        $output = $this->context->smarty->fetch( $path . $file );
        return $output;
    }

    public function installEntity( Array $entities, String $namespace = '\\FusionStoreBundle\\Entity\\' )
    {
        $success = true;
        foreach ( $entities as $entity ) {
            $entity_class = $namespace.$entity;
            if( class_exists($entity_class) ){
                $success &= $entity_class::install();
            }
        }
        return $success;
    }

    public function uninstallEntity( Array $entities, String $namespace = '\\FusionStoreBundle\\Entity\\' )
    {
        foreach ( $entities as $entity ) {
            $entity_class = $namespace.$entity;
            if( class_exists($entity_class) ){
                $sql = "DROP TABLE IF EXISTS "._DB_PREFIX_.$entity_class::$definition['table'].";";
                Db::getInstance()->execute($sql);
                $sql = "DROP TABLE IF EXISTS "._DB_PREFIX_.$entity_class::$definition['table']."_lang;";
                Db::getInstance()->execute($sql);
                $sql = "DROP TABLE IF EXISTS "._DB_PREFIX_.$entity_class::$definition['table']."_shop;";
                Db::getInstance()->execute($sql);
            }
        }
        return true;
    }

    public function getEntity( $entity, String $namespace = '\\FusionStoreBundle\\Entity\\' )
    {
        $entity_class = $namespace.$entity;
        if( class_exists($entity_class) ){
            $sql = "SELECT *
            FROM information_schema.tables
            WHERE table_schema = '"._DB_NAME_."'
            AND table_name = '"._DB_PREFIX_.$entity_class::$definition['table']."'
            LIMIT 1;";
            $result = Db::getInstance()->executeS($sql);
            if( is_array($result) && !empty($result) ){
                return true;
            }
        }
        return false;
    }

    public function ajaxResponse( $ajaxResponse, $success = true )
    {
        \FusionStoreBundle\Tools::ajaxResponse( $ajaxResponse, $success );
        die();
    }

    public function isModuleActive($function_exist = false)
    {
        if (Validate::isLoadedObject($this->module) && $this->module->active) {
            $sql = new DbQuery();
            $sql->from('module_shop', 'm');
            $sql->where('m.id_module = '.(int)$this->module->id);
            $sql->where('m.enable_device & '.(int)Context::getContext()->getDevice());
            $sql->where('m.id_shop = '.(int)Context::getContext()->shop->id);

            $active_device = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($sql);

            if ($active_device) {
                if ($function_exist) {
                    if (method_exists($this->module, $function_exist)) {
                        return true;
                    } else {
                        return false;
                    }
                }

                return true;
            }
        }
        return false;
    }
}
