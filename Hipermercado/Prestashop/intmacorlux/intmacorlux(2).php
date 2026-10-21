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

class IntMacorlux extends \FusionStoreBundle\Module\ProductsApiModule implements \FusionStoreBundle\Module\ProductsApiInterface
{
    public $hooks_register = [];

    private $apiurl = "https://www.macorlux.pt/webservice.php?user={_user_}&pass={_pass_}&key={_apikey_}&format={_type_}&method={_call_type_}";
    private $apifiletype = "json";
    private $expireCache = 18000; # 5 horas

    public function __construct()
    {
        $this->name = 'intmacorlux';
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

        $this->displayName = $this->l('Macorlux API');
        $this->description = $this->l('Macorlux API connector module');
        $this->confirmUninstall = $this->l('Pretende desinstalar?');
        $this->ps_versions_compliancy = array('min' => '1.6', 'max' => _PS_VERSION_);

        $this->default_active = Configuration::get('API_MACORLUX_PRODUCT_DEFAULT_ACTIVE', '0');
    }

    public function getContent()
    {
        parent::getContent();

        if (((bool) Tools::isSubmit('_action')) == true && Tools::getValue('_action') == 'syncProduct') {
            $this->syncProductEntry();
        }

        if (((bool) Tools::isSubmit('submitIntMacorluxModule')) == true) {
            $this->postProcess();
        }

        $this->context->smarty->assign('module_dir', $this->_path);

        if (
            Configuration::get('API_MACORLUX_ACTIVE')
            && Configuration::get('API_MACORLUX_APIKEY', '') != ""
            && Configuration::get('API_MACORLUX_USERNAME', '') != ""
            && Configuration::get('API_MACORLUX_PASSWORD', '') != ""
        ) {
            $sync_form = $this->renderCategoryMatchForm() . $this->getSyncTable();
        } else {
            $sync_form = '';
        }

        return $this->renderForm() . $sync_form;
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
        $helper->submit_action = 'submitIntMacorluxModule';
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
                        'name' => 'API_MACORLUX_ACTIVE',
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
                        'name' => 'API_MACORLUX_APIKEY',
                        'label' => $this->l('API KEY')
                    ),
                    array(
                        'col' => 3,
                        'type' => 'text',
                        'name' => 'API_MACORLUX_USERNAME',
                        'label' => $this->l('API Username')
                    ),
                    array(
                        'col' => 3,
                        'type' => 'text',
                        'prefix' => '<i class="icon icon-key"></i>',
                        'name' => 'API_MACORLUX_PASSWORD',
                        'label' => $this->l('API Password')
                    ),
                    array(
                        'type'  => 'categories',
                        'label' => $this->l('Product Category'),
                        'name'  => 'FS_IMPORT_DEFAULT_CATEGORY_' . $this->name,
                        'tree'  => array(
                            'id' => 'category',
                            'selected_categories' => array((int)Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_' . $this->name)),
                        ),
                    ),
                    array(
                        'type' => 'switch',
                        'label' => $this->l('Active product after import'),
                        'name' => 'API_MACORLUX_PRODUCT_DEFAULT_ACTIVE',
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
            'FS_IMPORT_DEFAULT_CATEGORY_' . $this->name => Configuration::get('FS_IMPORT_DEFAULT_CATEGORY_' . $this->name),
            'API_MACORLUX_ACTIVE' => Configuration::get('API_MACORLUX_ACTIVE'),
            'API_MACORLUX_APIKEY' => Configuration::get('API_MACORLUX_APIKEY', ''),
            'API_MACORLUX_USERNAME' => Configuration::get('API_MACORLUX_USERNAME', ''),
            'API_MACORLUX_PASSWORD' => Configuration::get('API_MACORLUX_PASSWORD', ''),
            'API_MACORLUX_PRODUCT_DEFAULT_ACTIVE' => Configuration::get('API_MACORLUX_PRODUCT_DEFAULT_ACTIVE', true)
        );
    }

    protected function postProcess()
    {
        $form_values = $this->getConfigFormValues();

        foreach (array_keys($form_values) as $key) {
            Configuration::updateValue($key, Tools::getValue($key));
        }

        if (Configuration::get('API_MACORLUX_ACTIVE')) {
            if (
                Configuration::get('API_MACORLUX_USERNAME', '') == ""
                || Configuration::get('API_MACORLUX_APIKEY', '') == ""
                || Configuration::get('API_MACORLUX_PASSWORD', '') == ""
            ) {
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
            Configuration::get('API_MACORLUX_PRODUCT_DEFAULT_ACTIVE', '0'),
            true
        );

        ob_end_clean();
        header('Content-Type: application/json');
        echo json_encode([
            'status' => ($result ? 'OK' : 'FAIL'),
            'data' => $result[1]
        ]);
        die();
    }

    private function getApiUrl($call_type)
    {
        $replace_params = [
            '{_apikey_}' => Configuration::get('API_MACORLUX_APIKEY'),
            '{_user_}' => Configuration::get('API_MACORLUX_USERNAME'),
            '{_pass_}' => Configuration::get('API_MACORLUX_PASSWORD'),
            '{_type_}' => $this->apifiletype,
            '{_call_type_}' => $call_type
        ];

        $final_url = $this->apiurl;

        foreach ($replace_params as $find => $replace_value) {
            $final_url = str_replace($find, $replace_value, $final_url);
        }

        return $final_url;
    }

    // private function filterStock($product_data)
    // {
    //     switch ((int)$product_data['quantity']) {
    //         case 0:
    //             $quantity = 0;
    //             break;

    //         case 1:
    //             $quantity = 0;
    //             break;

    //         case 2:
    //             $quantity = 2;
    //             break;

    //         case 3:
    //             $quantity = 5;
    //             break;

    //         default:
    //             $quantity = 0;
    //             break;
    //     }

    //     $product_data['quantity'] = $quantity;
    //     return $product_data;
    // }

    private function filterStock($product_data)
    {
        switch ((int)$product_data['quantity']) {
            case 0:
                $quantity = 0;
                break;

            case 1:
            case 2:
                $quantity = 2;
                break;

            default:
                // Se não é 0, nem 1, nem 2, cai aqui.
                // Logo, cobre o 3 e qualquer número maior.
                $quantity = 5;
                break;
        }

        $product_data['quantity'] = $quantity;
        return $product_data;
    }

    public function filterProductData($product_data)
    {
        foreach ($product_data as &$product) {
            if (is_array($product['features'])) {
                $features = [];
                foreach ($product['features'] as $feature) {
                    $features[] = [
                        'name' => $feature['Categoria'],
                        'value' => $feature['Valor']
                    ];
                }
                $product['features'] = $features;
            }
            $product['category'] = $product['category']['Valor'];
            $product['sub_category'] = $product['sub_category']['Valor'];
            $product['brand'] = $product['brand']['Valor'];

            $product['wholesale_price'] = $product['unit_price'];
            $product['unit_price'] = $this->filterProductPrice($product);
            $product['unit_price_tax'] = $product['unit_price'];

            $reference = $product['reference'];
            $reference = explode('.', $reference);
            $product['reference'] = end($reference);
            $product = $this->filterStock($product);
        }
        return $product_data;
    }

    public function getProductsFeed($update_timestamp = false, $ignore_cache = true)
    {
        $feed_url = $this->getApiUrl('normal');

        $json = new \FusionStoreBundle\Import\Adapter\JSON($feed_url);

        $json->ignore_cache = $ignore_cache;

        if ($update_timestamp) {
            $json->refreshTimeStamp();
        }

        $json->curl = true;

        $json->setParent('Produtos');
        $json->setMatches([
            'Nome'            => 'name_pt',
            'EAN'             => 'ean13',
            'Referencia'      => 'reference',
            'Preco'           => 'unit_price',
            'Imagem'          => 'images',
            'Descricao'       => 'description_pt',
            'Resumo'          => 'description_short_pt',
            'Marca'           => 'brand',
            'Familia'         => 'category',
            'SubFamilia'      => 'sub_category',
            'Stock'           => 'quantity',
            'Portes'          => 'shipping',
            'PesoBruto'       => 'weight',
            'Caracteristicas' => 'features',
        ], true);

        $_records = $json->getRecords($update_timestamp);

        $filepath = _PS_MODULE_DIR_ . $this->name . '/logs/' . date('d_m_Y-H_i') . '.flog';

        file_put_contents($filepath, $json->req_response);

        $file_attachment['content'] = $json->req_response;
        $file_attachment['name'] = 'records_macorlux.json';
        $file_attachment['mime'] = 'application/json';

        Mail::Send(
            (int)(Configuration::get('PS_LANG_DEFAULT')),
            'newsletter',
            'Macorlux Records',
            array(
                '{firstname}' => '',
                '{lastname}' => '',
                '{message}' => 'Ficheiro gerado pela Macorlux',
            ),
            'geral@hipermercado.pt',
            null,
            Configuration::get('PS_SHOP_EMAIL'),
            Configuration::get('PS_SHOP_NAME'),
            $file_attachment,
            null,
            _PS_MAIL_DIR_,
            true
        );

        return $this->filterProductData($_records);
    }

    public function provideInternalFeed()
    {
        $feed_url = $this->getApiUrl('normal');
        $reader = new FusionStoreBundle\Import\Adapter\JSON($feed_url);
        return $reader->getFeedFromCache();
    }
}
