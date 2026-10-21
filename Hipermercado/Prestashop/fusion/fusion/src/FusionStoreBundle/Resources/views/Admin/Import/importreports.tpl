<style media="screen">
  .modules-list{
    padding: 15px;
    display: block;
    position: relative;
  }
  .modules-list:after{
    clear: both;
    display: block;
    content: "";
  }
  .modules-list .module{
    padding: 8px;
    border: solid 1px #dbe6e9;
    width: 120px;
    cursor: pointer;
    margin-right: 15px;
    float: left;
    border-radius: 10px;
  }
  .modules-list .module img{
    max-height: 100px;
  }
  #reports-list{
  }

  .report-item{
    border: solid 1px #6b868e;
    padding: 10px 15px;
    margin-bottom: 15px;
    background: #ffffff;
    border-radius: 13px;
  }

  .product-row{
    background: #f1f2f3;
    line-height: 1;
    padding: 8px 11px;
    position: relative;
    margin-bottom: 1px;
    min-height: 45px;
    border-radius: 15px;
  }
  .alert-icons{
    float: right;
    display: block;
  }
  .alert-icons>span{
    padding: 0 9px;
    height: 21px;
    display: block;
    float: left;
    font-size: 15px;
    font-weight: 400;
    text-transform: uppercase;
  }

  .product-row .info-notes, .product-row .info-errors{
    padding: 10px 10px 10px 10px;
    background: #fff;
    border-radius: 10px;
    margin-top: 10px;
    font-weight: 400;
    color: #000;
    line-break: anywhere;
  }
  .product-row .info-notes p, .product-row .info-errors p{
    margin: 0;
    font-size: 13px;
    margin-bottom: 6px;
    line-height: 17px;
  }
  .product-row span.label{
    display: block;
    color: #333;
    font-size: 18px;
    text-align: center;
    margin-bottom: 10px;
    font-weight: 800;
    text-transform: uppercase;
  }

  .product-row .error{}
  .product-row .success{}
  .product-row .need-alert{}
  .product-row .identifier{
    font-size: 12px;
    line-height: 29px;
    height: 29px;
  }
  .report-actions{
    display: block;
    text-align: right;
    height: auto;
    width: 100%;
    margin-bottom: 11px;
  }
  .product-row .actions{
    float: right;
    height: 25px;
    line-height: 25px;
  }
  .bootstrap .new-theme button.btn, .bootstrap .new-theme button.btn{
    height: 25px;
    padding: 5px 15px;
    line-height: 1;
    font-size: 12px;
    color: #6c868e;
    background-color: transparent;
    border-color: #6c868e;
    border: solid 1px #6c868e;
  }
  .bootstrap .new-theme button.btn-danger, .bootstrap .new-theme button.btn-danger{
    color: #fff;
    background-color: #e08f95;
    border-color: #da7b82;
  }

  .report-name{
    padding: 5px;
    font-size: 14px;
    font-weight: 500;
    color: #000;
  }

  .report-content{
    margin-top: 10px;
  }
  .quick-view{
    float: left;
    text-align: left;
    font-size: 13px;
    color: #d9404d;
  }

  .repo-filename{
    font-size: 11px;
    color: #9a9a9a;
    padding-left: 12px;
  }
  .alert-resume-note{
    display: inline-block;
    padding: 0 0 0 15px;
    text-transform: uppercase;
    font-size: 10px;
  }
  .alert-resume-note i{
    width: 10px;
    height: 10px;
  }
  .alert-resume-label{
    font-weight: bold;
  }
  .alert-note-filter{
    background: #f9f9f9;
    margin: 0px 3px;
    padding: 5px 12px;
    border: solid 1px #d4d4d4;
    cursor: pointer;
    border-radius: 11px;
    line-height: 1;
    height: 25px;
    display: inline-block;
  }
</style>


<div class="new-theme">

  <div class="row">
    <div class="col-md-12">
      <div class="card">
        <div class="modules-list">
          {if $total_modules > 0}
            {foreach from=$available_modules item=module}
              <div class="module" view-module="{$module.module_name}">
                <img src="{$module.logo}" alt="{$module.name}">
              </div>
            {/foreach}
          {else}
            <h5 class="">{l s='There are no import modules installed' mod='fusion'}</h5>
          {/if}
        </div>
      </div>
    </div>
  </div>

  {if $total_modules > 0}
    <div class="row">
      <div class="col-md-12">
        <div id="reports-list"></div>
      </div>
    </div>
  {/if}

</div>

{literal}
<script type="text/javascript">

  $(document).on('click', '[view-module]' , function(event) {
      event.preventDefault();
      var module = $(this).attr('view-module');
      (new FusionReq({
          success : ( result ) => {
              $('#reports-list').html(`<div> `+result.html+` </div>`);
          },
          complete : () => { $('#reports-list').removeClass('ajax-loader'); },
          before : () => { $('#reports-list').addClass('ajax-loader'); },
          error : () => { showErrorMessage({/literal}'{l s='Error' mod='fusion'}'{literal}); }
      })).save({
          action : 'getModuleReport',
          module : module
      });
  });

  $(document).on('click', '.report-name.fstab' , function(event) {
      var reportItem = $(this).parents('.report-item');
      reportItem.find('.report-content.fstabc').toggle();
  });

  $(document).on('click', '.report-content .product-row [data-source]' , function(event) {
      var dataSource = $(this).attr('data-source');
      $(this).parents('.product-row').find('[data-target="'+dataSource+'"]').toggle();
  });

  $(document).on('click', '[filter]' , function(event) {
      var filter = $(this).attr('filter');
      $('.product-row').hide();
      $('[alert-filter-'+filter+']').show();
      $('[data-action="clearFilter"]').show();
  });

  $(document).on('click', '[data-action="clearFilter"]' , function(event) {
    $('.product-row').show();
    $('[data-action="clearFilter"]').hide();
  });

  $(document).on('click', '[data-action="deleteReport"]' , function(event) {
      event.preventDefault();
      var module = $(this).attr('data-module');
      var filename = $(this).attr('data-filename');
      (new FusionReq({
          success : ( result ) => {
              $('[report="'+filename+'"]').remove();
          },
          complete : () => { $('#reports-list').removeClass('ajax-loader'); },
          before : () => { $('#reports-list').addClass('ajax-loader'); },
          error : () => { showErrorMessage({/literal}'{l s='Error' mod='fusion'}'{literal}); }
      })).save({
          action : 'deleteReport',
          filename : filename,
          module : module
      });
  });

</script>
{/literal}
