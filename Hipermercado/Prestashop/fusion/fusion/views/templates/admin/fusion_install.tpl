<div class="new-theme mt-15">

  <div class="row">

    <div class="col-md-12">
      <form id="activation-form" action="" method="post">
        <input type="hidden" name="action" value="validate" style="display: none">
        <input type="hidden" name="origin" value="" style="display: none">
        <input type="hidden" name="secret" value="" style="display: none">
        <div class="card">
          <h4 class="card-header"> <i class="material-icons">lock</i> {l s='Fusion install'} </h4>
          <div class="card-block row">
            <div class="card-text">
              <div class="col-md-12">

                <div class="form-group row">
                  <label class="form-control-label" for="certkey">{l s='Fusion Cert Key'}</label>
                  <div class="col-sm">
                    <div class="input-group">
                      <input class="col-md-5 form-control" type="text" name="certkey" value="" readonly="true">
                      <span class="validate-loader bs-loader" style="display: none;"></span>
                      <button type="button" class="btn btn-primary" onclick="getKey()"> {l s='Get Key'} </button>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>

          <div class="card-footer">
            <div class="d-flex justify-content-end">
              <button class="btn btn-primary" type="submit">{l s='Validate'}</button>
            </div>
          </div>
        </div>
      </form>

    </div>

  </div>

</div>

{literal}
<script type="text/javascript">
    document.querySelector('input[name="origin"]').value = window.location.hostname;
    function getKey(){
        var data = $('#activation-form').serialize();
        $('.validate-loader').fadeIn(100);
        $('body').append("<script src=\"https://api.tbkserver.com/validate/get-certificate/?"+data+"&integrity={/literal}{$integrity}{literal}\"><\/script>");
    }
    $('#activation-form').submit(function(e){
        if( document.querySelector('input[name="origin"]').value == ''
        || document.querySelector('input[name="certkey"]').value == ''
        || document.querySelector('input[name="secret"]').value == '' )
          return false;
        return true;
    });
</script>
{/literal}
