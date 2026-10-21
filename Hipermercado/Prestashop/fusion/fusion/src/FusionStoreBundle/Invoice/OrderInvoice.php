<?php

namespace FusionStoreBundle\Invoice;

use Order;

class OrderInvoice
{
    public $mime = 'application/pdf';

    public $folder = '';

    public $file = '';

    public $extension = '';

    public $name = '';

    public $filename = '';

    public function __construct()
    {
    }

    public function load()
    {
        $this->filename = $this->name.$this->extension;
        $this->file = $this->folder.$this->filename;
        return $this;
    }
}
