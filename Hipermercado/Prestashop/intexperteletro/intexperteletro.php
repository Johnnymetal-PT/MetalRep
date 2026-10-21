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

class IntExperteletro extends \FusionStoreBundle\Module\ProductsApiModule implements \FusionStoreBundle\Module\ProductsApiInterface
{
    public $hooks_register = [];

    public function __construct()
    {
        $this->name = 'intexperteletro';
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

        $this->displayName = $this->l('Experteletro API');
        $this->description = $this->l('Experteletro API connector module');
        $this->confirmUninstall = $this->l('Pretende desinstalar?');
        $this->ps_versions_compliancy = array('min' => '1.6', 'max' => _PS_VERSION_);

        $this->default_active = Configuration::get('API_EXPERTELETRO_PRODUCT_DEFAULT_ACTIVE', '0');
    }

    public function getContent()
    {
        parent::getContent();

        if (((bool) Tools::isSubmit('_action')) == true && Tools::getValue('_action') == 'syncProduct') {
            $this->syncProductEntry();
        }

        if (((bool) Tools::isSubmit('submitIntExperteletroModule')) == true) {
            $this->postProcess();
        }

        $this->context->smarty->assign('module_dir', $this->_path);

        if( Configuration::get('API_EXPERTELETRO_ACTIVE')
          && Configuration::get('API_EXPERTELETRO_URL', '') != ""
        ){
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
        $helper->submit_action = 'submitIntExperteletroModule';
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
                        'name' => 'API_EXPERTELETRO_ACTIVE',
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
                        'col' => 3,
                        'type' => 'text',
                        'name' => 'API_EXPERTELETRO_URL',
                        'label' => $this->l('URL')
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
                        'name' => 'API_EXPERTELETRO_PRODUCT_DEFAULT_ACTIVE',
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
            'API_EXPERTELETRO_ACTIVE' => Configuration::get('API_EXPERTELETRO_ACTIVE'),
            'API_EXPERTELETRO_URL' => Configuration::get('API_EXPERTELETRO_URL', ''),
            'API_EXPERTELETRO_PRODUCT_DEFAULT_ACTIVE' => Configuration::get('API_EXPERTELETRO_PRODUCT_DEFAULT_ACTIVE', true)
        );
    }

    protected function postProcess()
    {
        $form_values = $this->getConfigFormValues();

        foreach (array_keys($form_values) as $key) {
            Configuration::updateValue($key, Tools::getValue($key));
        }

        if (Configuration::get('API_EXPERTELETRO_ACTIVE')) {
            if ( Configuration::get('API_EXPERTELETRO_URL') == ""
            ){
                $this->context->controller->errors[] = $this->l("API access info is missing.");
            } else {
                $this->context->controller->confirmations[] = $this->l("Settings saved successfully.");
            }
        } else {
            $this->context->controller->confirmations[] = $this->l("Settings saved successfully.");
        }
    }

    private function syncProductEntry()
    {
        $entry_key = Tools::getValue('_key');

        $result = $this->syncProduct(
            $entry_key,
            Configuration::get('API_EXPERTELETRO_PRODUCT_DEFAULT_ACTIVE', '0'),
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

    private function filterStock($product_data)
    {
        switch ($product_data['quantity']) {
          case 'Limitado':
            $quantity = 2;
            break;

          case 'Indisponivel':
            $quantity = 0;
            break;

          case 'Disponivel':
            $quantity = 5;
            break;

          default:
            $quantity = 0;
            break;
        }

        $product_data['quantity'] = $quantity;
        return $product_data;
    }

    public function filterProductData( $product_data )
    {
        foreach ($product_data as &$product) {
            if(isset($product['galeria'])){
              $galeria = explode( ',', $product['galeria'] );
              $product['images'] = $galeria;
            }

            #$images = [ $product_data['image'] ];

            $categorys = explode('->', $product['category']);

            $product['category'] = $categorys[0];
            $product['sub_category'] = end($categorys);

            $product['wholesale_price'] = $product['unit_price'];
            $product['unit_price'] = $this->filterProductPrice($product);
            $product['unit_price_tax'] = $product['unit_price'];
            $product = $this->filterStock($product);
        }
        return $product_data;
    }

    public function getProductsFeed( $update_timestamp = false, $ignore_cache = true )
    {
        $feed_url = Configuration::get('API_EXPERTELETRO_URL');

        $csv = new FusionStoreBundle\Import\Adapter\CSV($feed_url);
        $csv->ignore_cache = $ignore_cache;

        if( $update_timestamp ){
            $csv->refreshTimeStamp();
        }

        $csv->curl = true;

        $csv->utf8Enc(false);

        $csv->setMatches([
            'nome'            => 'name_pt',
            'familia'         => 'category',
            'referencia'      => 'reference',
            'ean'             => 'ean13',
            'preco'           => 'unit_price',
            'disponibilidade' => 'quantity',
            'marcas'          => 'brand',
            'caracteristicas' => 'description_pt',
            'resumo'          => 'description_short_pt',
            'imagens'         => 'image',
            'galeria'         => 'galeria',
        ], true);

      	$_records = $csv->getRecords( $update_timestamp );

      	file_put_contents(_PS_MODULE_DIR_.$this->name.'/logs/'.date('d_m_Y-H_i').'.flog', $csv->req_response );

        return $this->filterProductData( $_records );
    }

    public function provideInternalFeed()
    {
        $feed_url = Configuration::get('API_EXPERTELETRO_URL');
        $csv = new FusionStoreBundle\Import\Adapter\CSV($feed_url);
        return $csv->getFeedFromCache();
    }
}
