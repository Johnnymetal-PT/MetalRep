<?php

namespace FusionStoreBundle\Import\Adapter;

use PrestaShopException;
use PrestaShopLogger;
use Exception;
use Hook;
use Tools;
use FusionStoreBundle\Cache\FileCache;

class JSON extends Reader
{

    public function __construct( $jsonFile )
    {
        parent::__construct( $jsonFile );
        $this->hook_matches = Hook::exec('AdapterJSONMatches', array(), null, true);
    }

    protected function initReader( $file_contents )
    {
        try {

            $jsonFile = Tools::jsonDecode($file_contents, true);

            if( isset($this->parent_key) ){
                $jsonFile = $jsonFile[$this->parent_key];
            }

            $_records_ = array();

            foreach ($jsonFile as $offset => $record) {

                if( isset($this->child_key) ){
                    $record = $record[$this->child_key];
                }

                if( $this->ignore_first_record && $offset == 1 ){
                    # do nothing
                }else{
                    if( !empty($this->matches) ){
                        foreach ($record as $record_key => $__) {
                            if( !isset($this->matches[$record_key]) ){
                                $this->matches[$record_key] = $record_key;
                            }
                        }
                        $filterKey = array_intersect_key( $this->matches, $record );
                        $record = array_combine(array_merge($record, $filterKey), $record);
                    }
                    $_records_[$offset] = $record;
                }
            }

            return $_records_;

        } catch (\Exception $e) {
            PrestaShopLogger::addLog($e->getMessage());
            Tools::displayError($e->getMessage());
            return [];
        }
    }

    public static function file_get_contents( $url, $timeout = 5 )
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_HEADER, false);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: application/json'
        ));
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_URL, $url );
        // Execute
        $result = curl_exec($ch);
        // Closing
        curl_close($ch);

        return $result;
    }

    public function setParent( $parent_key )
    {
        $this->parent_key = $parent_key;
        return $this;
    }

    public function setChild( $child_key )
    {
        $this->child_key = $child_key;
        return $this;
    }
}
