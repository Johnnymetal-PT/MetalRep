<?php

namespace FusionStoreBundle\Helper;

use Context;
use Module;

class UploadForm extends Form
{

  private $upload_folder = false;

  function __construct( Context $context, Module $module = null)
  {
    parent::__construct($context);
    return $this;
  }

  public function setUploadFolder( $upload_folder )
  {
    $this->upload_folder = $upload_folder;
  }

  public function render()
  {
    parent::render();
    return $render;
  }
}
