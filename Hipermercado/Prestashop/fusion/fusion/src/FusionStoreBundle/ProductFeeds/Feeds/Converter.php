<?php

namespace FusionStoreBundle\ProductFeeds\Feeds;

use SimpleXMLElement;

class Converter
{
    public $header_content_type;

    public $content;

    public static function convert( $content, $type, $root_elem = null)
    {
        $_converter = (new Converter());

        switch ($type) {
          case 'xml':
              $_converter->header_content_type = 'text/xml';
              $_converter->content = self::arrayToXml($content, $root_elem);
              break;

          case 'json':
              $_converter->header_content_type = 'application/json';
              $_converter->content = json_encode($content);
              break;

          default:
              $_converter->header_content_type = 'text/html';
              $_converter->content = 'Invalid type format';
              break;
        }

        return $_converter;
    }

    public static function arrayToXml($array, $rootElement = null, $xml = null)
    {
        $_xml = $xml;

        # If there is no Root Element then insert root
        if ($_xml === null) {
            $_xml = new SimpleXMLElement($rootElement !== null ? $rootElement : '<root/>');
        }

        # Visit all key value pair
        foreach ($array as $k => $v) {
            # If there is nested array then
            if (is_array($v)) {
                # Call function for nested array
                self::arrayToXml($v, $k, $_xml->addChild($k));
            }else{
                # Simply add child element.
                $_xml->addChild($k, $v);
            }
        }

        return $_xml->asXML();
    }
}
