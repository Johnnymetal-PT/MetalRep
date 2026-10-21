<?php

namespace FusionStoreBundle\Hooks;

use Hook;
use Module;
use Context;

class FusionServicesHooks
{
    public function __construct( Module $module, Context $context = null )
    {
        $this->module = $module;
        $this->context = $context;
        return $this;
    }

    public function Routes( $params = [] )
    {
        return $this->Hook( 'Routes', $params );
    }

    public function Hook( $hook_name, $params )
    {
        $result = [];
        $fservises = file_get_contents(FUSION_SERVICES_DIR.'src/FusionServices/services.json');
        $fservises = json_decode($fservises);

        foreach ($fservises->packages as $package) {
            $service_name = 'FusionServices\\'.$package->name.'\\'.$package->name;
            $service = new $service_name($this->module, $this->context);
            if( method_exists($service, 'hook'.$hook_name) ){
                $result[] = $service->{'hook'.$hook_name}($params);
            }
        }
        return $result;
    }
}
