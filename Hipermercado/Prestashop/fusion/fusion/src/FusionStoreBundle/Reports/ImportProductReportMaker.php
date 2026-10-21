<?php

namespace FusionStoreBundle\Reports;

use FusionStoreBundle\Import\ProductModel;

class ImportProductReportMaker
{
    private $reports_folder;

    private $report_file;

    private $module;

    private $hash;

    private $product_model;

    public function __construct()
    {
        $this->reports_folder = _PS_ROOT_DIR_.'/modules/fusion/reports/';
    }

    public function module( String $module_name )
    {
        $this->module = $module_name;
        $this->reports_folder = $this->reports_folder . $this->module . '/';
        if( !is_dir($this->reports_folder) ){
            mkdir($this->reports_folder);
        }
        return $this;
    }

    public function hash( String $hash )
    {
        $this->hash = $hash;
        $this->report_file = $this->hash . '.repo';
        return $this;
    }

    public function product( ProductModel $product_model )
    {
        $this->product_model = $product_model;
        return $this;
    }

    public function feed( $feed_data )
    {
        $this->feed_data = $feed_data;
        return $this;
    }

    public function result( $result )
    {
        if( $result->ignore() ){
            return $this;
        }

        if( file_exists($this->reports_folder.$this->report_file) ){
            $report_data = file_get_contents( $this->reports_folder.$this->report_file );
            $report_data = json_decode($report_data, true);
            if( !is_array($report_data) ){ # check if data is corrupt
                $report_data = [];
            }
        }else{
            $report_data = [];
        }

        $report = $result->getReport();

        $report_data[$this->feed_data['ean13']] = [
            'result'        => $report['result'],
            'need_alert'    => $report['need_alert'],
            'report'        => $report,
            'feed_data'     => $this->feed_data,
            'product_model' => $this->product_model
        ];

        file_put_contents( $this->reports_folder.$this->report_file, json_encode($report_data) );

        return $this;
    }

    public function deleteByName( $filename )
    {
        if( file_exists($this->reports_folder.$filename) ){
            return unlink($this->reports_folder.$filename);
        }
        return true;
    }

    public function getReports()
    {
        $reports = [];
        $files = scandir($this->reports_folder);
        foreach ($files as $key => $value) {
            $path = realpath($this->reports_folder . DIRECTORY_SEPARATOR . $value);
            if (!is_dir($path)) {
                $reports[] = [
                    'filehour'    => date('H:i', filemtime($path)),
                    'filedate'    => date('d, M Y', filemtime($path)),
                    'filename'    => $value,
                    'contents'    => json_decode(file_get_contents($path),true),
                    'filetime'    => filemtime($path)
                ];
            }
        }
        return $reports;
    }
}
