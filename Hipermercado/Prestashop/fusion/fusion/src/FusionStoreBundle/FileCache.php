<?php

namespace FusionStoreBundle\Cache;

class FileCache
{

    # Cache life time
    private $expireCache = 18000; # 5 horas

    private $file = null;

    private $cache_dir = null;

    public function __construct( $file, $expireCache = false, $alt_cache_dir = false )
    {
        if( $expireCache !== false )
            $this->expireCache = $expireCache;

        if( $alt_cache_dir !== false ){
            $cache_dir = $alt_cache_dir;
        }else{
            $cache_dir = _PS_CACHE_DIR_ . 'fusion' . DIRECTORY_SEPARATOR;
        }

        if( !is_dir($cache_dir) ){
            mkdir($cache_dir);
        }

        $this->file = $cache_dir . $file;

        return $this;
    }

    public function refreshTimeStamp()
    {
        if( file_exists($this->file) ){
            $this->putOnCache( file_get_contents($this->file) );
        }
        return $this;
    }

    public function isOnCache( $return_file_path = false )
    {
        if( file_exists($this->file) ){
            $timestamp = filemtime($this->file);
            if( ($this->expireCache + $timestamp) >= time() ){
                if($return_file_path)
                    return $this->file;
                else
                    return file_get_contents($this->file);
            }else{
                @unlink($this->file);
            }
        }
        return false;
    }

    public function putOnCache( $content )
    {
        if( $content == "" || !$content )
            return false;
        return file_put_contents($this->file, $content);
    }

    public static function getCacheId( $params )
    {
        $CacheID = md5($params).'.fcache';
        return $CacheID;
    }
}
