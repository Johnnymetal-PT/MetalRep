<?php

namespace FusionStoreBundle\Entity;

use Db;
use DbQuery;
use ObjectModel;
use Validate;
use DateTime;

class FusionSync extends ObjectModel
{
    public $id_product;

    public $source;

    public $module;

    public $skip_product;

    public $date_upd = false;

    /**
     * @see ObjectModel::$definition
     */
    public static $definition = array(
        'table' => 'fusion_sync',
        'primary' => 'id_sync_entry',
        'fields' => array(
            'id_product'  => array('type' => self::TYPE_INT, 'validate' => 'isUnsignedId'),
            'source'      => array('type' => self::TYPE_STRING, 'validate' => 'isGenericName'),
            'module'      => array('type' => self::TYPE_STRING, 'validate' => 'isGenericName'),
            'skip_product'=> array('type' => self::TYPE_BOOL, 'validate' => 'isBool'),
            'date_upd'    => array('type' => self::TYPE_DATE, 'validate' => 'isDate'),
        ),
    );

    public function __construct($id = null, $id_lang = null, $id_shop = null, $translator = null)
    {
        parent::__construct($id, $id_lang, $id_shop, $translator);

        if( $this->date_upd != false ){
            $earlier = new DateTime($this->date_upd);
            $later = new DateTime(date('Y-m-d H:i:s'));
            $this->last_update_days = $later->diff($earlier)->format("%a");
        }
    }

    public function add($auto_date = true, $null_values = false)
    {
        $this->skip_product = 0;
        parent::add($auto_date, $null_values);
    }

    public static function getByProductID( $id_product )
    {

        if (!Validate::isUnsignedId($id_product))
            return false;

        $result = Db::getInstance()->getRow('
            SELECT `id_sync_entry` FROM `'._DB_PREFIX_.'fusion_sync`
            WHERE `id_product` = '.(int)$id_product.' ');

        if (!$result) {
            return false;
        }

        return new FusionSync($result['id_sync_entry']);
    }

    public static function install()
    {
        $success = true;

        $sql = array();

        $sql[] = 'CREATE TABLE IF NOT EXISTS `'._DB_PREFIX_.'fusion_sync` (
            `id_sync_entry` int(11) NOT NULL AUTO_INCREMENT,
            `id_product` int(11) NOT NULL,
            `skip_product` int(1) NOT NULL,
            `source` varchar(255) NOT NULL,
            `module` varchar(255) NOT NULL,
            `date_upd` datetime NOT NULL,
            PRIMARY KEY  (`id_sync_entry`)
        ) ENGINE='._MYSQL_ENGINE_.' DEFAULT CHARSET=utf8;';

        foreach ($sql as $query){
            $success &= Db::getInstance()->execute($query);
        }

        return $success;
    }
}
