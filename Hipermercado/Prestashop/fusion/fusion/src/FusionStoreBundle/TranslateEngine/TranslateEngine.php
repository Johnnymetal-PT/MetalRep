<?php

namespace FusionStoreBundle\TranslateEngine;

class TranslateEngine
{
    protected $translate_api_key = false;
    protected $target = false;
    protected $source = false;
    protected $allow = [];

    public function __construct( $translate_api_key, $target, $source )
    {
        if( $translate_api_key && !empty($translate_api_key) && is_string($translate_api_key) ){
            $this->translate_api_key = $translate_api_key;
        }
        $this->target = $target;
        $this->source = $source;
        return $this;
    }

    public function translate( $text )
    {
        return $text;
    }

    public function map( $fields )
    {
        $this->allow = $fields;
        return $this;
    }

    public function can( $field )
    {
        if( in_array($field, $this->allow) ){
            return true;
        }else{
            return false;
        }
    }
}