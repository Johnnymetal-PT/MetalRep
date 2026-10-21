<?php

namespace FusionStoreBundle;

use Country;
use Context;
use Currency;
use Validate;
use Shop;
use Link;

class Locator
{

    protected $default_currency = 1;

    protected $context = null;

    public $locator_changer_url_prefix = '';

    public function __construct( $context = null )
    {
        if( $context === null ){
            $this->context = Context::getContext();
        } else {
            $this->context = $context;
        }

        if(!$this->context->cookie->customer_locate){

            if( !Validate::isLoadedObject($this->context->country) ){
                $this->context->country = new Country(Configuration::get('PS_COUNTRY_DEFAULT'));
            }

            $this->context->cookie->customer_locate = $this->context->country->id;
            $this->context->cookie->write();
        }

        return $this;
    }

    protected function setCurrency( $cookie, $id_currency )
    {
        if ($id_currency) {
            /** @var Currency $currency */
            $currency = Currency::getCurrencyInstance((int) $id_currency);
            if (is_object($currency) && $currency->id && !$currency->deleted && $currency->isAssociatedToShop()) {
                $cookie->id_currency = (int) $currency->id;
            }
        }

        $currency = null;
        if ((int) $cookie->id_currency) {
            $currency = Currency::getCurrencyInstance((int) $cookie->id_currency);
        }
        if (!Validate::isLoadedObject($currency) || (bool) $currency->deleted || !(bool) $currency->active) {
            $currency = Currency::getCurrencyInstance($this->default_currency);
        }

        $cookie->id_currency = (int) $currency->id;

        if ($currency->isAssociatedToShop()) {
            return $currency;
        } else {
          // get currency from context
            $currency = Shop::getEntityIds('currency', Context::getContext()->shop->id, true, true);
            if (isset($currency[0]) && $currency[0]['id_currency']) {
                $cookie->id_currency = $currency[0]['id_currency'];
                return Currency::getCurrencyInstance((int) $cookie->id_currency);
            }
        }

        return $currency;
    }

    public function setCustomerLocate( $id_country )
    {
      	$context = Context::getContext();
      	$country = new Country($id_country, (int) $this->context->cookie->id_lang);
      	$id_currency = $country->id_currency ? (int) $country->id_currency : (int) $this->default_currency;

      	$currency = $this->setCurrency($context->cookie, $id_currency);

      	if(Validate::isLoadedObject($country)){
        		$context->country = $country;
            $context->cookie->id_currency = (int) Currency::getCurrencyInstance($id_currency)->id;
            $context->cookie->iso_code_country = strtoupper($country->iso_code);
      	}

      	$context->cookie->id_lang = 1;
        $context->cookie->write();

        $context->currency = $currency;

      	$this->context->cookie->customer_locate = $id_country;
        $this->context->cookie->write();
    }

    public function getLocationOptions()
    {
        $all_countries = Country::getCountries($this->context->language->id, true);
        $all_currencys = Currency::getCurrencies(false, true);

        $currency_order = array();
        foreach ($all_currencys as $currency) {
            $currency_order[(int)$currency['id']] = $currency;
        }

        $link = new Link();

        $current_locale = false;
        foreach ($all_countries as $key => $countrie) {
            if(isset($currency_order[(int)$countrie['id_currency']])){
                $countrie['currency'] = $currency_order[(int)$countrie['id_currency']];
            }else if(isset($currency_order[$this->default_currency])) {
                $countrie['currency'] = $currency_order[$this->default_currency];
            }
            $countrie['link'] = Context::getContext()->link->getBaseLink().$this->locator_changer_url_prefix.'?locate='.$countrie['id_country'];
            $all_countries[$key] = $countrie;

            if( (int)$this->context->cookie->customer_locate == (int)$countrie['id_country'] ){
                $current_locale = $countrie;
            }
        }

        return array(
            'location_selector' => $all_countries,
            'customer_locate' => $current_locale,
        );
    }
}
