<?php

namespace FusionStoreBundle\Import\Adapter;

use PrestaShopException;
use PrestaShopLogger;
use Exception;
use Hook;
use Tools;
use League\Csv\Reader;
use League\Csv\Writer;
use League\Csv\Statement;
use FusionStoreBundle\Cache\FileCache;

class CSV
{
    protected static $loaded_records = array();

    private $table_columns = array();

    private $hook_matches = array();

    private $matches = array();

    private $file;

    private $cache;

    public $delimiter = ';';

    public $offset = 0;

    public function __construct( $csvFile )
    {
        $this->file = $csvFile;
        $this->hook_matches = Hook::exec('AdapterCSVMatches', array(), null, true);

        $this->cache = new FileCache(
          FileCache::getCacheId($this->file)
        );

        $file_contents = $this->cache->isOnCache();

        if( !$file_contents ){
            $file_contents = self::file_get_contents( $this->file, 400);
            if( $file_contents !== false ){
                $this->cache->putOnCache($file_contents);
                $file_contents = $this->cache->isOnCache(true);
            }
        }

        try {
            if(!$file_contents){
                throw new \PrestaShopException("Error. CSV file content is null", 1);
            }

            $this->loadRecords($file_contents);

        } catch (\PrestaShopException $e) {
            PrestaShopLogger::addLog($e->getMessage());
            Tools::displayError($e->getMessage());
        }
    }

    protected function loadRecords( $file_contents )
    {
        if( !empty(ImportCSV::$loaded_records) )
            return ImportCSV::$loaded_records;

        try {
          $csvFile = Reader::createFromString($file_contents);
          $csvFile->setDelimiter($this->delimiter);
          $csvFile->setHeaderOffset($this->offset);

          $stmt = Statement::create()->process($csvFile);
          $header = $stmt->getHeader();

          $matched_header = array();
          foreach ($header as $column) {
              if( isset($this->matches[$column]) ){
                  $matched_header[] = $this->matches[$column];
              }else if( isset($this->hook_matches[$column]) ){
                  $matched_header[] = $this->hook_matches[$column];
              }else{
                  $matched_header[] = $column;
              }
          }

          var_dump($matched_header);

          /*$records = $this->feed->getRecords( $matched_header );

          $_records_ = array();

          foreach ($records as $offset => $record){

              if( $offset>1 ){
                  $_records_[($offset-1)] = $record;
              }else{
                  foreach ( $record as $column_key => $trash_value ) {
                      $this->table_columns[] = $column_key;
                  }
              }

          }

          ImportCSV::$loaded_records = $_records_;

          return $_records_;*/

        } catch (\Exception $e) {
            PrestaShopLogger::addLog($e->getMessage());
            Tools::displayError($e->getMessage());
        }
    }

    public function setMatches( Array $matches )
    {
        $this->matches = $matches;
    }

    public static function file_get_contents( $url, $timeout = 5 )
    {
        Tools::refreshCACertFile();
        $curl = curl_init();

        curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($curl, CURLOPT_URL, $url);
        #curl_setopt($curl, CURLOPT_CONNECTTIMEOUT, 5);
        curl_setopt($curl, CURLOPT_TIMEOUT, $curl_timeout);
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, true);
        curl_setopt($curl, CURLOPT_CAINFO, _PS_CACHE_CA_CERT_FILE_);
        curl_setopt($curl, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($curl, CURLOPT_MAXREDIRS, 5);

        $content = curl_exec($curl);

        if (false === $content && _PS_MODE_DEV_) {
            $errorMessage = sprintf('file_get_contents_curl failed to download %s : (error code %d) %s',
                $url,
                curl_errno($curl),
                curl_error($curl)
            );

            throw new \Exception($errorMessage);
        }

        curl_close($curl);

        return $content;
    }
}
