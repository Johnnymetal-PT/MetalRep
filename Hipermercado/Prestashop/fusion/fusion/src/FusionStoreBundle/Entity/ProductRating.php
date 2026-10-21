<?php

namespace FusionStoreBundle\Entity;

use Db;
use DbQuery;
use ObjectModel;
use Validate;

class ProductRating extends ObjectModel
{
    /**
     * @see ObjectModel::$definition
     */
    public static $definition = array(
        'table' => 'rating_product',
        'primary' => 'id_rating_product',
        'multilang' => true,
        'fields' => array(
            'id_product'  => array('type' => self::TYPE_INT, 'validate' => 'isUnsignedId'),
            'id_customer' => array('type' => self::TYPE_INT, 'validate' => 'isUnsignedId'),
            'id_guest'    => array('type' => self::TYPE_INT, 'validate' => 'isUnsignedId'),
            'rating'      => array('type' => self::TYPE_INT, 'validate' => 'isUnsignedId'),
            'date_add'    => array('type' => self::TYPE_DATE, 'validate' => 'isDate'),

            /* Lang fields */
            'comment' => array('type' => self::TYPE_STRING, 'lang' => true, 'required' => false, 'size' => 500),
        ),
    );

    public static function getStarRatingByProductID( $id_product )
    {

        if (!Validate::isUnsignedId($id_product))
            return false;

        $avgrating_sql = 'SELECT AVG(`rating`) as avgrating
        FROM `' . _DB_PREFIX_ . 'rating_product`
        WHERE `id_product` = ' . (int) $id_product;

        $count_sql = 'SELECT COUNT(*) as totalcount
        FROM `' . _DB_PREFIX_ . 'rating_product`
        WHERE `id_product` = ' . (int) $id_product;

        $rating_res = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($avgrating_sql);
        $count_res = Db::getInstance(_PS_USE_SQL_SLAVE_)->executeS($count_sql);

        if( $rating_res && isset($rating_res[0]) ){
            return [
                'ratings' => true,
                'averageTotal' => $rating_res[0]['avgrating'],
                'interactionsTotal' => $count_res[0]['totalcount']
            ];
        }

        return [];
    }

    public static function getRatingByProductID( $id_product )
    {
        $star_rating = self::getStarRatingByProductID( $id_product );
        return array_merge($star_rating);
    }

    public static function install()
    {
        $success = true;

        $sql = array();

        $sql[] = 'CREATE TABLE IF NOT EXISTS `'._DB_PREFIX_.'rating_product` (
            `id_rating_product` int(11) NOT NULL AUTO_INCREMENT,
            `id_product` int(11) NOT NULL,
            `id_customer` int(11) NOT NULL,
            `id_guest` int(11) NOT NULL,
            `rating` int(1) NOT NULL,
            `date_add` datetime NOT NULL,
            PRIMARY KEY  (`id_rating_product`)
        ) ENGINE='._MYSQL_ENGINE_.' DEFAULT CHARSET=utf8;';

        $sql[] = 'CREATE TABLE IF NOT EXISTS `'._DB_PREFIX_.'rating_product_lang` (
            `id_rating_product` int(11) NOT NULL AUTO_INCREMENT,
            `id_lang` int(11) NOT NULL,
            `comment` text,
            PRIMARY KEY  (`id_rating_product`, `id_lang`)
        ) ENGINE='._MYSQL_ENGINE_.' DEFAULT CHARSET=utf8;';

        foreach ($sql as $query){
            $success &= Db::getInstance()->execute($query);
        }

        return $success;
    }
}
