<?php

use FusionStoreBundle\Reports\ImportProductReportMaker;

class AdminFusionImportReportController extends ModuleAdminController
{
  	public $bootstrap = true;

  	public function __construct()
  	{
    		$this->lang = false;
        $this->allow_export = false;
    		parent::__construct();
	  }

  	public function setMedia($isNewTheme = false)
    {
        parent::setMedia($isNewTheme);
        #Media::addJsDef(array());
        #$this->context->controller->addCSS($this->_path.'views/css/admin/sim-edit.css');
    		#$this->context->controller->addJS($this->_path.'views/js/admin/sim-render.js');
    }

    public function initContent()
    {
        $available_modules = $this->_getModulesList();

        $this->context->smarty->assign(array(
            'total_modules' => count($available_modules),
            'available_modules' => $available_modules,
        ));

        $this->content .= $this->context->smarty->fetch( _PS_MODULE_DIR_ . $this->module->name . '/src/FusionStoreBundle/Resources/views/Admin/Import/importreports.tpl' );
        $this->context->smarty->assign('content', $this->content);

        return parent::initContent();
    }

    public function postProcess()
    {
        if( Tools::isSubmit('action') && Tools::isSubmit('module') ){
            if(Tools::getValue('action')=='deleteReport'){
                $reports = new ImportProductReportMaker();
                $reports->module( Tools::getValue('module') );
                $result = $reports->deleteByName( Tools::getValue('filename') );
                FusionStoreBundle\Tools::ajaxResponse('ok', $result);
            }else if(Tools::getValue('action')=='getModuleReport'){
                $reports = $this->getModuleReport( Tools::getValue('module') );
                $this->context->smarty->assign([
                  'module'    => Tools::getValue('module'),
                  'reports'   => $reports
                ]);
                $html = $this->context->smarty->fetch( _PS_MODULE_DIR_ . $this->module->name . '/src/FusionStoreBundle/Resources/views/Admin/Import/reports.tpl' );
                FusionStoreBundle\Tools::ajaxResponse(['html'=>$html]);
            }
        }else{
            return parent::postProcess(true);
        }
    }

    public function getModuleReport( $module_name )
    {
        $reports = new ImportProductReportMaker();
        $reports->module($module_name);
        $reps = $reports->getReports();
        foreach ($reps as &$repo) {
            $repo['need_alert'] = false;
            $repo['result'] = false;
            $repo['bad_weight'] = 0;
            $repo['bad_ean13'] = 0;
            $repo['bad_features'] = 0;
            foreach ($repo['contents'] as $item) {
                if( (bool)$item['need_alert']){
                    $repo['need_alert'] = true;
                }
                if( (bool)$item['result']){
                    $repo['result'] = true;
                }

                foreach ($item['report']['notes'] as $key => $note) {
                    if($note){
                        if( $key == 'weight' && (bool)$note[1] ){
                            $repo['bad_weight']++;
                        }
                        if( $key == 'ean13' && (bool)$note[1] ){
                            $repo['bad_ean13']++;
                        }
                        if( $key == 'features' && (bool)$note[1] ){
                            $repo['bad_features']++;
                        }
                    }
                }
            }
        }
        return $reps;
    }

    public function _getModulesList()
    {
        $list = [];
        $modules = Module::getModulesOnDisk();
        foreach ($modules as $module) {
            if( $module->parent_class == 'FusionStoreBundle\Module\ProductsApiModule' && $module->installed){
                $list[] = [
                    'name'        => $module->displayName,
                    'module_name' => $module->name,
                    'logo'        => __PS_BASE_URI__.'modules/'.$module->name.'/logo.png',
                ];
            }
        }
        return $list;
    }

}
?>