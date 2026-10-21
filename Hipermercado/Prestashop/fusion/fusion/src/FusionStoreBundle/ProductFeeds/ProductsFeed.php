<?php

namespace FusionStoreBundle\ProductFeeds;

use Context;
use Product;
use Category;
use Validate;

class ProductsFeed
{
    private $token = 'a17ga346wq';

    protected $context;

    protected $id_lang;

    protected $feed_data;

    protected $feed_name;
    protected $feed_link;
    protected $feed_description;

    public $content;

    public function __construct( $feed_name, $feed_token )
    {
        if( $this->token != $feed_token ){
            return false;
        }

        $this->context = Context::getContext();

        $this->id_lang = 1;
        $this->feed_name = $feed_name;
        $this->feed_link = '';
        $this->feed_description = '';

        $products = Product::getSimpleProducts(
            $this->id_lang
        );

        $this->feed_data = $products;
        return $this;
    }

    public function feed()
    {
        return $this->feed_data;
    }

    protected function getCategories( $product )
    {
        $cat = new Category($product->id_category_default, $this->id_lang);
        if( Validate::isLoadedObject($cat) ){
            return $cat->name;
        }
        return '';
    }
}
