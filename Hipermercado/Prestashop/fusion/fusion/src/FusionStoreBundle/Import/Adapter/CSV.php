<?php

namespace FusionStoreBundle\Import\Adapter;

use PrestaShopException;
use PrestaShopLogger;
use Exception;
use Hook;
use Tools;
use League\Csv\Reader as CSVReader;
use League\Csv\Writer;
use League\Csv\Statement;
use FusionStoreBundle\Cache\FileCache;

class CSV extends Reader
{
    public $delimiter = ';';

    protected $utf8encode = true;

    public function __construct( $csvFile )
    {
        parent::__construct( $csvFile );
        $this->hook_matches = Hook::exec('AdapterJSONMatches', array(), null, true);
    }

    protected function initReader( $file_contents )
    {
        try {

          if( $this->utf8encode )
              $file_contents = utf8_encode($file_contents);

          $csvFile = CSVReader::createFromString($file_contents);
          $csvFile->setDelimiter($this->delimiter);
          $csvFile->setHeaderOffset($this->offset);

          $stmt = Statement::create()->process($csvFile);
          $header = $stmt->getHeader();

          $matched_header = array();
          foreach ($header as $column) {
              $column = trim($column);

              if( isset($this->matches[$column]) ){
                  $matched_header[] = $this->matches[$column];
              }else if( isset($this->hook_matches[$column]) ){
                  $matched_header[] = $this->hook_matches[$column];
              }else{
                  $matched_header[] = $column;
              }
          }

          $_records_ = array();

          foreach ($csvFile->getRecords($matched_header) as $offset => $record){
              if( $this->ignore_first_record && $offset == 1 ){
                  # do nothing
              }else{
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

    public function utf8Enc( Bool $encode )
    {
        $this->utf8encode = $encode;
        return $this;
    }

    public static function file_get_contents( $url, $timeout = 5 )
    {
        $content = file_get_contents($url);
        return $content;
    }

}
