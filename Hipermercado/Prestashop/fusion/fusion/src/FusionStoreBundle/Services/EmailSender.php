<?php

namespace FusionStoreBundle\Services;

use Mail;
use Context;

class EmailSender
{
    public static function sendMail(
        Array $to,
        String $template,
        $email_template_dir,
        Array $params,
        Array $fileAttachment = null
    ){
        $sent = true;
        foreach ($to as $email) {
            $sent &= Mail::sendAlt(
                Context::getContext()->language->id,
                $template,
                $params['subject'],
                $params['templates_var'],
                $email,
                $params['subject'],
                null,
                null,
                $fileAttachment,
                null,
                $email_template_dir
            );
        }
        return $sent;
    }
}
