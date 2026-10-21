<?php

namespace FusionStoreBundle\Import;

use PrestaShop\PrestaShop\Adapter\Import\ImportDataFormatter;
use PrestaShop\PrestaShop\Core\ConfigurationInterface;
use FusionStoreBundle\Entity\FusionSync;
use FusionStoreBundle\Reports\ImportProductReport;
use FusionStoreBundle\LegacyImportController;
use League\Csv\Reader as CSVReader;
use League\Csv\Writer as CSVWriter;
use League\Csv\Statement as CSVStatement;
use League\Csv\CannotInsertRecord;

use Db;
use Tools;
use Context;
use Combination;

class CombinationImport
{
    public $combinations = [];

    public $context = null;

    public $report = null;

    public $id_product = null;

    public $image_folder = null;

    public $import_folder = null;

    public function __construct( $id_product )
    {
        $this->context = Context::getContext();
        $this->report = new ImportProductReport();
        $this->import_folder = _PS_ADMIN_DIR_ . '/import/';
        $this->importhash = 'teste';
        $this->id_product = $id_product;
    }

    public function setMask( Array $mask )
    {
        $this->mask = $mask;
        return $this;
    }

    public function imageFolder( $folder )
    {
        $this->image_folder = $folder;
        return $this;
    }

    public function getImagesInFolder( $ean = false )
    {
        if( $ean === false ||  $this->image_folder === null )
            return '';

        $product_images = [];
        # Check in uploads folder
        for ( $i=1; $i <= 10 ; $i++ ) {
            $image_path = $this->image_folder.$ean.'_'.sprintf('%03d', $i).'.jpg';
            if(file_exists($image_path)){
                #$product_images[] = $image_path;
                $product_images[] = $this->context->link->getBaseLink().'modules/importpro/import/uploads/'.$ean.'_'.sprintf('%03d', $i).'.jpg';
            }
        }

        return implode(',', $product_images);
    }

    public function import()
    {
        $final_data = [];

        foreach ($this->combinations as $combination) {
            $row = [];

            # Set Product ID
            $row['id_product']  = $this->id_product;

            # Set Groups and attributtes
            $row['group']       = $combination['group'];
            $row['attribute']   = $combination['attribute'];

            # Set Combination data from submited mask
            foreach ($this->mask as $find_key) {
                if( isset($combination[$find_key]) ){
                    $row[$find_key] = $combination[$find_key];
                }
            }

            # Search Images by EAN13 code
            if( isset($row['ean13']) ){
                $row['image_url'] = $this->getImagesInFolder( $row['ean13'] );
            }

            $final_data[] = $row;
        }

        try {
            $writer = CSVWriter::createFromPath($this->import_folder.$this->importhash.'.csv', 'w+');
            $writer->setDelimiter(';');
            $writer->insertAll($final_data);
        } catch (CannotInsertRecord $e) {
            $e->getRecords();
        }

        $_POST['regenerate'] = true;
        $_POST['type_value'] = array_keys($final_data[0]);

        $importController = new LegacyImportController();
        $importController->csv_file   = $this->importhash.'.csv';

        $crossStepsVariables = [];
        if ($crossStepsVars = Tools::getValue('crossStepsVars')) {
            $crossStepsVars = json_decode($crossStepsVars, true);
            if (count($crossStepsVars) > 0) {
                $crossStepsVariables = $crossStepsVars;
            }
        }


        $offset = 0;
        $done = $importController->attributeImport($offset, count($final_data), $crossStepsVariables, false);
        $importController->clearSmartyCache();

        return $done;
    }

}
