<?php

namespace FusionStoreBundle\Module;

use Module;
use Context;
use Order;
use Customer;
use Configuration;
use FusionStoreBundle\Invoice\OrderInvoice;

class InvoiceModule extends Module
{
    protected $FusionModule = null;

    protected $_order = null;

    protected $local_invoice_folder = null;

    protected $invoice_local_file = null;

    protected $invoice_extension = '.pdf';

    public $invoice = null;

    function __construct()
    {
        parent::__construct();

        /* Connect to Fusion Services */
        if( class_exists('FusionStoreBundle\Module\AdminModule') ){
            $this->FusionModule = new \FusionStoreBundle\Module\AdminModule($this, $this->context);
        }

        $this->local_invoice_folder = _PS_ROOT_DIR_.'/modules/'.$this->name.'/invoices/';
    }

    public function install()
    {
        $install_success = parent::install();
        if( !is_dir($this->local_invoice_folder) ){
            $install_success &= mkdir($this->local_invoice_folder);
        }
        return $install_success;
    }

    public function validateToken( $token )
    {
        if( $token == md5($this->_order->id.$this->_order->reference) ){
            return true;
        }
        return false;
    }

    public function loadOrder( $order )
    {
        if ($order instanceof Order) {
            $this->_order = $order;
        }else if( is_int($order) ){
            $this->_order = new Order($order);
        }else{
            return false;
        }

        $this->invoice = new OrderInvoice();
        $this->invoice->folder = $this->local_invoice_folder;
        $this->invoice->extension = $this->invoice_extension;
        $this->invoice->name = $this->_order->reference;
        $this->invoice->load();

        return true;
    }

    public function invoiceExists()
    {
        return file_exists($this->invoice->file);
    }

    public function getInvoiceUrl()
    {
        return Context::getContext()->link->getModuleLink(
            $this->name,
            $this->invoice_controller,
            array(
                'orderId' => $this->_order->id, 's' => md5( $this->_order->id.$this->_order->reference )
            )
        );
    }

    public function processInvoice( $invoice_file )
    {
        if( file_exists($invoice_file) ){
            return copy($invoice_file, $this->invoice->file);
        }
        return false;
    }

}
