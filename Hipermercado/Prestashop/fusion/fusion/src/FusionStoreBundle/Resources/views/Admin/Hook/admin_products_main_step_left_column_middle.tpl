
{if isset($product_sync_source)}

  <style media="screen">
      .fusionSyncFromLabel{
        position: fixed;
        bottom: 81px;
        right: 0;
        width: auto;
        height: 30px;
        line-height: 30px;
        background: #ffffff;
        padding-left: 10px;
        padding-right: 10px;
        z-index: 1000;
        border: solid 1px #6c858e;
        border-right: none;
        border-bottom: none;
      }
      .fusionSyncFromLabel p{
        color: #6c858e;
        line-height: 1;
        margin: 0;
        padding: 0;
        display: inline-block;
        font-weight: 700;
      }
      .fusionSyncFromLabel .label{
        color: #848484;
        font-weight: 200;
      }
      .fusionSyncFromLabel .interact{
        cursor: pointer;
      }
  </style>

  <div class="fusionSyncFromLabel">
    <div class="" style="display: inline-block; margin-right: 20px;">
      <span class="label">{l s='Skip product' mod='fusion'}</span>
      <input
          class="switch-input-sm"
          id="skip_this_product_from_update"
          data-toggle="switch"
          type="checkbox"
          name="skip_this_product_from_update"
          value="1"
          {if $skip_product}checked="checked"{/if}
        />
    </div>
    <div class="interact" data-action="loadImportRecord" data-last_update="{$last_update_days}" style="display: inline-block">
      <p> <span class="label">{l s='Product linked from ' mod='fusion'}</span> {$product_sync_source} {if (int)$last_update_days >= 2 }<i style="font-size: 18px;top: -1px;position: relative;color: #ff8d18;" class="material-icons">warning</i>{/if}</p>
    </div>

    <div id="syncInfoModal" style="display: none;">

        {if (int)$last_update_days >= 2 }
          <div class="alert expandable-alert alert-warning mt-3" role="alert">
            <p class="alert-text">
              {l s='This product has not been updated for more than 2 days.' mod='fusion'}
            </p>
          </div>
          <div class="alert expandable-alert alert-warning mt-3" role="alert">
            <p class="alert-text">
              {l s='No matching products found on suppliers.' mod='fusion'}
            </p>
          </div>
        {/if}

        <p>{l s='Linked to' mod='fusion'} <strong>{$product_sync_source}</strong> </p>
        <p>{l s='Module:' mod='fusion'} <strong>{$product_sync_module}</strong></p>
        <p>{l s='Last update:' mod='fusion'} <strong>{$last_update_days}</strong> {l s='days ago' mod='fusion'}</p>
        <pre class="json_feed">
          <code>
          {$feed_data|htmlspecialchars_decode|strip_tags}
          </code>
        </pre>
    </div>
  </div>

  <script type="text/javascript">

    var id_sync_entry = {$id_sync_entry};
    var fusion_id_product = {$fusion_id_product};

    {literal}

    var modal_dialog = new plModal({
        title : "{/literal}{l s='Detalhes' mod='fusion'}{literal}",
        theme : "white",
        content_from : "#syncInfoModal"
    });

    $('.fusionSyncFromLabel').appendTo(document.body);

    $('.interact[data-action="loadImportRecord"]').bind( "click", function() {
        modal_dialog.open();
    });

    $(document).ready(function() {
        //set initial state.
        $('#skip_this_product_from_update').change(function() {
            if(this.checked) {
                var skip_this_product_from_update = 1;
            }else{
                var skip_this_product_from_update = 0;
            }

            (new FusionReq({
                module : 'fusion',
                success : ( result ) => {
                    showSuccessMessage({/literal}'{l s='Saved' mod='fusion'}'{literal});
                },
                error : () => { showErrorMessage({/literal}'{l s='Error' mod='fusion'}'{literal}); }
            })).save({
                action : 'changeProductSkipOption',
                id_sync_entry : id_sync_entry,
                id_product : fusion_id_product,
                skip_this_product_from_update : skip_this_product_from_update
            });
        });
    });
    {/literal}
  </script>

{/if}
