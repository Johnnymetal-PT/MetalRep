<?php

namespace FusionStoreBundle;

class MediaPlugins
{
    static $plugins = [
        'dashboard' => [
          'css' => [ 'dashboard/new-theme/theme.css', 'dashboard/override.css' ]
        ],
        'dashboard-178' => [
          'css' => [ 'dashboard/override-178.css' ]
        ],
        'dashboard-1783' => [
          'css' => [ 'dashboard/override-1783.css' ]
        ],
        'dashboard-legay' => [
          'css' => [ 'dashboard/default/theme.css', 'dashboard/default/new-theme.css', 'dashboard/override.css' ]
        ],
        'dashboard-legay-178' => [
          'css' => [ 'dashboard/default/new-theme.css', 'dashboard/override-178.css' ]
        ],
        'dashboard-legay-1783' => [
          'css' => [ 'dashboard/default/new-theme.css', 'dashboard/override-1783.css' ]
        ],
        'fusion' => [
          'js' => [  'fusion/fusion.js', 'fusion/fusion.req.js' ],
          'css' => [ 'fusion/icons.lib.css', 'fusion/fusion.css' ]
        ],
        'fusion-lib' => [
          'js' => [ 'fusion/fusion.lib.js' ],
          'css' => [ 'fusion/fusion.lib.css' ]
        ],
        'bs-modal' => [
          'css' => [ 'bs-modal/bs-modal.css' ],
          'js' => [ 'bs-modal/bs-modal.js' ]
        ]
    ];

    public static function load( $context, $plugin )
    {
        $base_plugin_path = _MODULE_DIR_.'fusion/libs/';

        if( isset(self::$plugins[$plugin]) ){
            if( isset(self::$plugins[$plugin]['css']) )
            {
                foreach (self::$plugins[$plugin]['css'] as $file) {
                    $context->controller->addCSS( $base_plugin_path.$file);
                }
            }
            if( isset(self::$plugins[$plugin]['js']) )
            {
                foreach (self::$plugins[$plugin]['js'] as $file) {
                    $context->controller->addJS( $base_plugin_path.$file);
                }
            }
        }
    }
}
