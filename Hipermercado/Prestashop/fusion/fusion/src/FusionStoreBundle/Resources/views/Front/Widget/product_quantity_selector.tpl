<div class="">
  <div id="qty-select" data-name="quantidade" style="display:none;">
    {foreach from=$specific_prices item=specific_price}
      <div class=""
        data-value="{$specific_price.quantity}"
        unit-price="{$specific_price.unit_price_tax_excl}"
        total-price-tax-excl="{$specific_price.total_price_tax_excl}"
        total-price-tax-incl="{$specific_price.total_price_tax_incl}"
        >
        <span class="min-unit">{$specific_price.quantity}</span>
        <span class="unit-price"><span class="label">{l s='Preço unid.'}</span> {$specific_price.unit_price_tax_excl}</span>
        <span class="price-count-ex">{$specific_price.total_price_tax_excl}</span>
        <span class="price-count-incl">{$specific_price.total_price_tax_incl} <span class="label">{l s='IVA incl.'}</span></span>
      </div>
    {/foreach}
  </div>
</div>
