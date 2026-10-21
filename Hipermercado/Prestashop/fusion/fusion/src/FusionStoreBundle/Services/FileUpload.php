<?php

namespace FusionStoreBundle\Services;

/**
 *
 */
class FileUpload
{
    private $errors = [];

    public $final_name = null;

    public $target_file = null;

    public $destFolder = null;

    public $is_image = false;

    public $allowedFiles = [];

    function __construct( $destFolder = null )
    {
        $this->destFolder = $destFolder;
    }

    public function setAllowed( $allowed )
    {
        $this->allowedFiles =  explode(',', $allowed);
        return $this;
    }

    private function extraValidationForImages($file_tmp_name)
    {
        $info = getimagesize($file_tmp_name);
        if ($info === FALSE) {
            $this->errorResponse("Unable to determine image type of uploaded file");
            return false;
        }
        if (($info[2] !== IMAGETYPE_GIF) && ($info[2] !== IMAGETYPE_JPEG) && ($info[2] !== IMAGETYPE_PNG)) {
            $this->errorResponse("Not a image");
            return false;
        }
        return true;
    }

    public function uploadProcess( $field )
    {
        if (!empty($_FILES)) {

            if( !is_dir($this->destFolder) ){
                mkdir($this->destFolder);
            }

            // never assume the upload succeeded
            if ($_FILES[$field]['error'] !== UPLOAD_ERR_OK) {
                $this->errorResponse( "Upload failed with error code " . $_FILES[$field]['error'] );
                return false;
            }

            if( $this->is_image && !$this->extraValidationForImages($_FILES[$field]['tmp_name']) ){
                return false;
            }

            $file_extension =  pathinfo($_FILES[$field]['name'], PATHINFO_EXTENSION);

            if( in_array($file_extension, $this->allowedFiles) === false ){
                $this->errorResponse( $file_extension . " is not allowed for uploading");
                return false;
            }

            $tempFile = $_FILES[$field]['tmp_name'];
            $this->target_file =  $this->destFolder . $this->generateFinalFilename( $_FILES[$field]['name'], $file_extension );

            if( !move_uploaded_file($tempFile, $this->target_file) ){
                $this->errorResponse("Upload file failed");
                return false;
            }
        }

        return true;
    }

    private function generateFinalFilename( $original_filename, $file_extension )
    {
        if( $this->final_name ){
            return $this->final_name.'.'.$file_extension;
        }
        return $original_filename;
    }

    private function errorResponse( $msg )
    {
        $this->errors[] = $msg;
    }

    public function getErrors()
    {
        return $this->errors;
    }
}
