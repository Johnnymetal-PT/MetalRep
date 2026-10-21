<?php

namespace FusionStoreBundle\Import;

class ProductPropFinder
{

    protected static $loaded_records = array();

    public static function match( $match_table, $data )
    {
        if(!empty(self::$loaded_records))
            return self::$loaded_records;

        $_records = array();

        foreach ($match_table as $match_key => $match_head ) {
            if( isset($data[$match_head]) ){
                $_records[$match_key] = $data[$match_head];
            }
        }

        self::$loaded_records = $_records;
        return self::$loaded_records;
    }

}
