<?php

namespace FusionStoreBundle\Hooks;

use FusionStoreBundle\Entity\FusionSync;
use FusionStoreBundle\MediaPlugins;
use Product;
use Hook;
use Module;

class FusionBundleHooks extends HookRender
{

    public function __construct( $module, $context = null )
    {
        parent::__construct($module, $context);
        return $this;
    }

    public function DisplayAdminAfterHeader(array $params = [])
    {
        return '<div id="fusion-loader"><div class="-pulsing-1"></div></div>';
    }

    public function DisplayAdminProductsOptionsStepTop(array $params = [])
    {
        $template_file = 'admin_product_options_step_top.tpl';

        #$id_product = $params['idproduct'];

        #if (!$this->module->isCached($this->getTemplate($template_file), $this->getCacheId($id_product.$template_file) )) {
        #    $product_rating = \FusionStoreBundle\Entity\ProductRating::getStarRatingByProductID($id_product);
        #    $this->context->smarty->assign($product_rating);
        #}

        #return $this->module->fetch( $this->getTemplate($template_file) );

        return '';
    }

    public function DisplayAdminOrderTabContent(array $params = [])
    {
        $template_file = 'order_tab_content.tpl';

        $this->context->smarty->assign([
            'fusion_tab_contents'          => Hook::exec('fusionDisplayAdminOrderTabContent')
        ]);

        return $this->module->fetch( $this->getTemplate($template_file) );
    }

    public function DisplayAdminOrderTabLink(array $params = [])
    {
        $template_file = 'order_tab_link.tpl';

        $this->context->smarty->assign([
            'fusion_tab_links'             => Hook::exec('fusionDisplayAdminOrderTabLink')
        ]);

        return $this->module->fetch( $this->getTemplate($template_file) );

    }

    public function DisplayAdminProductsMainStepLeftColumnMiddle(array $params = [])
    {
        $FusionModule = new \FusionStoreBundle\Module\AdminModule($this->module);
        if( !$FusionModule->getEntity('FusionSync') ){
            return '';
        }

        $template_file = 'admin_products_main_step_left_column_middle.tpl';

        $id_product = $params['id_product'];

        $fusion_sync = FusionSync::getByProductID($id_product);

        $feed_file = _PS_ROOT_DIR_.'/modules/fusion/mergedfeed.ffusion';
        $feed_data = [];

        if( file_exists($feed_file) ){
            $feedmerged = json_decode(file_get_contents( $feed_file ), true);
            $p = new Product($id_product);
            if( isset($feedmerged[$p->ean13]) ){
                $feed_data = $feedmerged[$p->ean13];
            }
        }

        if($fusion_sync){
            $this->context->smarty->assign([
                'feed_data'             => json_encode($feed_data, JSON_PRETTY_PRINT),
                'last_update_days'      => $fusion_sync->last_update_days,
                'product_sync_source'   => $fusion_sync->source,
                'product_sync_module'   => $fusion_sync->module,
                'skip_product'          => (bool)$fusion_sync->skip_product,
                'id_sync_entry'         => $fusion_sync->id,
                'fusion_id_product'     => $id_product,
            ]);
        }

        return $this->module->fetch( $this->getTemplate($template_file) );
    }

}
