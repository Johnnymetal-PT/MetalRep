<?php

namespace FusionStoreBundle\Invoice;

use Context;
use Order;
use Customer;
use Configuration;
use FusionStoreBundle\Mail\MailBuilder;
use FusionStoreBundle\Mail\Sender;

class InvoiceSender
{
    private $context;

    private $order;

    private $customer;

    private $files;

    private $template;

    private $subject;

    public function __construct( Context $context = null, Order $order = null, Customer $customer = null )
    {
        if( !$context ){
            $context = Context::getContext();
        }
        if( $order != null ){
            $this->order = $order;
        }
        if( $order != null ){
            $this->customer = $customer;
        }
        $this->context = $context;
        return $this;
    }

    public function template( $template )
    {
        $this->template = $template;
        return $this;
    }

    public function subject( $subject )
    {
        $this->subject = $subject;
        return $this;
    }

    public function order( $id_order )
    {
        $this->order = new Order((int)$id_order);
        $this->customer = new Customer($this->order->id_customer);
        return $this;
    }

    public function invoice( $invoice_file )
    {
        if( file_exists($invoice_file) ){
            $this->files[] = $invoice_file;
        }
        return $this;
    }

    public function send( $email_data, $email_folder )
    {

        if ($email_data instanceof MailBuilder) {
            $email_data = $email_data->build();
        }

        return Sender::send(
            $this->context->language->id,
            $this->template,
            $this->subject,
            $email_data,
            $this->customer->email,
            $this->customer->firstname . ' ' . $this->customer->lastname,
            Configuration::get('PS_MAIL_USER'),
            null,
            $this->files,
            null,
            $email_folder
        );
    }

}
