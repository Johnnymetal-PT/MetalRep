<?php

namespace FusionStoreBundle\Module;

interface ProductsApiInterface
{
    public function getProductsFeed();
    public function cronRun();
}
