<?php

namespace FusionStoreBundle\CronJob;

use Context;
use Module;

class Flag
{
    private $flagindicatorfile = null;

    public function __construct( Context $context, $isFeedmerge = false )
    {
        $this->context = $context;
        if($isFeedmerge) {
            $this->flagindicatorfile = _PS_ROOT_DIR_.'/modules/fusion/cron_feedmerge.flag';
        }else{
            $this->flagindicatorfile = _PS_ROOT_DIR_.'/modules/fusion/cron.flag';
        }
        
        return $this;
    }

    public function is_running()
    {
        try {
            $flag = file_get_contents($this->flagindicatorfile);
            return (bool)$flag;
        } catch (\Throwable $th) {
            return false;
        }
        
    }

    public function running()
    {
        file_put_contents($this->flagindicatorfile, '1');
        return $this;
    }

    public function finish()
    {
        file_put_contents($this->flagindicatorfile, '0');
        return $this;
    }
}
