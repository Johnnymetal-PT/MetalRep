<?php

namespace FusionStoreBundle\Helper;

use Context;
use Module;
use Tools;

class Dropzone
{

  private $upload_handler = false;

  private $upload_folder = false;

  private $only_images = false;

  private $allowed_ext = false;

  private $max_file_size = 10;

  private $timeout = 120000;

  private $complete_callback = false;

  function __construct( Context $context, Module $module = null)
  {
    return $this;
  }

  public function onlyImages( Bool $only_images )
  {
    $this->only_images = $only_images;
    return $this;
  }

  public function setAllowed( Array $allowed_ext )
  {
    $this->allowed_ext = $allowed_ext;
    return $this;
  }

  public function setUploadFolder( String $upload_folder )
  {
    $this->upload_folder = $upload_folder;
    return $this;
  }

  public function setUploadHandler( String $upload_handler )
  {
    $this->upload_handler = $upload_handler;
    return $this;
  }

  public function setMaxFileSize( Int $max_file_size )
  {
    $this->max_file_size = $max_file_size;
    return $this;
  }

  public function setCompleteCallback($complete_callback)
  {
    $this->complete_callback = $complete_callback;
    return $this;
  }

  public function uploadHandlerProcess( $rename_file = false )
  {
    if (!empty($_FILES)) {

      // never assume the upload succeeded
      if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) {
        $this->errorResponse( "Upload failed with error code " . $_FILES['file']['error'] );
      }
      if( $this->only_images ){

        $info = getimagesize($_FILES['file']['tmp_name']);
        if ($info === FALSE) {
          $this->errorResponse("Unable to determine image type of uploaded file");
        }

        if (($info[2] !== IMAGETYPE_GIF) && ($info[2] !== IMAGETYPE_JPEG) && ($info[2] !== IMAGETYPE_PNG)) {
          $this->errorResponse("Not a gif/jpeg/png");
        }
      }else{
        $name = $_FILES["file"]["name"];
        $ext = end((explode(".", $name))); # extra () to prevent notice

        if ( !in_array($ext, $this->allowed_ext) ) {
          $this->errorResponse("Not allowed file. Allowed: " . implode(',', $this->allowed_ext) );
        }
      }

      $tempFile = $_FILES['file']['tmp_name'];

      var_dump($rename_file);die();
      if($rename_file!==false && function_exists($rename_file)){
          $targetFile = $rename_file($this->upload_folder, $_FILES['file']['name']);
      }else{
        $targetFile =  $this->upload_folder . $_FILES['file']['name'];
      }

      if( !move_uploaded_file($tempFile, $targetFile) ){
        $this->errorResponse("Move file failed");
      }
      ob_end_clean();
      header('Content-Type: application/json');
      echo Tools::jsonEncode(['status' => 'OK']);
      die();
    }
    return true;
  }

  public function getJS()
  {
    return [
      'https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.8.0/min/dropzone.min.js'
    ];
  }

  public function getCSS()
  {
    return [
      'https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.8.0/dropzone.min.css',
      'https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.8.0/basic.min.css'
    ];
  }

  public function render()
  {
    $dropz_id = 'DrOpZoNe_'.time();
    return $this->html($dropz_id).
    $this->javascript($dropz_id);
  }

  private function html( $dropz_id )
  {
    return '
      <div class="dropzone-container"">
         <form action="'.$this->upload_handler.'" class="dropzone needsclick" id="'.$dropz_id.'">
            <div class="dz-message needsclick">
               <button type="button" class="dz-button">Drop files here or click to upload.</button><br />
            </div>
         </form>
      </div>
    ';
  }

  private function javascript( $dropz_id )
  {
    return '
      <script type="text/javascript">
        var _'.$dropz_id.'_Oj = new Dropzone("#'.$dropz_id.'",{
          maxFilesize: '.$this->max_file_size.',
          retryChunks: true,
          timeout: '.$this->timeout.',
        });
        ' . ($this->complete_callback? '
          _'.$dropz_id.'_Oj.on("complete", function(file) {
            _'.$dropz_id.'_Oj.removeFile(file);
            '.$this->complete_callback.'(file);
          });
        ':'') . '
      </script>
    ';
  }

  protected function errorResponse($msg)
  {
    header('HTTP/1.1 400 Bad request');
    die($msg);
  }
}
