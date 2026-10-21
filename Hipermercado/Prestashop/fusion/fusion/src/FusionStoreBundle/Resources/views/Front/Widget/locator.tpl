
{function renderWidget}
<a href="#" class="location-selector">
  <div class="flags f18 flag-{$location_options.customer_locate.iso_code|lower}"></div>
  <i class="ti-angle-down"></i>
  <span>COUNTRY / REGION</span>
</a>
{/function}


{function renderWindowContainer}
<div class="location-overlay byw-overlay"></div>
<div class="locate-wind loading" data-locator="{$locator_url}">
	<div class="locate-top-close">
		<a href="#" class="close-locator"><i class="ti-close"></i></a>
	</div>
</div>
{/function}


{function renderWindowContent}
  <div class="locate-top-close">
  	<a href="#" class="close-locator"><i class="ti-close"></i></a>
  </div>

  <div class="locate-head">
  	<span class="locate-head-title">{l s='Delivery Country or Region' d='Shop.Theme.Global'}</span>
  	<span class="locate-head-descr">{l s='You are currently shipping to' d='Shop.Theme.Global'} {$location_options.customer_locate.name} {l s='and your order will be billed in' d='Shop.Theme.Global'} {$location_options.customer_locate.currency.iso_code} {$location_options.customer_locate.currency.symbol} </span>
  </div>

  <div class="locate-search-box">
  	<input onkeyup="locationFilter()" id="location-search-input" class="search-input" type="search" name="locate-search" placeholder="Search for a country or region">
  	<svg class="search-box-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"> <g fill="none" fill-rule="evenodd" stroke="#222" stroke-width="2" transform="translate(7 6)"> <circle cx="4.327" cy="4.326" r="3.995"></circle> <path stroke-linecap="round" stroke-linejoin="round" d="M7.32 7.32l2.995 2.995"></path> </g> </svg>
  </div>

  <ul class="locate-list">

    <li class="current-locate-list-item" data-ctrcode="{$location_options.customer_locate.iso_code}">
       <div class="flags f18 flag-{$location_options.customer_locate.iso_code|lower}"></div>
       <span>{$location_options.customer_locate.name} <span>({l s='selected' d='Shop.Theme.Global'})</span></span> <span class="locate-current-label">{$location_options.customer_locate.currency.iso_code} {$location_options.customer_locate.currency.symbol}</span>
    </li>

    <!--<li class="locate-list-no hide" data-test="no-countries-found-search-result-div"> No results found </li>-->

    {foreach from=$location_options.location_selector item=location key=key}
  		<li data-ctrcode="{$location.iso_code}" data-currency="{$location.id_currency}" data-location="{$location.country}" class="locate-list-item" data-locale-id="{$location.id_country}">
   			<div class="flags f18 flag-{$location.iso_code|lower}"></div>
   			<span>{$location.country}</span><span class="locate-list-label">{$location.currency.iso_code} {$location.currency.symbol}</span>
    		</li>
  	{/foreach}
  </ul>
{/function}


{if $renderwhat == 'renderWidget'}
  {renderWidget}
  {renderWindowContainer}
{else}
  {renderWindowContent}
{/if}
