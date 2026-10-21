<?php

use FusionStoreBundle\Locator;
use FusionStoreBundle\Widgets\FusionBundleWidget;

class FusionLocatorModuleFrontController extends ModuleFrontController
{
    public $ssl = true;

    public function initContent()
    {
        parent::initContent();
        if( Tools::getValue('getlist') ){
            $this->displayAjaxLocationList();
            die();
        }else if( Tools::getValue('locate') ){
            (new Locator($this->context))->setCustomerLocate(Tools::getValue('locate'));
            die(json_encode(array('st'=>'OK')));
        }
        header('Location: '.$this->context->link->getBaseLink());
        exit;
    }

    public function displayAjaxLocationList()
    {
        ob_end_clean();
        header('Content-Type: application/json');
        $this->ajaxRender(Tools::jsonEncode(array(
            'list_html' => (new FusionStoreBundle\Widgets\FusionBundleWidget($this->module, $this->context))->renderWidget('StoreLocator', [ 'renderwhat'=>'window_content' ])
        )));
        return;
    }
}
