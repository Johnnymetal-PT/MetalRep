{if isset($averageTotal) && $averageTotal > 0}
  <div class="product-rating" itemprop="review" itemtype="http://schema.org/Review" itemscope>
    <meta itemprop="author" content="Customer" />

    <div class="star_content clearfix">
      {section name="i" start=0 loop=5 step=1}
        {if $averageTotal le $smarty.section.i.index}
          <span class="star star_off">&#9733;</span>
        {else}
          <span class="star star_on">&#9733;</span>
        {/if}
      {/section}
    </div>

    <span class="interactions-total">({$interactionsTotal})</span>

    {if isset($ratings)}
      <div itemprop="reviewRating" itemtype="http://schema.org/Rating" itemscope>
        <meta itemprop="ratingValue" content="{if isset($ratings.avg)}{$ratings.avg|round:1|escape:'html':'UTF-8'}{else}{$averageTotal|round:1|escape:'html':'UTF-8'}{/if}" />
        <meta itemprop="bestRating" content="5" />
      </div>
    {/if}
  </div>
{else}
  <div itemtype="http://schema.org/AggregateRating" itemscope="" itemprop="aggregateRating" class="comments_note">
    <!--<div class="star_content clearfix">
      <span class="star">&#9734;</span>
      <span class="star">&#9734;</span>
      <span class="star">&#9734;</span>
      <span class="star">&#9734;</span>
      <span class="star">&#9734;</span>
    </div>-->
  </div>
{/if}
