<?php
/**
 * Copyright since 2007 PrestaShop SA and Contributors
 * PrestaShop is an International Registered Trademark & Property of PrestaShop SA
 *
 * NOTICE OF LICENSE
 *
 * This source file is subject to the Open Software License (OSL 3.0)
 * that is bundled with this package in the file LICENSE.md.
 * It is also available through the world-wide-web at this URL:
 * https://opensource.org/licenses/OSL-3.0
 * If you did not receive a copy of the license and are unable to
 * obtain it through the world-wide-web, please send an email
 * to license@prestashop.com so we can send you a copy immediately.
 *
 * DISCLAIMER
 *
 * Do not edit or add to this file if you wish to upgrade PrestaShop to newer
 * versions in the future. If you wish to customize PrestaShop for your
 * needs please refer to https://devdocs.prestashop.com/ for more information.
 *
 * @author    PrestaShop SA and Contributors <contact@prestashop.com>
 * @copyright Since 2007 PrestaShop SA and Contributors
 * @license   https://opensource.org/licenses/OSL-3.0 Open Software License (OSL 3.0)
 */

namespace FusionStoreBundle;

use Tools;
use Shop;
use Attribute;
use AttributeGroup;
use Configuration;
use AdminImportController;
use AdminImportControllerCore;

@ini_set('max_execution_time', 0);
/* No max line limit since the lines can be more than 4096. Performance impact is not significant. */
define('MAX_LINE_SIZE', 0);

/* Used for validatefields diying without user friendly error or not */
define('UNFRIENDLY_ERROR', false);

/* this value set the number of columns visible on each page */
define('MAX_COLUMNS', 6);

/* correct Mac error on eof */
@ini_set('auto_detect_line_endings', '1');

class LegacyImportController extends AdminImportController
{
    public $csv_file = null;

    public $separator = ';';
    public $convert = false;
    public $multiple_value_separator  = ',';

    public function __construct()
    {
        parent::__construct();
    }

    protected function openCsvFile($offset = false)
    {
        $file = $this->excelToCsvFile( $this->csv_file );
        $handle = false;
        if (is_file($file) && is_readable($file)) {
            if (!mb_check_encoding(file_get_contents($file), 'UTF-8')) {
                $this->convert = true;
            }
            $handle = fopen($file, 'rb');
        }

        if (!$handle) {
            return null; // error case
        }

        AdminImportController::rewindBomAware($handle);

        $toSkip = (int) Tools::getValue('skip');
        if ($offset && $offset > 0) {
            $toSkip += $offset;
        }
        for ($i = 0; $i < $toSkip; ++$i) {
            $line = fgetcsv($handle, MAX_LINE_SIZE, $this->separator);
            if ($line === false) {
                return false; // reached end of file
            }
        }

        return $handle;
    }

    public function attributeImport($offset = false, $limit = false, &$crossStepsVariables = false, $validateOnly = false)
    {
        $default_language = Configuration::get('PS_LANG_DEFAULT');

        $groups = [];
        if ($crossStepsVariables !== false && array_key_exists('groups', $crossStepsVariables)) {
            $groups = $crossStepsVariables['groups'];
        }
        foreach (AttributeGroup::getAttributesGroups($default_language) as $group) {
            $groups[$group['name']] = (int) $group['id_attribute_group'];
        }

        $attributes = [];
        if ($crossStepsVariables !== false && array_key_exists('attributes', $crossStepsVariables)) {
            $attributes = $crossStepsVariables['attributes'];
        }
        foreach (Attribute::getAttributes($default_language) as $attribute) {
            $attributes[$attribute['attribute_group'] . '_' . $attribute['name']] = (int) $attribute['id_attribute'];
        }

        $this->receiveTab();

        $handle = $this->openCsvFile($offset);
        if (!$handle) {
            return false;
        }

        AdminImportController::setLocale();

        $regenerate = Tools::getValue('regenerate');
        $shop_is_feature_active = Shop::isFeatureActive();

        $line_count = 0;

        for ($current_line = 0; ($line = fgetcsv($handle, MAX_LINE_SIZE, $this->separator)) && (!$limit || $current_line < $limit); ++$current_line) {
            ++$line_count;

            if ($this->convert) {
                $line = $this->utf8EncodeArray($line);
            }

            if (count($line) == 1 && $line[0] == null) {
                $this->warnings[] = $this->trans('There is an empty row in the file that won\'t be imported.', [], 'Admin.Advparameters.Notification');

                continue;
            }

            $info = AdminImportController::getMaskedRow($line);
            $info = array_map('trim', $info);

            $this->attributeImportOne(
                $info,
                $default_language,
                $groups, // by ref
                $attributes, // by ref
                $regenerate,
                $shop_is_feature_active,
                $validateOnly
            );
        }
        $this->closeCsvFile($handle);

        if ($crossStepsVariables !== false) {
            $crossStepsVariables['groups'] = $groups;
            $crossStepsVariables['attributes'] = $attributes;
        }

        return $line_count;
    }

}
