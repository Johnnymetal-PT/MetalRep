<?php
/**
* NOTICE OF LICENSE
*
* This source file is subject to a commercial license from MigrationPro
* Use, copy, modification or distribution of this source file without written
* license agreement from the MigrationPro is strictly forbidden.
* In order to obtain a license, please contact us: contact@migration-pro.com
*
* INFORMATION SUR LA LICENCE D'UTILISATION
*
* L'utilisation de ce fichier source est soumise a une licence commerciale
* concedee par la societe MigrationPro
* Toute utilisation, reproduction, modification ou distribution du present
* fichier source sans contrat de licence ecrit de la part de la MigrationPro est
* expressement interdite.
* Pour obtenir une licence, veuillez contacter la MigrationPro a l'adresse: contact@migration-pro.com
*
* @author    MigrationPro
* @copyright Copyright (c) 2012-2021 MigrationPro
* @license   Commercial license
* @package   MigrationPro: Prestashop Upgrade and Migrate tool
*/

require_once(dirname(__FILE__).'../../../config/config.inc.php');
require_once(dirname(__FILE__).'../../../init.php');

error_reporting(1);

if (!isset($_SERVER)) {
    $_GET = &$HTTP_GET_VARS;
    $_POST = &$HTTP_POST_VARS;
    $_ENV = &$HTTP_ENV_VARS;
    $_SERVER = &$HTTP_SERVER_VARS;
    $_COOKIE = &$HTTP_COOKIE_VARS;
    $_REQUEST = array_merge($_GET, $_POST, $_COOKIE);
}

define('FUSION_ROOT_BASE_NAME', basename(getcwd()));
define('FUSION_CONNECTOR_BASE_DIR', dirname(__FILE__).DIRECTORY_SEPARATOR);
define('FUSION_STORE_BASE_DIR', dirname(__FILE__) . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR);


class FusionConnector
{
    private $certkey = null;

    function __construct()
    {
        if( file_exists(FUSION_CONNECTOR_BASE_DIR.'.certkey') ){
            $this->certkey = file_get_contents(FUSION_CONNECTOR_BASE_DIR.'.certkey');
        }
        $this->actions = new FusionConnectorActions();
    }

    public function run()
    {
        if( $this->checkCert() ){
            if( isset($_GET['action']) && method_exists($this->actions, '_'.$_GET['action'])){
                $this->actions->{'_'.$_GET['action']}();
                return;
            }
        }else{
            die('Invalid Auth');
        }
        die();
    }

    private function checkCert() {
        if (isset($_GET['cert']) && $_GET['cert'] == $this->certkey) {
            return true;
        } else {
            return false;
        }
    }
}

class FusionConnectorActions
{
    private function response( $data, $data_type = 'plain' )
    {
        switch ($data_type) {
          case 'plain':
            echo serialize($data);
            break;

          case 'base64':
            echo base64_encode(serialize($data));
            break;

          default:
            echo 'Invalid output data';
            break;
        }
    }

    public function _getVersion()
    {
        return $this->response('1.1.1.1', 'base64');
    }
}

$connector = new FusionConnector();
$connector->run();
