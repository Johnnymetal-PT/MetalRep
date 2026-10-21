<?php

namespace FusionStoreBundle;

use FusionStoreBundle\TBK\TBKClient;
use FusionStoreBundle\Services\AdminModuleService;

class ProductsApiModuleAssociations
{
    protected $data;

    protected $module_name;

    public function __construct( $module, $config_data )
    {
        $this->data = $config_data;
        $this->module = $module;
    }

    public function getSerialize()
    {
        return serialize($this->data);
    }

    public function getUnserialize()
    {
        return unserialize($this->data);
    }

    public function getArray()
    {
        $config_File = FUSION_SERVICES_DIR.'config/'.$this->module->name.'_ProductsApiModuleAssociations.json';
        if(!file_exists($config_File))
            return [];
        $this->data = file_get_contents($config_File);
        return  $this->getUnserialize();
    }

    public function saveLocal()
    {
        $config_File = FUSION_SERVICES_DIR.'config/'.$this->module->name.'_ProductsApiModuleAssociations.json';
        return file_put_contents( $config_File, $this->getSerialize() );
    }

    public function saveOnline()
    {
        return (new TBKClient())->cert(
            (new AdminModuleService($this->module))->getCertKey()
        )->save($this);
    }
}
