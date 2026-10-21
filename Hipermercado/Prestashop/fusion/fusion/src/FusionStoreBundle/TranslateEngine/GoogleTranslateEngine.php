<?php

namespace FusionStoreBundle\TranslateEngine;

use Google\Cloud\Translate\V2\TranslateClient;

class GoogleTranslateEngine extends TranslateEngine
{
    public function translate( $text )
    {
        if( !$this->translate_api_key || $this->translate_api_key == ''){
            return $text;
        }

        $translate = new TranslateClient([
            'key' => $this->translate_api_key,
        ]);

        // Translate text from english to french.
        $result = $translate->translate($text, [
            'source' => $this->source,
            'target' => $this->target
        ]);

        return isset($result['text']) ? $result['text'] : $text;
    }
}