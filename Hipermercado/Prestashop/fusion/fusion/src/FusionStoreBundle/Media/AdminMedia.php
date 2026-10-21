<?php

namespace FusionStoreBundle\Media;

use Media;

class AdminMedia
{
    static $skds = [
        'product' => []
    ];

    public static function getSDK( $sdk_plugin )
    {
        if( isset(self::$skds[$sdk_plugin]) ){
            #Media::addJs(self::$skds[$sdk_plugin]);
        }
    }

}
