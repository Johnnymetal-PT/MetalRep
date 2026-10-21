<?php

namespace FusionStoreBundle\Reports;

class ImportProductReport
{
    private $result = true;

    private $errors = [];

    private $need_alert = false;

    private $product = null;

    private $ean13 = null;

    private $wholesale_price = null;

    private $price = null;

    private $id_tax_rules_group = null;

    private $categorys = null;

    private $weight = null;

    private $images = null;

    private $features = null;

    private $combinations = null;

    private $tags = null;

    private $ignore_line = false;

    public function getPropNotes( $propdata )
    {
        if( is_array($propdata) ){
            return $propdata;
        }else{
            return ['',false];
        }
    }

    public function getReport()
    {
        return [
            'notes' => [
                'product'             => $this->getPropNotes($this->product),
                'ean13'               => $this->getPropNotes($this->ean13),
                'wholesale_price'     => $this->getPropNotes($this->wholesale_price),
                'price'               => $this->getPropNotes($this->price),
                'id_tax_rules_group'  => $this->getPropNotes($this->id_tax_rules_group),
                'categorys'           => $this->getPropNotes($this->categorys),
                'weight'              => $this->getPropNotes($this->weight),
                'images'              => $this->getPropNotes($this->images),
                'tags'                => $this->getPropNotes($this->tags),
                'features'            => $this->getPropNotes($this->features),
                'combinations'        => $this->getPropNotes($this->combinations),
            ],
            'need_alert'  => $this->need_alert,
            'errors'      => $this->errors,
            'result'      => $this->result
        ];
    }

    public function alert( $note_label, $note_value, $alert = false )
    {
        if( property_exists($this, $note_label) ){
            $this->{$note_label} = [ $note_value, $alert];
            if( $alert === true ){
                $this->need_alert = true;
            }
        }
        return $this;
    }

    public function result($result)
    {
        $this->result = (bool)$result;
        return $this;
    }

    public function ignore( $ignore = null )
    {
        if( $ignore===null ){
            return $this->ignore_line;
        }
        $this->ignore_line = true;
        return $this;
    }

    public function log($log)
    {
        $this->errors[] = $log;
        return $this;
    }

    public function lastError()
    {
        return implode('<br>',$this->errors);
    }

    public function getAjaxResponse()
    {
        return [ $this->result, $this->lastError() ];
    }
}
