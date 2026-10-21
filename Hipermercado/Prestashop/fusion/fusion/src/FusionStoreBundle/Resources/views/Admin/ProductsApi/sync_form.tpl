<style media="screen">
  .import-btn.list-toolbar-btn{
    display: block;
    padding: 1px;
    position: relative;
    height: 30px;
    line-height: 30px;
    color: #363a40 !important;
  }
  .detail-row{
    display: none;
    position: fixed;
    z-index: 99999;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #f9f9f9;
    padding: 30px;
  }
  button.btn.btn-open-detail{
    padding: 3px 6px !important;
    background: #fff;
    border: none;
    border-radius: 0;
    color: #333;
    font-size: 20px;
    line-height: 1;
  }
  button.btn.close-detail{
    padding: 3px 6px !important;
    border: none;
    border-radius: 0;
    color: #fff;
    font-size: 20px;
    line-height: 1;
    float: right;
  }
  button.btn.btn-open-detail i{
    font-size: 20px;
  }
</style>


<div class="panel" id="fieldset_0">
   <div class="panel-heading">
      <i class="icon-cogs"></i> {l s='Import'} ({$total_products}) In stock ({$total_products_in_stock})

      <span class="panel-heading-action">
        <a class="list-toolbar-btn import-btn" href="">
           Importar <i class="icon-download"></i>
        </a>
      </span>

   </div>
   <div class="form-wrapper">

     <table class="table table-responsive">
       <tr>
         <th>--</th>
         {foreach from=$table_header item=colname}
           {if is_array($colname) && isset($colname.collabel)}
              <th>{$colname.collabel}</th>
           {else}
             <th>{$colname}</th>
           {/if}
         {/foreach}
         <th>--</th>
       </tr>

       {foreach from=$api_feed item=row key=key}
       {if !$row.hide}
         <tr product-line data-id="{$key}">
           <td width="30px">{if isset($row.noimg)} <img width="20px" src="data:image/png;base64,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" alt=""> {/if}</td>

           {foreach from=$table_header item=colname key=colkey}
             <td>
               {if is_array($colname)}
                  <table class="table">
                    <tr>
                      {foreach from=$colname item=colname_extra key=colkey_extra}
                        {if $colkey_extra != 'collabel' && is_array($row[$colkey])}
                          <th>{$colname_extra}</th>
                        {/if}
                      {/foreach}
                    </tr>
                    {foreach from=$row[$colkey] item=iitem}
                      <tr>
                      {foreach from=$colname item=colname_extra key=colkey_extra}
                        {if $colkey_extra != 'collabel' && is_array($row[$colkey])}
                          <td>{$iitem[$colkey_extra]}</td>
                        {/if}
                      {/foreach}
                      </tr>
                    {/foreach}
                  </table>
               {else}
                {if isset($row[$colkey])}
                  {if is_array($row[$colkey])}
                    {$row[$colkey]|@var_dump}
                  {else}
                    {$row[$colkey]}
                  {/if}
                {/if}
               {/if}
             </td>
           {/foreach}

           <td> <button class="btn btn-sm btn-open-detail" type="button" view-detail="{$key}" name="button"><i class="material-icons">search</i></button> </td>

         </tr>
       {/if}
       {/foreach}


     </table>
   </div>
</div>

{foreach from=$api_feed item=row key=key }
  <div class="detail-row" detail="{$key}">
    <button type="button" class="close-detail  btn btn-danger" closedet="{$key}" name="button"><i class="material-icons">close</i></button>
    <table class="table table-responsive">
      {foreach from=$row item=data key=index }
         <tr>
           <td>{$index}</td>
           <td>
              {if is_array($data)}
                {$data|@var_dump}
              {else}
                {$data}
              {/if}
           </td>
         </tr>
      {/foreach}
    </table>
  </div>
{/foreach}


<div id="options_form">
  <div class="row">

      <div class="col-md-12">
        <p class="title">{l s='If product exists, ignore:' mod='fusion'}</p>
      </div>

      <div class="col-md-6">
         <div class="form-group fswitch-group">
            <span class="label">{l s='Name' mod='fusion'}</span>
            <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="product_name"></div>
         </div>
         <div class="form-group fswitch-group">
            <span class="label">{l s='Descriptions' mod='fusion'}</span>
            <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="product_info"></div>
         </div>
         <div class="form-group fswitch-group">
            <span class="label">{l s='Prices' mod='fusion'}</span>
            <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="product_prices"></div>
         </div>
         <div class="form-group fswitch-group">
            <span class="label">{l s='Combinations' mod='fusion'}</span>
            <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="combinations"></div>
         </div>
     </div>
     <div class="col-md-6">
        <div class="form-group fswitch-group">
           <span class="label">{l s='Images' mod='fusion'}</span>
           <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="images"></div>
        </div>
        <div class="form-group fswitch-group">
           <span class="label">{l s='Categories' mod='fusion'}</span>
           <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="categories"></div>
        </div>
        <div class="form-group fswitch-group">
           <span class="label">{l s='Features' mod='fusion'}</span>
           <div class="fswitch sm"><input type="checkbox" class="fswitch-inp" sync-options="features"></div>
        </div>
      </div>

      <div class="col-md-12">
        <button type="button" class="btn btn-default" name="button" data-sync="save-pref">{l s='Save preferences' mod='fusion'}</button>
        <button type="button" class="btn btn-info pull-right" name="button" data-sync="sync-list">{l s='Import' mod='fusion'}</button>
      </div>
  </div>
</div>

<script type="text/javascript">

    var import_hash = "{$import_hash}";
    {literal}
    var FusionApiSync = function()
    {
        this.process_handler = '';
        this.datalist = [];
        this.modal_dialog = false;
        this.options_dialog = false;
        this.allow_to_run = true;
        this.iie = true;

        this.options = {
            images          : true,
            product_name    : true,
            product_info    : true,
            categories      : true,
            product_prices  : true,
            features        : true,
            combinations    : true,
        };

        this.steps = {
          total : 0,
          current : 0
        };

        this.syncProduct = function( total, current, callback)
        {
            if(!this.allow_to_run)
              return;

            console.log( "Total: " + total + " current: " + (current+1) );
            var self = this;
            var data = {
              _key : this.datalist[current],
              _options : this.options,
              _iie : this.iie,
              _action : 'syncProduct',
              _hash : import_hash
            };

            $.ajax({
              type: "POST",
              url: this.process_handler,
              data: data,
              success: function(result){

                  if(result.data != ''){
                      self.modal_dialog.progressFeed(result.data);
                  }

                  if(result.status == 'OK'){
                      var progress = ((current+1)*100)/total;
                      self.modal_dialog.progressBar(progress,(current+1),total);
                      $('[data-id="'+self.datalist[current]+'"]').addClass('success');

                      current ++;
                      if( current < total ){
                          self.syncProduct(total, current, callback);
                      }else{
                          callback();
                      }
                  }else{
                      $('[data-id="'+self.datalist[current]+'"]').addClass('error');
                      self.modal_dialog.progressFeed('<button class="btn btn-sm btn-info" onclick="fusionsync.syncProduct('+total+','+(current+1)+',function(){})">Clique aqui para continuar</button>');
                      alert('Warning!');
                  }
                },
                error: function (request, status, error) {
                    self.modal_dialog.progressFeed('Server busy, try again');
                    $('[data-id="'+self.datalist[current]+'"]').addClass('error');
                    self.modal_dialog.progressFeed('<button class="btn btn-info" onclick="fusionsync.syncProduct('+total+','+(current+1)+',function(){})">Continuar</button>');
                    self.syncProduct(total, current, callback);
                },
                dataType: "json"
            });
        };

        this.loadPreferences = function()
        {
            var options = getCookie('fusion_sync_options');
            if(options!=''){
              options = JSON.parse(options);
              $("[sync-options]").each(function( index ) {
                  var key = $(this).attr('sync-options');
          if(options[key]){
          $('input.fswitch-inp[sync-options="'+key+'"]').parents(".fswitch").addClass('on');
          }
                  $(this).prop("checked", options[key]);
                  $(this).change();
              });
            }else{
              options = {};
            }

            this.options = options;
        };

        this.setOptions = function()
        {
            var iie = true;
            var options = {};
            $("[sync-options]").each(function( index ) {
                var key = $(this).attr('sync-options');
                options[key] = $(this).is(':checked');
                iie &= options[key];
            });
            this.iie = iie;
            this.options = options;
            setCookie('fusion_sync_options', JSON.stringify(this.options), 365);
        };

        this.init = function()
        {
            var self = this;
            this.modal_dialog = new plModal({
                title : "Sync",
                theme : "white bootstrap",
                show_progress_bar : true
            });
            this.modal_dialog.options.closeTimeout = 7000;

            $('body').on('click', '.close-pl-float-wind', function (event) {
                event.preventDefault();
                self.allow_to_run = false;
            });
        };
    }

    var fusionsync = new FusionApiSync();
    fusionsync.init();

    fusionsync.options_dialog = new plModal({
        title : "Sync options",
        theme : "white bootstrap",
        content_from : '#options_form',
    });

  function setCookie(c_name, value, exdays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value = escape(value) + ((exdays == null) ? "" : "; expires=" + exdate.toUTCString());
    document.cookie = c_name + "=" + c_value;
  }

  function getCookie(c_name) {
    var i, x, y, ARRcookies = document.cookie.split(";");
    for (i = 0; i < ARRcookies.length; i++) {
      x = ARRcookies[i].substr(0, ARRcookies[i].indexOf("="));
      y = ARRcookies[i].substr(ARRcookies[i].indexOf("=") + 1);
      x = x.replace(/^\s+|\s+$/g, "");
      if (x == c_name) {
        return unescape(y);
      }
    }
    return '';
  }

    $(document).on('click', '.btn-open-detail' , function(event) {
        var detail = $(this).attr('view-detail');
        $('[detail="'+detail+'"]').show();
    });

    $(document).on('click', '.close-detail' , function(event) {
        var detail = $(this).attr('closedet');
        $('[detail="'+detail+'"]').hide();
    });

  $(document).on('click', '.fswitch' , function(event) {
        $(this).toggleClass('on');
        if($(this).hasClass('on')){
      $(this).find('input.fswitch-inp').prop("checked", true);
    }else{
      $(this).find('input.fswitch-inp').prop("checked", false);
    }
    });

    $(document).on('click', '.import-btn' , function(event) {
        event.preventDefault();
        fusionsync.loadPreferences();
        fusionsync.options_dialog.open();
    });

    $(document).on('click', '[data-sync]' , function(event) {
        event.preventDefault();

        fusionsync.options_dialog.close();

        if( $(this).attr('data-sync') == "save-pref" ){
            fusionsync.setOptions();
            return;
        }

        var data_rows = [];
        var counter = 0;
        var first = false;

        $("[product-line]").each(function( index ) {
            var dataid = $(this).data('id');
            data_rows[counter] = dataid;
            counter ++;
        });

        fusionsync.datalist = data_rows;
        fusionsync.setOptions();

        fusionsync.modal_dialog.progressBar(0,1,Object.keys(data_rows).length);
        fusionsync.modal_dialog.open();
        fusionsync.allow_to_run = true;
        fusionsync.syncProduct( counter, 0, function(){} );

    });

    {/literal}
</script>
