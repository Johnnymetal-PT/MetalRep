{extends file='page.tpl'}

{block name='head_seo' prepend}
  <link rel="canonical" href="{$product.canonical_url}">
{/block}

{block name='nav_menu'}{/block}
{block name='product_page_top_banner'}{/block}


{block name='content'}


<style media="screen">
  .name_details{
    text-align: center;
  }
  .productName .name_details{
    margin-top: 60px;
    margin-bottom: 80px;
  }
  .add-to-cart{
    display: block;
    min-width: 200px;
    margin: auto;
    width: 100%;
    background: #4dd19e;
    margin-bottom: 30px;
    margin-top: 30px;
  }
  .priceBlock{
    margin-top: 40px;
  }
  .productShort span{
    line-height: 24px;
  }
</style>

<section id="main" itemscope itemtype="https://schema.org/Product">
  <meta itemprop="url" content="{$product.url}">

  <div class="row">
    <div class="col-md-12">
      <div class="productName">
        <h1 class="h1 name_details" itemprop="name">{block name='page_title'}{$product.name}{/block}</h1>
      </div>
    </div>


    <div class="col-md-8">
      {foreach from=$product.images item=image}
        {if $image.cover}
          <div class="">
            <a href="{$image.bySize.large_default.url}">
              <img class=""  style="width:100%;" src="{$image.bySize.large_default.url}" alt="{$image.legend}" title="{$image.legend}" itemprop="image">
            </a>
          </div>
        {/if}
 		 {/foreach}
    </div>

    <div class="col-md-4">

      <div class="productShort" itemprop="description">
        {$product.description_short nofilter}
      </div>

      <div class="priceBlock">

        {if $product.show_price}
          <div class="product-prices">

            {block name='product_price'}
              <div class="product-price h5 {if $product.has_discount}has-discount{/if}" itemprop="offers" itemscope itemtype="https://schema.org/Offer">
                <link itemprop="availability" href="{$product.seo_availability}"/>
                <meta itemprop="priceCurrency" content="{$currency.iso_code}">

                <div class="productPrices">
                  <span itemprop="price" content="{$product.price_amount}" class="current-price" price-current="{$product.price}">{$product.price}</span>

                  {if $product.has_discount}
                    <span class="now-label">{l s='Now' d='Shop.Theme.Catalog'}</span>
                    <span class="regular-price">{$product.regular_price}</span>
                    {*if $product.discount_type === 'percentage'}
                      <span class="discount discount-percentage">{l s='Save %percentage%' d='Shop.Theme.Catalog' sprintf=['%percentage%' => $product.discount_percentage_absolute]}</span>
                    {else}
                      <span class="discount discount-amount"> {l s='Save %amount%' d='Shop.Theme.Catalog' sprintf=['%amount%' => $product.discount_to_display]} </span>
                    {/if*}
                  {/if}

                  {hook h='displayProductDiscount' product=$product}

                  <span class="display_tax_exclude">{l s='tax excl.' d='Shop.Theme.Catalog'}</span>
                  <span class="display_tax_include">{l s='tax incl.' d='Shop.Theme.Catalog'}</span>
                </div>
              </div>
            {/block}

          </div>
        {/if}

      </div>

      <div class="product-add-to-cart">
        <div class="add">
          <button class="btn btn-primary add-to-cart" data-button-action="add-to-cart" type="submit" {if !$product.add_to_cart_url}disabled {/if} >
            {l s='Buy' d='Shop.Theme.Actions'}
          </button>
        </div>
      </div>

    </div>

    <div class="col-md-12">
      <div class="productDesca">
        {$product.description nofilter}
      </div>
    </div>

  </div>

  <div style="height: 50px; width: 100%; display: block"> </div>

</section>

{/block}
