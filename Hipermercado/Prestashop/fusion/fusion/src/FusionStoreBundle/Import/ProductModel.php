<?php

namespace FusionStoreBundle\Import;

use Shop;
use Context;
use Validate;
use Language;

class ProductModel
{
  public $product_data = array();

  private $exclude_fields = array();

  private $product_structure = [
    'name'                => [ 'lang', 'trim' ],
    'description'         => [ 'lang' ],
    'description_short'   => [ 'lang' ],
    'ean13'               => [ 'trim' ],
    'reference'           => [ 'trim' ],
    'brand'               => [ 'trim' ],
    'category'            => [ 'trim' ],
    'sub_category'        => [ 'trim' ],
    'quantity'            => [ 'int' ],
    'qty_min'             => [ 'int' ],
    'images'              => [ 'array', 'trim' ],
    'unit_price'          => [ 'float' ],
    'unit_price_tax'      => [ 'float' ],
    'wholesale_price'     => [ 'float' ],
    'shipping'            => [ 'trim' ],
    'weight'              => [ 'trim', 'float' ],
    'width'               => [ 'trim' ],
    'height'              => [ 'trim' ],
    'depth'               => [ 'trim' ],
    'features'            => [ 'array', 'trim' ],
    'supplier'            => [ 'trim' ],
    'reference_suppliers' => [ 'trim' ],
    'tags'                => [],
    'meta_title'          => [ 'trim' ],
    'meta_keywords'       => [ 'trim' ],
    'meta_description'    => [ 'trim' ],
    'combinations'        => [ 'array' ],
    'attributes_color'    => [],
    'attributes_size'     => [],
    'attributes_material' => [],
    'attributes_other'    => [],
    'info_manual'         => [ 'trim' ],
    'link_rewrite'        => [ 'trim' ],
  ];

  public function __construct( $data_table = null )
  {
      if( $data_table !== null && is_array($data_table) ){
          $keys = [];
          foreach ($data_table as $table_key => $table_value) {
              $keys[] = $table_key;
          }
          $this->HydrateModel($keys, $data_table);
      }
      return $this;
  }

  public function name($value)
  {
    $value = trim($value);
    $this->product_data['name'] = $value;
    return $this;
  }

  public function description($value)
  {
    $value = trim($value);
    $this->product_data['description'] = $value;
    return $this;
  }

  public function description_short($value)
  {
    $value = trim($value);
    $this->product_data['description_short'] = $value;
    return $this;
  }

  public function ean13($value)
  {
    if( !isset($this->product_data['ean13']) ){
      $this->product_data['ean13'] = [];
    }
    if( is_array($value) ){
      foreach ($value as $_value) {
        $this->ean13($_value);
      }
    }else{
      $value = trim($value);
      if( strlen($value) > 13 ){
        $value = '';
      }
      $this->product_data['ean13'][] = $value;
    }
    return $this;
  }

  public function reference($value)
  {
    $value = trim($value);
    $this->product_data['reference'] = $value;
    return $this;
  }

  public function brand($value)
  {
    $this->product_data['brand'] = $value;
    return $this;
  }

  public function category($value)
  {
    if( !isset($this->product_data['category']) ){
      $this->product_data['category'] = [];
    }
    if( is_array($value) ){
      foreach ($value as $_value) {
        $this->category($_value);
      }
    }else{
      $this->product_data['category'][] = trim($value);
    }
    return $this;
  }

  public function sub_category($value)
  {
    if( !isset($this->product_data['sub_category']) ){
      $this->product_data['sub_category'] = [];
    }
    if( is_array($value) ){
      foreach ($value as $_value) {
        $this->sub_category($_value);
      }
    }else{
      $this->product_data['sub_category'][] = trim($value);
    }
    return $this;
  }

  public function quantity($value)
  {
    $this->product_data['quantity'] = $value;
    return $this;
  }

  public function qty_min($value)
  {
    $this->product_data['qty_min'] = $value;
    return $this;
  }

  public function images($value)
  {
    if( !isset($this->product_data['images']) ){
      $this->product_data['images'] = [];
    }
    if( is_array($value) ){
      foreach ($value as $_value) {
        $this->images($_value);
      }
    }else{
      $this->product_data['images'][] = trim($value);
    }
    return $this;
  }

  public function unit_price($value)
  {
    $this->product_data['unit_price'] = $value;
    return $this;
  }

  public function wholesale_price($value)
  {
    $this->product_data['wholesale_price'] = $value;
    return $this;
  }

  public function shipping($value)
  {
    $this->product_data['shipping'] = $value;
    return $this;
  }

  public function weight($value)
  {
    $value = str_replace( ',', '.', $value);
    $this->product_data['weight'] = $value;
    return $this;
  }

  public function width($value)
  {
    $value = str_replace( ',', '.', $value);
    $this->product_data['width'] = $value;
    return $this;
  }

  public function height($value)
  {
    $value = str_replace( ',', '.', $value);
    $this->product_data['height'] = $value;
    return $this;
  }

  public function depth($value)
  {
    $value = str_replace( ',', '.', $value);
    $this->product_data['depth'] = $value;
    return $this;
  }

  public function features($value)
  {
    if( !isset($this->product_data['features']) ){
      $this->product_data['features'] = [];
    }
    if( is_array($value) ){
      foreach ($value as $_value) {
        $this->features($_value);
      }
    }else{
      $this->product_data['features'][] = trim($value);
    }
    return $this;
  }

  public function supplier($value)
  {
    $this->product_data['supplier'] = $value;
    return $this;
  }

  public function reference_suppliers($value)
  {
    $this->product_data['reference_suppliers'] = $value;
    return $this;
  }

  public function tags($value)
  {
    $this->product_data['tags'] = $value;
    return $this;
  }

  public function meta_title($value)
  {
    $this->product_data['meta_title'] = $value;
    return $this;
  }

  public function meta_keywords($value)
  {
    $this->product_data['meta_keywords'] = $value;
    return $this;
  }

  public function meta_description($value)
  {
    $this->product_data['meta_description'] = $value;
    return $this;
  }

  public function attributes_color($value)
  {
    $this->product_data['attributes_color'] = $value;
    return $this;
  }

  public function attributes_size($value)
  {
    $this->product_data['attributes_size'] = $value;
    return $this;
  }

  public function attributes_material($value)
  {
    $this->product_data['attributes_material'] = $value;
    return $this;
  }

  public function attributes_other($value)
  {
    $this->product_data['attributes_other'] = $value;
    return $this;
  }

  public function info_manual($value)
  {
    $this->product_data['info_manual'] = $value;
    return $this;
  }

  public function combinations($value)
  {
    $this->product_data['combinations'] = $value;
    return $this;
  }

  public function get( $prop, $key = false )
  {
    if( $key !== false ){
      if( isset($this->product_data[$prop][$key]) ){
        return $this->product_data[$prop][$key];
      }
    }else{
      if( isset($this->product_data[$prop]) ){
        return $this->product_data[$prop];
      }
    }
    return '';
  }

  public function extra_from_hook( $fields_from_modules, $entry )
  {
    if( $fields_from_modules && is_array($fields_from_modules) && !empty($fields_from_modules) )
    {
      foreach ($fields_from_modules as $fields) {
        foreach ($fields as $field_key => $field_name) {
          $this->product_data[$field_key] = $entry[$field_key];
        }
      }
    }
    return $this;
  }

  private function getLangField( $iso, $fentry, $field )
  {
    if( isset( $fentry[$field.'_'.$iso] ) ){
      $this->exclude_fields[] = $field.'_'.$iso;
      return $fentry[$field.'_'.$iso];
    }else{
      return '';
    }
  }

  private function filter_field( $value, $filter, $by_pass = false )
  {
    if( is_array($value) ){
      foreach ($value as $key => $_value) {
        $value[$key] = $this->filter_field( $_value, $filter, true);
      }
    }else{
      switch ( $filter ) {
        case 'lang':
          if(!$by_pass){
              if(!is_array($value)){
                  $_value = array();
                  foreach ( Language::getIDs(false) as $id_lang ) {
                    $_value[$id_lang] = $value;
                  }
                  $value = $_value;
              }
          }
          break;
        case 'array':
            if(!$by_pass){
                if(!is_array($value)){
                    $value = array($value);
                }
            }
            break;
        case 'trim':
          $value = trim($value);
          break;
        case 'int':
          $value = (int)$value;
          break;
        case 'float':
          $value = str_replace(',','.',$value);
          $value = (float)$value;
          break;
      }
    }
    return $value;
  }

  public function filterModel()
  {
      $this->product_data = $this->preFilter( $this->product_data );
      return $this;
  }

  public function cleanProductName($name)
  {
      $name = str_replace('>', '-', $name);
      $name = str_replace('<', '-', $name);
      return $name;
  }

  private function preFilter( $data )
  {
    foreach ($this->product_structure as $column => $filters) {
      if( isset($this->product_data[$column]) ){
        foreach ( $filters as $filter ) {
          $data[ $column ] = $this->filter_field( $data[ $column ], $filter );
        }
      }
    }
    return $data;
  }

  public function HydrateModel( $table_columns, $product_entry, $hook_matches = null )
  {
    $langs = array();
    foreach ( Language::getIDs(false) as $id_lang ) {
      $langs[$id_lang] = Language::getIsoById($id_lang);
    }

    // Reference and barcodes funcParams
    $this->product_data['ean13'] = explode(',', $product_entry['ean13']);
    $this->product_data['reference'] = $product_entry['reference'];

    if( isset($product_entry['categorys']) && $product_entry['categorys'] != '' ){
      $main_cat_tree = explode(',', $product_entry['categorys']);

      if(!empty($main_cat_tree)){
        foreach ($main_cat_tree as $key => $value) {
          if($value == '' || $value == false){
            unset($main_cat_tree[$key]);
          }else{
            $value = explode('>', $value);
            foreach ($value as $_key => $_value) {
              if($_value == '' || $_value == false){
                unset($_value[$_key]);
              }
            }
          }
        }
        $this->product_data['categorys'] = $main_cat_tree;
      }
    }

    // Get lang fields
    foreach ( $langs as $id_lang => $iso ) {
      $this->product_data['name'][$id_lang] = $this->cleanProductName($this->getLangField( $iso, $product_entry, 'name' ));
      $this->product_data['description'][$id_lang] = $this->getLangField( $iso, $product_entry, 'description' );
      $this->product_data['description_short'][$id_lang] = $this->getLangField( $iso, $product_entry, 'description_short' );

      $this->product_data['meta_description'][$id_lang] = $this->getLangField( $iso, $product_entry, 'meta_description' );
      $this->product_data['meta_keywords'][$id_lang] = $this->getLangField( $iso, $product_entry, 'meta_keywords' );
      $this->product_data['meta_title'][$id_lang] = $this->getLangField( $iso, $product_entry, 'meta_title' );

      $this->product_data['link_rewrite'][$id_lang] = $this->getLangField( $iso, $product_entry, 'link_rewrite' );
    }

    // visibility
    $this->product_data['visibility'] = 'both';

    // manufacturer
    $this->product_data['manufacturer_name'] = @$product_entry['brand'];
    $this->product_data['supplier'] = @$product_entry['supplier'];

    // product shipping data
    $this->product_data['width'] = @$product_entry['width'];
    $this->product_data['height'] = @$product_entry['height'];
    $this->product_data['depth'] = @$product_entry['depth'];
    $this->product_data['weight'] = @$product_entry['weight'];

    // price params
    $this->product_data['unit_price'] = @$product_entry['unit_price'];
    $this->product_data['unit_price_tax'] = @$product_entry['unit_price_tax'];
    $this->product_data['tax_rules_group'] = @$product_entry['tax_rules_group'];

    foreach ($table_columns as $column) {
      if( !isset($this->product_data[$column]) && !in_array($column, $this->exclude_fields) )
        $this->product_data[$column] = $product_entry[ $column ];
    }

    $this->extra_from_hook( $hook_matches, $product_entry );
    $this->product_data = $this->preFilter( $this->product_data );

    return $this;
  }

}
