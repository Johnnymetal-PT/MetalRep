<?php

namespace FusionStoreBundle\Widgets;

use Tools;
use Dispatcher;
use Configuration;
use Shop;
use Group;
use Customer;
use Language;
use Currency;

class WidgetRender
{
    protected $context = null;

    protected $module = null;

    public function __construct( $module, $context = null )
    {
        if( $context === null ){
            $this->context = Context::getContext();
        } else {
            $this->context = $context;
        }

        $this->module = $module;
        return $this;
    }

    protected function getViewContext()
    {
        $controller_type = $this->context->controller->controller_type;
        return ( ($controller_type == 'front' || $controller_type == 'modulefront') ? 'Front' : 'Admin');
    }

    protected function getCacheId($name = null)
    {
        $cache_array = array();
        $cache_array[] = $name !== null ? $name : $this->name;
        if (Configuration::get('PS_SSL_ENABLED')) {
            $cache_array[] = (int) Tools::usingSecureMode();
        }
        if (Shop::isFeatureActive()) {
            $cache_array[] = (int) $this->context->shop->id;
        }
        if (Group::isFeatureActive() && isset($this->context->customer)) {
            $cache_array[] = (int) Group::getCurrent()->id;
            $cache_array[] = implode('_', Customer::getGroupsStatic($this->context->customer->id));
        }
        if (Language::isMultiLanguageActivated()) {
            $cache_array[] = (int) $this->context->language->id;
        }
        if (Currency::isMultiCurrencyActivated()) {
            $cache_array[] = (int) $this->context->currency->id;
        }
        $cache_array[] = (int) $this->context->country->id;

        return implode('|', $cache_array);
    }

    protected function getTemplate($template)
    {
        $overloaded = $this->isTemplateOverloaded( 'fusion', $template );
        $overloaded = str_replace(_PS_ROOT_DIR_,'',$overloaded);

        if ($overloaded === null) {
            return null;
        }

        if ($overloaded) {
            return ltrim($overloaded, '/');
        }elseif (Tools::file_exists_cache(_PS_MODULE_DIR_ . '/fusion/views/templates/' . strtolower($this->getViewContext()) . '/' . $template)) {
            return 'module:fusion/views/templates/' . strtolower($this->getViewContext()) . '/' . $template;
        }elseif (Tools::file_exists_cache(_PS_MODULE_DIR_ . 'fusion/src/FusionStoreBundle/Resources/views/' . $this->getViewContext() . '/Widget/' . $template)) {
            return 'module:fusion/src/FusionStoreBundle/Resources/views/' . $this->getViewContext() . '/Widget/' . $template;
        }else{
            return null;
        }
    }

    protected function isTemplateOverloaded($module_name, $template)
    {
        if (Tools::file_exists_cache(_PS_THEME_DIR_ . 'modules/' . $module_name . '/' . $template)) {
            return _PS_THEME_DIR_ . 'modules/' . $module_name . '/' . $template;
        } elseif (Tools::file_exists_cache(_PS_THEME_DIR_ . 'modules/' . $module_name . '/src/FusionStoreBundle/Resources/views/' . $this->getViewContext() . '/Widget/' . $template)) {
            return _PS_THEME_DIR_ . 'modules/' . $module_name . '/src/FusionStoreBundle/Resources/views/' . $this->getViewContext() . '/Widget/' . $template;
        } elseif (Tools::file_exists_cache(_PS_THEME_DIR_ . 'modules/' . $module_name . '/Widgets/' . $template)) {
            return _PS_THEME_DIR_ . 'modules/' . $module_name . '/Widgets/' . $template;
        } elseif (Tools::file_exists_cache(_PS_MODULE_DIR_ . $module_name . '/views/templates/' . strtolower($this->getViewContext()) . '/' . $template)) {
            return false;
        } elseif (Tools::file_exists_cache(_PS_MODULE_DIR_ . $module_name . '/src/FusionStoreBundle/Resources/views/' . $this->getViewContext() . '/Widget/' . $template)) {
            return false;
        }
        return null;
    }

    public function renderWidget($hookName = null, array $configuration = [])
    {
        $_widget = ucfirst(Tools::toCamelCase($hookName));
        if( method_exists($this, 'widget'.$_widget) ){
            return $this->{'widget'.$_widget}($configuration);
        }
        if( isset($configuration['widname'])){
            $_widget = ucfirst(Tools::toCamelCase($configuration['widname']));
            if( method_exists($this, 'widget'.$_widget) ){
                return $this->{'widget'.$_widget}($configuration);
            }
        }
        return;
    }
}
