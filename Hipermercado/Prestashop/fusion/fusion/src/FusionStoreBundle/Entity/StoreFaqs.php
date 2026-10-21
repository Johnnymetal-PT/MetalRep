<?php

namespace FusionStoreBundle\Entity;

use ObjectModel;

class StoreFaqs extends ObjectModel
{
    /** @var string Title */
    public $title;

    public $description;

    public $active;

    /**
     * @see ObjectModel::$definition
     */
    public static $definition = array(
        'table'     => 'faqs',
        'primary'   => 'id_faq',
        'multilang' => true,
        'fields' => array(
            'active'            => array('type' => self::TYPE_BOOL, 'validate' => 'isBool'),
            'title'             => array('type' => self::TYPE_STRING, 'lang' => true, 'validate' => 'isCleanHtml', 'size' => 512),
            'description'       => array('type' => self::TYPE_STRING, 'lang' => true, 'validate' => 'isCleanHtml', 'size' => 3999999999999),
        ),
    );

    public function add($autoDate = true, $nullValues = false)
    {
        $return = parent::add($autoDate, true);
        return $return;
    }

    public function update($nullValues = false)
    {
        $this->clearCache();
        return parent::update($nullValues);
    }

    public function delete()
    {
        $return = parent::delete();
        return $return;
    }

}
