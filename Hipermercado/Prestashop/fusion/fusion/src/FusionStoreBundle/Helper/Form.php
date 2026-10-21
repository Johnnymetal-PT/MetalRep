<?php

namespace FusionStoreBundle\Helper;

use Context;
use Module;

class Form
{

  private $context = null;
  private $module = null;

  function __construct( Context $context, Module $module = null)
  {
    $this->context = $context;
    $this->module = $module;
    return $this;
  }

  public function render(){}
}
