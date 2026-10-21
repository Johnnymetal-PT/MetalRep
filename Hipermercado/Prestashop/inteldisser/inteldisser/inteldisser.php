<?php
/**
* 2007-2021 PrestaShop
*
* NOTICE OF LICENSE
*
* This source file is subject to the Academic Free License (AFL 3.0)
* that is bundled with this package in the file LICENSE.txt.
* It is also available through the world-wide-web at this URL:
* http://opensource.org/licenses/afl-3.0.php
* If you did not receive a copy of the license and are unable to
* obtain it through the world-wide-web, please send an email
* to license@prestashop.com so we can send you a copy immediately.
*
* DISCLAIMER
*
* Do not edit or add to this file if you wish to upgrade PrestaShop to newer
* versions in the future. If you wish to customize PrestaShop for your
* needs please refer to http://www.prestashop.com for more information.
*
*  @author    PrestaShop SA <contact@prestashop.com>
*  @copyright 2007-2021 PrestaShop SA
*  @license   http://opensource.org/licenses/afl-3.0.php  Academic Free License (AFL 3.0)
*  International Registered Trademark & Property of PrestaShop SA
*/

if (!defined('_PS_VERSION_')) {
    exit;
}

class IntEldisser extends \FusionStoreBundle\Module\ProductsApiModule implements \FusionStoreBundle\Module\ProductsApiInterface
{
    public $hooks_register = [];

    public function __construct()
    {
        $this->name = 'inteldisser';
        $this->tab = 'content_management';
        $this->version = '1.1.0';
        $this->author = 'fusion';
        $this->need_instance = 1;
        $this->trusted = true;

        /**
         * Set $this->bootstrap to true if your module is compliant with bootstrap (PrestaShop 1.6)
         */
        $this->bootstrap = true;

        parent::__construct();

        $this->displayName = $this->l('Eldisser Scrapper');
        $this->description = $this->l('Eldisser Scrapper connector module');
        $this->confirmUninstall = $this->l('Pretende desinstalar?');
        $this->ps_versions_compliancy = array('min' => '1.6', 'max' => _PS_VERSION_);

        $this->apiCacheFile = $this->name . '/download/'.date('d_m_Y').'_feed.csv';

        $this->default_active = Configuration::get('ELDISSER_PRODUCT_DEFAULT_ACTIVE', '0');

        $this->translate_engine = new \FusionStoreBundle\TranslateEngine\GoogleTranslateEngine( Configuration::get('TRANSLATE_API_KEY'), 'pt', 'es' );
        $this->translate_engine->map(['name','description','description_short']);
    }

    public function getContent()
    {
        parent::getContent();

        if (((bool) Tools::isSubmit('_action')) == true && Tools::getValue('_action') == 'syncProduct') {
            $this->syncProductEntry();
        }

        if (((bool) Tools::isSubmit('submitIntSorefozModule')) == true) {
            $this->postProcess();
        }

        $this->context->smarty->assign('module_dir', $this->_path);

        if( Configuration::get('ELDISSER_ACTIVE')){
            $sync_form = $this->renderCategoryMatchForm() . $this->getSyncTable();
        }else{
            $sync_form = '';
        }

        return $this->renderForm().$sync_form;
    }

    protected function renderForm()
    {
        $helper = new HelperForm();

        $helper->show_toolbar             = false;
        $helper->table                    = $this->table;
        $helper->module                   = $this;
        $helper->default_form_language    = $this->context->language->id;
        $helper->allow_employee_form_lang = Configuration::get('PS_BO_ALLOW_EMPLOYEE_FORM_LANG', 0);

        $helper->identifier    = $this->identifier;
        $helper->submit_action = 'submitIntSorefozModule';
        $helper->currentIndex  = $this->context->link->getAdminLink('AdminModules', false) .
        '&configure=' . $this->name . '&tab_module=' . $this->tab . '&module_name=' . $this->name;
        $helper->token         = Tools::getAdminTokenLite('AdminModules');

        $helper->tpl_vars = array(
            'fields_value' => $this->getConfigFormValues(),
            /* Add values for your inputs */
            'languages' => $this->context->controller->getLanguages(),
            'id_language' => $this->context->language->id
        );

        return $helper->generateForm(array(
            $this->getConfigForm()
        ));
    }

    protected function getConfigForm()
    {
        return array(
            'form' => array(
                'legend' => array(
                    'title' => $this->l('Settings'),
                    'icon' => 'icon-cogs'
                ),
                'input' => array(
                    array(
                        'type' => 'switch',
                        'label' => $this->l('Active'),
                        'name' => 'ELDISSER_ACTIVE',
                        'is_bool' => true,
                        'values' => array(
                            array(
                                'id' => 'active_on',
                                'value' => true,
                                'label' => $this->l('Enabled')
                            ),
                            array(
                                'id' => 'active_off',
                                'value' => false,
                                'label' => $this->l('Disabled')
                            )
                        )
                    ),
                    array(
                        'col' => 6,
                        'type' => 'text',
                        'name' => 'TRANSLATE_API_KEY',
                        'hint' => 'Test: Hola > ' . ($this->translate_engine->translate('Hola')),
                        'label' => $this->l('Google API Key for translate')
                    ),
                    array(
                      'type'  => 'categories',
                      'label' => $this->l('Product Category'),
                      'name'  => 'FS_IMPORT_DEFAULT_CATEGORY_'.$this->name,
                      'tree'  => array(
                        'id' => 'category',
                        'selected_categories' => array((int)Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_'.$this->name)),
                      ),
                    ),
                    array(
                        'type' => 'switch',
                        'label' => $this->l('Active product after import'),
                        'name' => 'ELDISSER_PRODUCT_DEFAULT_ACTIVE',
                        'is_bool' => true,
                        'values' => array(
                            array(
                                'id' => 'active_on',
                                'value' => true,
                                'label' => $this->l('Enabled')
                            ),
                            array(
                                'id' => 'active_off',
                                'value' => false,
                                'label' => $this->l('Disabled')
                            )
                        )
                    ),
                ),
                'submit' => array(
                    'title' => $this->l('Save')
                )
            )
        );
    }

    protected function getConfigFormValues()
    {
        return array(
            'FS_IMPORT_DEFAULT_CATEGORY_'.$this->name => Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_'.$this->name),
            'ELDISSER_ACTIVE' => Configuration::get('ELDISSER_ACTIVE'),
            'TRANSLATE_API_KEY' => Configuration::get('TRANSLATE_API_KEY', ''),
            'ELDISSER_PRODUCT_DEFAULT_ACTIVE' => Configuration::get('ELDISSER_PRODUCT_DEFAULT_ACTIVE', true)
        );
    }

    protected function postProcess()
    {
        $form_values = $this->getConfigFormValues();

        foreach (array_keys($form_values) as $key) {
            Configuration::updateValue($key, Tools::getValue($key));
        }

        $this->context->controller->confirmations[] = $this->l("Settings saved successfully.");
    }

    private function syncProductEntry()
    {
        $entry_key = Tools::getValue('_key');

        $result = $this->syncProduct(
            $entry_key,
            Configuration::get('ELDISSER_PRODUCT_DEFAULT_ACTIVE', '0'),
            true
        );

        ob_end_clean();
        header('Content-Type: application/json');
        echo json_encode([
          'status' => ( $result ? 'OK' : 'FAIL' ),
          'data' => $result[1]
        ]);
        die();
    }

    public function filterProductData( $product_data )
    {
        foreach ($product_data as &$product) {
            $product['reference'] = $product['ean13'];
            $product['images'] =  str_replace(' ', '%20', $product['images']);
            $fixPriceFormat = str_replace('.', '', $product['unit_price']);
            $product['unit_price'] = str_replace(',', '.', $fixPriceFormat);
            $product['wholesale_price'] = $product['unit_price'];
            $product['unit_price'] = $this->filterProductPrice($product);
            $product['unit_price_tax'] = $product['unit_price'];
            $product['description_pt'] = utf8_decode($product['description_pt']);
            $product['description_short_pt'] = utf8_decode($product['description_short_pt']);
            $product = $this->filterStock($product);
        }
        return $product_data;
    }

    private function filterStock($product_data)
    {
        $qty = intval($product_data['quantity']);

        switch (true) {
          case $qty == 0:
            $quantity = 0;
            break;
          case $qty < 5:
            $quantity = 2;
            break;
          case $qty >= 5:
            $quantity = 5;
            break;
          default:
            $quantity = 0;
            break;
        }
        $product_data['quantity'] = $quantity;
        return $product_data;
    }

    public function getProductsFeed( $update_timestamp = false, $ignore_cache = true )
    {
        $file = $this->getFile();

        if( $file === false ){
            return [];
        }

        $csv = new FusionStoreBundle\Import\Adapter\CSV($file);
        $csv->ignore_cache = $ignore_cache;

        $csv->setMatches([
            'NOME_PRODUTO'              => 'name_pt',
            'NOME_FAMILIA'              => 'category',
            'Referencia'                => 'reference',
            'EAN'                       => 'ean13',
            'PR_LIQUIDO'                => 'unit_price',
            'QtdLinear'                 => 'quantity',
            'NOME_MARCA'                => 'brand',
            'Caracteristicas_Completa'  => 'description_pt',
            'Caracteristicas_Resumo'    => 'description_short_pt',
            'LinkImagem'                => 'images',
        ], true);
        $csv->delimiter = ",";

        $api_feed = $this->filterProductData( $csv->getRecords( $update_timestamp ) );
        $_feed = [];

        foreach ($api_feed as $key => $row) {
            if( strlen($row['ean13']) == 13 ){
                $_feed[$key] = $row;
            }
        }

        return $_feed;
    }

    private function getFile()
    {
        // return _PS_BASE_URL_SSL_ . _MODULE_DIR_.$this->apiCacheFile;
        return _PS_MODULE_DIR_ . $this->apiCacheFile;
    }
}
