<?php

if (!defined('_PS_VERSION_')) {
    exit;
}

if(!defined('FUSION_SERVICES_DIR'))
  define( 'FUSION_SERVICES_DIR', _PS_ROOT_DIR_.'/modules/fusion/' );

include_once(FUSION_SERVICES_DIR.'vendor/autoload.php');

use PrestaShop\PrestaShop\Core\Module\WidgetInterface;
use FusionStoreBundle\MediaPlugins;
use FusionStoreBundle\Tools as FusionTools;
use FusionStoreBundle\Entity\FusionSync;
use Statickidz\GoogleTranslate;

class Fusion extends Module implements WidgetInterface
{
    public $hooks_register = [
        'actionAdminControllerSetMedia',
        'actionAdminLoginControllerBefore',
        'actionAdminControllerInitAfter',
        'displayAdminAfterHeader'
    ];

    private $FusionModule;

    private $FusionServices;

    public function __construct()
    {
        $this->name = 'fusion';
        $this->tab = 'administration';
        $this->version = '9.0.0';
        $this->author = 'fusion';
        $this->need_instance = 1;
        $this->trusted = true;
        $this->bootstrap = true;
        $this->first_run = true;
        $this->license_key = '5fba7b67af07e44ac9213ea04400a0ee';

        parent::__construct();

        $this->displayName = $this->l('Fusion');
        $this->description = $this->l('Fusion');
        $this->ps_versions_compliancy = array('min' => '1.7.0', 'max' => _PS_VERSION_);

        /* Connect to Fusion Services */
        if( class_exists('FusionStoreBundle\Services\AdminModuleService') ){
            $this->FusionServices = new FusionStoreBundle\Services\AdminModuleService($this);
            if( $this->FusionServices->init() ){
                $this->first_run = false;
            }
        }

        if( class_exists('FusionStoreBundle\Module\AdminModule') ){
            $this->FusionModule = new FusionStoreBundle\Module\AdminModule($this, $this->context);
        }

    }

    public function renderWidget($hookName = null, array $configuration = [])
    {
        /* Connect to Fusion Widgets and get Fusion bundle widgets */
        if( class_exists('FusionStoreBundle\Widgets\FusionBundleWidget') ){
            return (new FusionStoreBundle\Widgets\FusionBundleWidget($this, $this->context))->renderWidget($hookName, $configuration);
        }
    }

    public function getWidgetVariables($hookName = null, array $configuration = []){}

    public function uninstall()
    {
        $success = true;
        foreach ($this->hooks_register as $hook_name) {
            $success &= $this->unregisterHook($hook_name);
        }
        $success &= parent::uninstall();
        return true;
    }

    public function install()
    {
        if (Shop::isFeatureActive()) {
            Shop::setContext(Shop::CONTEXT_ALL);
        }

        if (!parent::install()) {
            return false;
        }

        $success = true;

        foreach ($this->hooks_register as $hook_name) {
            $success &= $this->registerHook($hook_name);
        }

        if($success){
            return true;
        }

        $this->uninstall();
        return false;
    }

    public function getContent()
    {
        $success = true;

        if( ((bool)Tools::isSubmit('action')) == true && Tools::getValue('action') == 'validate' ){
            $this->FusionServices->generateCert(
                Tools::getValue('origin'),
                Tools::getValue('certkey'),
                Tools::getValue('secret')
            );
            $this->first_run = $this->FusionServices->getCertKey() ? false : true;
        }else if (((bool) Tools::isSubmit('submit'.$this->name)) == true && method_exists($this,'postProcess')) {
            $this->postProcess();
            return '';
        }
        return '';
    }

    public function postProcess()
    {
        # Process Fusion Module Requests
        if( Tools::getValue('action') == 'changeFusionSettings' ){
            if(Tools::getValue('type')=='bool'){
                $value = (bool)Tools::getValue('value');
            }else{
                $value = (string)Tools::getValue('value');
            }
            $result = $this->FusionServices->setConfig( Tools::getValue('param'), $value );
            if( $result ){
                $this->FusionModule->ajaxResponse($this->trans('Saved', [], 'Modules.Fusion.Fusion'), true);
            }else{
                $this->FusionModule->ajaxResponse($this->trans('Error', [], 'Modules.Fusion.Fusion'), false);
            }
        }else if( Tools::getValue('action') == 'getEntityStatus' ){
            # - getEntityStatus
            $result = $this->FusionServices->getEntityStatus();
            $this->FusionModule->ajaxResponse($result, true);
        }else if( Tools::getValue('action') == 'getHooksStatus' ){
            # - getHooksStatus
            $result = $this->FusionServices->getHooksStatus();
            $this->FusionModule->ajaxResponse($result, true);
        }else if( Tools::getValue('action') == 'getFusionSettings' ){
            # - getFusionSettings
            $params = Tools::getValue('params');
            foreach ($params as $param => &$value) {
                $value = $this->FusionServices->getConfig( $param );
            }
            $this->FusionModule->ajaxResponse($params, true);
        }else if( Tools::getValue('action') == 'fusionAction' ){
            $result = $this->FusionServices->fusionAction( Tools::getValue('dowhat') );
            if( $result ){
                $this->FusionModule->ajaxResponse($this->trans('Success', [], 'Modules.Fusion.Fusion'), true);
            }else{
                $this->FusionModule->ajaxResponse($this->trans('Error', [], 'Modules.Fusion.Fusion'), false);
            }
        }else if( Tools::getValue('action') == 'invalidCert' ){
            $this->FusionServices->generateCert('', '');
            $this->FusionModule->ajaxResponse($this->trans('', [], 'Modules.Fusion.Fusion'), true);
        }else if( Tools::getValue('action') == 'changeProductSkipOption' ){
            $fsync = new FusionSync( (int)Tools::getValue('id_sync_entry') );
            $fsync->skip_product = (int)Tools::getValue('skip_this_product_from_update');
            if( $fsync->save() ){
                $this->FusionModule->ajaxResponse($this->trans('Saved', [], 'Modules.Fusion.Fusion'), true);
            }else{
                $this->FusionModule->ajaxResponse($this->trans('Error', [], 'Modules.Fusion.Fusion'), false);
            }
        }else{
            # Process Services Request Bind to Fusion Module
            $hook_postProcess = (new FusionStoreBundle\Hooks\FusionServicesHooks($this, $this->context))->Hook(
              'PostProcess',
              [ 'action' => Tools::getValue('action') ]
            );
            $success = true;
            foreach ($hook_postProcess as $hook_response) {
                $success &= $hook_response;
            }
            if( $success ){
                $this->FusionModule->ajaxResponse($this->trans('Saved', [], 'Modules.Fusion.Fusion'), true);
            }else{
                $this->FusionModule->ajaxResponse($this->trans('Error', [], 'Modules.Fusion.Fusion'), false);
            }
        }
    }

    public function hookModuleRoutes( $params )
    {
        $routes = [
            'locator' => array(
                'controller' => 'locator',
                'rule' =>       'locator',
                'keywords' => array(
                    'module'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'module')
                ),
                'params' => array(
                    'fc' => 'module',
                    'module' => 'fusion'
                ),
            ),
            'shoppingfeeds' => array(
                'controller' => 'shoppingfeeds',
                'rule' =>       'feeds/{feed_engine}-{feed_name}-{feed_token}.{feed_response_type}',
                'keywords' => array(
                    'module'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'module'),
                    'feed_engine'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'feed_engine'),
                    'feed_name'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'feed_name'),
                    'feed_token'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'feed_token'),
                    'feed_response_type'    =>  array('regexp' => '[_a-zA-Z0-9_-]+', 'param' => 'feed_response_type')
                ),
                'params' => array(
                    'fc' => 'module',
                    'module' => 'fusion'
                ),
            )
        ];
        return $routes;
    }

    public function hookActionAdminControllerSetMedia()
    {
        Media::addJsDef([
            'fusion' => [
                'shop_version' => _PS_VERSION_,
                'certkey' => '',
                'integrity' => '',
                'urls' => [
                    'fusion_services'   => $this->context->link->getAdminLink('AdminModules', false)
                    . '&tab_module=' . $this->tab . '&configure=' . $this->name . '&token='
                    . Tools::getAdminTokenLite('AdminModules'),
                    'modules'           => $this->context->link->getAdminLink('AdminModules', false)
                    . '&tab_module=' . $this->tab . '&module_name=' . $this->name
                    . '&token=' . Tools::getAdminTokenLite('AdminModules'),
                ]
            ]
        ]);


        MediaPlugins::load($this->context, 'fusion');
        MediaPlugins::load($this->context, 'bs-modal');

        if( Tools::getValue('controller') == 'AdminModules' &&  Tools::getValue('configure') == $this->name ){
            MediaPlugins::load($this->context, 'fusion-lib');
        }
        return;
    }

    public function hookDisplayHeader( $params )
    {
        $this->context->controller->registerJavascript('modules-fusion', 'modules/' . $this->name . '/libs/checkout/checkout.js', ['position' => 'bottom', 'priority' => 170]);

        $this->context->controller->registerStylesheet('modules-locator', 'modules/' . $this->name . '/libs/css/locator.1.4.css', ['position' => 'top', 'priority' => 171]);
        $this->context->controller->registerJavascript('modules-locator', 'modules/' . $this->name . '/libs/js/locator.1.4.js', ['position' => 'bottom', 'priority' => 171]);
    }

    public function hookActionAdminLoginControllerBefore( $params )
    {
        $this->FusionServices->lookForAutoUpdates();
    }

    public function hookActionAdminControllerInitAfter( $params )
    {
        $this->FusionServices->lookForAutoUpdates();
    }

    public function hookDisplayAdminAfterHeader( $params )
    {
        return (new FusionStoreBundle\Hooks\FusionBundleHooks($this, $this->context))->DisplayAdminAfterHeader($params).'<style>'.$this->FusionServices->hideModulesOnList().'</style>';
    }

    public function hookDisplayAdminProductsOptionsStepTop( $params )
    {
        return (new FusionStoreBundle\Hooks\FusionBundleHooks($this, $this->context))->DisplayAdminProductsOptionsStepTop($params);
    }

    public function hookDisplayAdminOrderTabOrder( $params )
    {
        return (new FusionStoreBundle\Hooks\FusionBundleHooks($this, $this->context))->DisplayAdminOrderTabOrder($params);
    }

    public function hookDisplayAdminProductsMainStepLeftColumnMiddle( $params )
    {
        return (new FusionStoreBundle\Hooks\FusionBundleHooks($this, $this->context))->DisplayAdminProductsMainStepLeftColumnMiddle($params);
    }

    public function hookFilterCmsContent( $params ){}

}
