<?php

namespace FusionStoreBundle\Import\Adapter;

use PrestaShopException;
use PrestaShopLogger;
use Exception;
use Hook;
use Tools;
use FusionStoreBundle\Cache\FileCache;

class Reader
{
    protected $loaded_records = array();

    protected $table_columns = array();

    protected $hook_matches = array();

    protected $matches = array();

    protected $only_matches = false;

    public $ignore_cache = false;

    public $curl = false;

  	public $req_response = '';

    protected $file;

    protected $cache;

    protected $filters;

    public $offset = 0;

    public $ignore_first_record = 0;

    public function __construct( $file )
    {
        $this->file = $file;
        $this->cache = new FileCache(
            FileCache::getCacheId($this->file),
            18000
        );
    }

    public function loadFile( Bool $update_timestamp = false )
    {
        $file_contents = false;

        if( !$this->ignore_cache )
            $file_contents = $this->cache->isOnCache();

        if( !$file_contents ){
            if( $this->curl ){
                $file_contents = static::curl_request( $this->file, 500 );
              	$this->req_response = $file_contents;
            }else {
                $file_contents = static::file_get_contents( $this->file, 400);
            }

            try {
                if(!$file_contents){
                    throw new \PrestaShopException("Error. Feed content is null", 1);
                }

                $this->loaded_records = $this->initReader(
                    $this->filter($file_contents)
                );

                if( is_array($this->loaded_records) ){
                    if( $this->only_matches ){
                        foreach ( $this->loaded_records as $key => &$row) {
                          $matches = $this->matches;
                          $row = array_filter(
                              $row,
                              function ($_key) use ($matches){
                                  return in_array($_key, $matches);
                              },
                              ARRAY_FILTER_USE_KEY
                          );
                        }
                    }
                    $save = $this->cache->putOnCache(json_encode($this->loaded_records));
                }

            } catch (\PrestaShopException $e) {
                PrestaShopLogger::addLog($e->getMessage());
                Tools::displayError($e->getMessage());
            }
        }else{
            if( $update_timestamp ){
                $this->cache->refreshTimeStamp();
            }
            $this->loaded_records = json_decode($file_contents, true);
        }

        return $this->loaded_records;
    }

    public function setMatches( Array $matches, Bool $only_matches = false )
    {
        $this->matches = $matches;
        $this->only_matches = $only_matches;
        return $this;
    }

    public function getRecords( Bool $update_timestamp = false )
    {
        if( !empty($this->loaded_records) )
            return $this->loaded_records;

        return $this->loadFile( $update_timestamp );
    }

    public function addFilter( $_function )
    {
        $this->filters[] = $_function;
        return $this;
    }

    protected function filter( $data )
    {
        if( !empty($this->filters) ){
            foreach ($this->filters as $filter_func) {
                $data = $filter_func($data);
            }
        }
        return $data;
    }

    public function refreshTimeStamp()
    {
        $this->cache->refreshTimeStamp();
    }

    protected function initReader( $file_contents ){}

    public static function file_get_contents( $url, $timeout = 5 ){}

    public static function curl_request( $url, $timeout = 500 )
    {
        try {

            $ch = curl_init($url);
            curl_setopt($ch, CURLOPT_FAILONERROR,1);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION,1);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER,1);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, array(
                'Content-Type: application/json'
            ));
            curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
            curl_setopt($ch, CURLOPT_URL, $url );
            $retValue = curl_exec($ch);
            curl_close($ch);

            if($retValue === false) {
                throw new \Exception("Error Processing Request", 1);
            } else {
                return $retValue;
            }

        } catch (\Exception $e) {
            PrestaShopLogger::addLog($e->getMessage());
            Tools::displayError($e->getMessage());
        }
        return false;
    }

    public function getFeedFromCache()
    {
        return $this->cache->isOnCache();
    }
}
