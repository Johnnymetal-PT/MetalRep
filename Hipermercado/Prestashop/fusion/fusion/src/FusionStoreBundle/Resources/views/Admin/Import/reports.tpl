
{function renderReportActions report=report reportindex=reportindex}
  <div class="quick-view">
    {if $report.bad_weight > 0}
      <span class="alert-note-filter" filter="weight">{l s='Products with 0 weight' mod='fusion'} <strong>{$report.bad_weight}</strong></span>
    {/if}
    {if $report.bad_ean13 > 0}
      <span class="alert-note-filter" filter="ean13">{l s='Products with invalid ean13' mod='fusion'} <strong>{$report.bad_ean13}</strong></span>
    {/if}
    {if $report.bad_features > 0}
      <span class="alert-note-filter" filter="features">{l s='Products with no features' mod='fusion'} <strong>{$report.bad_features}</strong></span>
    {/if}
    <button class="btn btn-info" style="display:none;"
      data-action="clearFilter">
      {l s='Clear filter' mod='fusion'}
    </button>
  </div>
  <div class="report-actions">

    <button class="btn btn-danger"
      data-action="deleteReport"
      data-module="{$module}"
      data-filename="{$report.filename}">
      {l s='Delete report' mod='fusion'}
    </button>
  </div>
{/function}

{function renderReportFeedData itemindex=itemindex feed=feed}
  <div class="col-md-12">
    <div style="margin-top:10px;" class="fstab" data-source="feed_{$itemindex}">{l s='View complete feed' mod='fusion'}</div>
    <div class="info-notes fstabc" data-target="feed_{$itemindex}">
      <table class="table table-sm">
        <thead>
          <th> <strong>{l s='Prop' mod='fusion'}</strong> </th>
          <th> <strong>{l s='Info' mod='fusion'}</strong> </th>
        </thead>
        {foreach from=$feed item=data key=item_prop}
          <tr>
            <td width="30%">{$item_prop}</td>
            <td>{$data|@var_dump}</td>
          </tr>
        {/foreach}
      </table>
    </div>
  </div>
{/function}

{function renderReportDetailErrors errors=errors}
  <div class="info-errors">
    <span class="label">{l s='Import log'  mod='fusion'}</span>
    {foreach from=$errors item=error}
        <p>{$error}</p>
    {/foreach}
  </div>
{/function}


{function renderReportDetailNotes notes=notes}
  <div class="info-notes">
    <span class="label">{l s='Product data' mod='fusion'}</span>
    <table class="table table-sm">
      <thead>
        <th> <strong>{l s='Prop' mod='fusion'}</strong> </th>
        <th> <strong>{l s='Info' mod='fusion'}</strong> </th>
        <th> <strong>{l s='Validation pass' mod='fusion'}</strong> </th>
      </thead>
      {foreach from=$notes item=note key=notekey}
        {if isset($note[0]) && isset($note[1])}
          <tr>
            <td width="30%">{$notekey}</td>
            <td>{$note[0]}</td>
            <td>{if !$note[1]}<i class="fsi-check fsi-xs"></i>{else}<i class="fsi-cross fsi-xs"></i>{/if}</td>
          </tr>
        {/if}
      {/foreach}
    </table>
  </div>
{/function}

{function renderReportResumeNotes notes=notes}
  {foreach from=$notes item=note key=notekey}
    {if isset($note[0]) && isset($note[1])}
      {if !$note[1]}

      {else}
        <span class="alert-resume-label">{$notekey}</span> <i class="fsi-cross fsi-xs"></i>
      {/if}
    {/if}
  {/foreach}
{/function}

{function renderReportAlertsFilters notes=notes}
  {foreach from=$notes item=note key=notekey}
    {if isset($note[0]) && isset($note[1])}
      {if $note[1]}
        alert-filter-{$notekey}
      {/if}
    {/if}
  {/foreach}
{/function}



{foreach from=$reports item=report key=reportindex}
    <div class="report-item" data-report="{$reportindex}" report="{$report.filename}">
      <div class="report-name fstab" data-source="{$reportindex}">
        <i class="fsi-file fsi-sm"  style="margin-right: 10px;"></i>
        <span> <strong>{l s='Report on' mod='fusion'}</strong> {$report.filedate} <strong>{l s='at' mod='fusion'}</strong> {$report.filehour}  <i class="repo-filename">{$report.filename}</i> </span>

        <span class="alert-icons">
          {if $report.result}
            <span><i class="fsi-success fsi-sm" style="margin-right:10px;"></i>{l s='Import Success' mod='fusion'} </span>
          {else}
            <span><i class="fsi-error fsi-sm" style="margin-right:10px;"></i>{l s='Import Fail' mod='fusion'} </span>
          {/if}
          {if $report.need_alert}
            <span><i class="fsi-warning fsi-sm" style="margin-right:10px;"></i>{l s='Check warnings' mod='fusion'} </span>
          {/if}
        </span>
      </div>
      <div class="report-content fstabc" data-target="{$reportindex}">

        {renderReportActions report=$report reportindex=$reportindex}

        {foreach from=$report.contents item=item key=itemindex}
          <div class="product-row {if $item.result}success{else}error{/if} {if $item.need_alert}need-alert{/if}" data-item-index="{$itemindex}" {renderReportAlertsFilters notes=$item.report.notes}>

            <div class="identifier">

              {if $item.result}
                {if $item.need_alert}
                  <i class="fsi-warning fsi-xs" style="margin-right: 10px;"></i>
                {else}
                  <i class="fsi-success fsi-xs" style="margin-right: 10px;"></i>
                {/if}
              {else}
                <i class="fsi-error fsi-xs" style="margin-right: 10px;"></i>
              {/if}

              {$itemindex}

              <span class="alert-resume-note">{renderReportResumeNotes notes=$item.report.notes}</span>

              <div class="actions">
                <button class="btn fstab" data-source="report_{$itemindex}" name="button">{l s='View report detail' mod='fusion'}</button>
              </div>
            </div>
            <div class="fstabc" data-target="report_{$itemindex}">

              <div class="row">
                <div class="col-md-8">
                  {renderReportDetailNotes notes=$item.report.notes}
                </div>
                <div class="col-md-4">
                  {renderReportDetailErrors errors=$item.report.errors}
                </div>
              </div>
              <div class="row">
                {renderReportFeedData itemindex=$itemindex feed=$item.feed_data}
              </div>
            </div>
          </div>
        {/foreach}
      </div>

    </div>
{/foreach}
