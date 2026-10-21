<?php

namespace FusionStoreBundle\Services;

use Customer;
use Context;

class CustomerAuthentication
{

    public function __construct()
    {
        return $this;
    }
    
    public function initSession( $email )
    {
        $customer = new Customer();
        $customer->getByEmail($email, null, false);
        Context::getContext()->updateCustomer($customer);
        return $customer->isLogged(true);
    }
}
