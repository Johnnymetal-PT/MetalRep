<div style="font-size: 13px;font-weight: 700;}">{l s='Custo de envio para'} {$country_name}
    <table class="table table-sm">
        {foreach from=$shipping_options item=shipping_option}
            <tr>
                <td>{$shipping_option.name}</td>
                <td>{$shipping_option.price}</td>
            </tr>
        {/foreach}
    </table>
</div>