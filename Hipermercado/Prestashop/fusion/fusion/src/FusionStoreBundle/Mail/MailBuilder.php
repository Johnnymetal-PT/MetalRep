<?php

namespace FusionStoreBundle\Mail;

use Context;
use Language;
use Configuration;
use Tools;
use Link;

class MailBuilder
{
    private $main_vars = [];

    private $extra_vars = [];

    public function __construct( $idLang, String $title, $idShop = null)
    {
        if (!$idShop) {
            $idShop = Context::getContext()->shop->id;
        }

        if ((Context::getContext()->link instanceof Link) === false) {
            Context::getContext()->link = new Link();
        }

        $this->iso_folder = Language::getIsoById((int) $idLang);

        $configuration = Configuration::getMultiple(
            [
                'PS_SHOP_NAME',
            ],
            null,
            null,
            $idShop
        );

        $this->main_vars['title'] = $title;
        $this->main_vars['shop_name'] = Tools::safeOutput($configuration['PS_SHOP_NAME']);
        $this->main_vars['shop_url'] = Context::getContext()->link->getPageLink(
            'index', true, $idLang,   null, false, $idShop
        );
    }

    public function assign( $var, $value = false )
    {
        if( is_array($var) ){
            foreach ($var as $_key => $_value) {
                $this->assign( $_key, $_value);
            }
        }else{
            $this->extra_vars[$var] = $value;
        }
        return $this;
    }

    public function build( $path = null )
    {
        if( $path == null ){
            $path = _PS_MAIL_DIR_;
        }

        Context::getContext()->smarty->assign($this->main_vars);

        return array_merge(
            $this->extra_vars,
            [
                '{HEADER}' => Context::getContext()->smarty->fetch( $path . $this->iso_folder . '/_common/header.tpl' ),
                '{FOOTER}' => Context::getContext()->smarty->fetch( $path . $this->iso_folder . '/_common/footer.tpl' )
            ]
        );
    }
}
