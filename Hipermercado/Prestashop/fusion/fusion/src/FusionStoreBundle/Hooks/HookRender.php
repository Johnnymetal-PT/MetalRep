<?php

namespace FusionStoreBundle\Hooks;

use FusionStoreBundle\Widgets\WidgetRender;

class HookRender extends WidgetRender
{
    protected function getTemplate($template)
    {
        return 'module:fusion/src/FusionStoreBundle/Resources/views/'.$this->getViewContext().'/Hook/'.$template;
    }
}
