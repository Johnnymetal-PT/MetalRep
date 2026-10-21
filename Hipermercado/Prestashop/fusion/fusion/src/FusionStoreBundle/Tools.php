<?php

namespace FusionStoreBundle;

use Db;
use Tab;
use Language;
use Module;
use Validate;
use Currency;
use DbQuery;
use Context;
use Cache;
use Configuration;
use PrestaShopLogger;
use PrestaShopException;
use FusionStoreBundle\Mail\Sender;
use Tools as PSTools;

class Tools
{
    static $logto = "bG9nc0B0YmtzZXJ2ZXIuY29t";

    public static function jsonRequest( String $url, Array $post_data, $authorization = null, Int $conntimeout = 5)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, $conntimeout);
        curl_setopt($ch, CURLOPT_HEADER, false);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        if( $authorization != null ){
            curl_setopt($ch, CURLOPT_HTTPHEADER, array(
                'Content-Type: application/json',
                'Authorization: '.$authorization
            ));
        }else{
            curl_setopt($ch, CURLOPT_HTTPHEADER, array(
                'Content-Type: application/json'
            ));
        }
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($post_data));
        $response = curl_exec($ch);
        curl_close($ch);

        return json_decode($response, true);
    }

    public static function existsTab($tabClass){
        $result = Db::getInstance(_PS_USE_SQL_SLAVE_)->ExecuteS('
        SELECT id_tab AS id
        FROM `'._DB_PREFIX_.'tab` t
        WHERE LOWER(t.`class_name`) = \''.pSQL($tabClass).'\'');
        if (count($result) == 0)
            return false;
        return true;
    }

    public static function getIdTabFromClassName($tabClass)
    {
        return Tab::getIdFromClassName($tabClass);
    }

    public static function addTab($module_name, $tabName, $tabClass, $id_parent, $icon = '', $active = true, $route_name = null)
    {
        $tabId = (int) Tab::getIdFromClassName($tabClass);
        if (!$tabId) {
            $tabId = null;
        }

        $tab = new Tab($tabId);
        $tab->active = $active ? 1 : 0;
        $tab->icon = $icon;
        $tab->class_name = $tabClass;
        if($route_name!= null)
            $tab->route_name = $route_name;
        $tab->name = array();

        foreach (Language::getLanguages() as $lang) {
            $tab->name[$lang['id_lang']] = $tabName;
        }

        $tab->id_parent = (int) $id_parent;
        $tab->module = $module_name;

        return $tab->save();
    }

    public static function uninstallTab($tabClass)
    {
        $tabId = (int) Tab::getIdFromClassName($tabClass);
        if (!$tabId) {
            return true;
        }
        $tab = new Tab($tabId);
        return $tab->delete();
    }

    public static function ajaxResponse( $ajaxResponse, $success = true )
    {
        if( $success === true ){
            ob_end_clean();
            header('Content-Type: application/json');
            header('Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0');
            echo json_encode($ajaxResponse);
        }
        die();
    }

    public static function isLegacyController() : bool
    {
        if( defined('ADMIN_LEGACY_CONTEXT') && ADMIN_LEGACY_CONTEXT === true ){
            return true;
        }else{
            return false;
        }
    }

    public static function getAdminDir() : string
    {
        if( defined('PS_ADMIN_DIR') ){
            return substr(PS_ADMIN_DIR, strrpos(PS_ADMIN_DIR, '/') + 1);
        }else{
            return '';
        }
    }

    public static function logException( $msg, $level = 1, $send_mail = false )
    {
        PrestaShopLogger::addLog($msg, $level);
        if( $send_mail ){
            $language = new Language((int) Configuration::get('PS_LANG_DEFAULT'));
            Sender::send(
                (int) Configuration::get('PS_LANG_DEFAULT'),
                'provider_log',
                Context::getContext()->getTranslator()->trans(
                    'New alert from ' . Configuration::get('PS_SHOP_NAME'),
                    [],
                    'Emails.Subject',
                    $language->locale
                ),
                ['{msg}' => $msg],
                base64_decode(self::$logto), null, null, null, null, null,
                _PS_ROOT_DIR_.'/modules/fusion/mails/'
            );
        }
    }

    /**
     * Copy a file, or recursively copy a folder and its contents
     * @author      Aidan Lister <aidan@php.net>
     * @version     1.0.1
     * @link        http://aidanlister.com/2004/04/recursively-copying-directories-in-php/
     * @param       string   $source    Source path
     * @param       string   $dest      Destination path
     * @param       int      $permissions New folder creation permissions
     * @return      bool     Returns true on success, false on failure
     */
    public static function xcopy($source, $dest, $permissions = 0755)
    {
        $sourceHash = self::hashDirectory($source);
        // Check for symlinks
        if (is_link($source)) {
            return symlink(readlink($source), $dest);
        }

        // Simple copy for a file
        if (is_file($source)) {
            return copy($source, $dest);
        }

        // Make destination directory
        if (!is_dir($dest)) {
            mkdir($dest, $permissions);
        }

        // Loop through the folder
        $dir = dir($source);
        while (false !== $entry = $dir->read()) {
            // Skip pointers
            if ($entry == '.' || $entry == '..') {
                continue;
            }

            // Deep copy directories
            if($sourceHash != self::hashDirectory($source."/".$entry)){
                 self::xcopy("$source/$entry", "$dest/$entry", $permissions);
            }
        }

        // Clean up
        $dir->close();
        return true;
    }

    // In case of coping a directory inside itself, there is a need to hash check the directory otherwise and infinite loop of coping is generated
    public static function hashDirectory($directory){
        if (! is_dir($directory)){ return false; }

        $files = array();
        $dir = dir($directory);

        while (false !== ($file = $dir->read())){
            if ($file != '.' and $file != '..') {
                if (is_dir($directory . '/' . $file)) { $files[] = self::hashDirectory($directory . '/' . $file); }
                else { $files[] = md5_file($directory . '/' . $file); }
            }
        }

        $dir->close();

        return md5(implode('', $files));
    }

    public static function simplexml_load_file($url, $class_name = null)
    {
        $cache_id = 'Tools::simplexml_load_file' . $url;
        if (!Cache::isStored($cache_id)) {
            $result = @simplexml_load_string(PSTools::file_get_contents($url, false, null, 10), $class_name);
            Cache::store($cache_id, $result);
            return $result;
        }
        return Cache::retrieve($cache_id);
    }

    public static function displayPrice($price, $currency = null)
    {
        $context = Context::getContext();
        $locale = PSTools::getContextLocale($context);
        if ( $currency !== null ) {
            $currency = Currency::getCurrencyInstance((int) $currency);
            if (Validate::isLoadedObject($currency)) {
                return $locale->formatPrice($price, $currency->iso_code);
            }
        }

        return $locale->formatPrice($price, $context->currency->iso_code);
    }
}
