<?php

namespace FusionStoreBundle\Services;

use Module;
use Context;

class FusionService
{
    protected $context = null;
    protected $module = null;

    public $front_controllers = [];

    public function __construct( Module $module, Context $context = null )
    {
      $this->module = $module;
      $this->context = $context;
    }

    public function install()
    {
        return true;
    }

    public function uninstall()
    {
        return true;
    }

    public function getEntity()
    {
        return [];
    }

    public function getHooks()
    {
        return [];
    }

}
