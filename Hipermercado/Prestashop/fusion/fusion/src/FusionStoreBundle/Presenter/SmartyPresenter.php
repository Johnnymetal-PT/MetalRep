<?php

namespace FusionStoreBundle\Presenter;

use ObjectModel;
use Validate;

class SmartyPresenter
{
    public static function present( $obj )
    {
        if (!Validate::isLoadedObject($obj))
            return false;

        $presented = array();

        foreach (get_object_vars($obj) as $prop => $value) {
            $presented[$prop] = $value;
        }

        foreach ( $obj::$definition['fields'] as $obj_key => $__ ) {
            if( property_exists($obj, $obj_key) ){
                $presented[$obj_key] = $obj->{$obj_key};
            }
        }

        return $presented;
    }
}
