<style media="screen">
   .head-label{
   margin-bottom: 10px;
   }
   .head-label p{
   font-size: 16px;
   color: #333;
   font-weight: bold;
   }
   .association-row{
   margin-bottom: 10px;
   }
   .hidecontent{
   display: none;
   }
</style>
<div class="panel" id="fieldset_0">
   <div class="panel-heading">
      <i class="icon-money"></i>	{l s='Category association'} & {l s=' Profit margin'}
      <span class="panel-heading-action">
      <a class="list-toolbar-btn" href="" data-hide="association-form-content" >
      <span title="" data-toggle="tooltip" class="label-tooltip" data-html="true" data-placement="top">
      <i class="icon-eye"></i>
      </span>
      </a>
      </span>
   </div>
   <div class="form-wrapper" id="association-form-content">
      <div class="row head-label">
         <div class="col-md-2">
            <p>{l s='Original category'}</p>
         </div>
         <div class="col-md-2">
            <p>{l s='Destination category'}</p>
         </div>
         <div class="col-md-2">
            <p>{l s='Shipping cost'} ({$currency->iso_code})</p>
            <div class="row">
               <div class="col-md-6">
                  <input class="form-control input-sm" type="number" name="shipping" value="">
               </div>
               <div class="col-md-6">
                  <button class="btn btn-default btn-sm btn-block" type="button" data-target="shipping" name="button">{l s='Apply to all'}</button>
               </div>
            </div>
         </div>
         <div class="col-md-2">
            <p>{l s='Profit margin'} %</p>
            <div class="row">
               <div class="col-md-6">
                  <input class="form-control input-sm" type="number" name="margin" value="">
               </div>
               <div class="col-md-6">
                  <button class="btn btn-default btn-sm btn-block" type="button" data-target="margin" name="button">{l s='Apply to all'}</button>
               </div>
            </div>
         </div>
         <div class="col-md-2">
            <p>{l s='Extra Profit margin'} %</p>
            <div class="row">
               <div class="col-md-6">
                  <input class="form-control input-sm" type="number" name="extra_margin" value="">
               </div>
               <div class="col-md-6">
                  <button class="btn btn-default btn-sm btn-block" type="button" data-target="extra_margin" name="button">{l s='Apply to all'}</button>
               </div>
            </div>
         </div>
         <div class="col-md-2">
            <p>{l s='Discount from original price'} %</p>
            <div class="row">
               <div class="col-md-6">
                  <input class="form-control input-sm" type="number" name="origin_desc" value="">
               </div>
               <div class="col-md-6">
                  <button class="btn btn-default btn-sm btn-block" type="button" data-target="origin_desc" name="button">{l s='Apply to all'}</button>
               </div>
            </div>
         </div>
      </div>
      <form id="association-form" action="" method="post">
         {foreach from=$feed_categorys item=category key=category_hash}
           <div class="row association-row">
              <div class="col-md-2">
                 <input class="form-control" type="text" name="origin|{$category_hash}" value="{$category.origin}" readonly="true">
              </div>
              <div class="col-md-2">
                 <select class="form-control" name="target|{$category_hash}">
                   {foreach from=$store_categorys item=store_category}
                    <option value="{$store_category.id_category}" {if $category.target == $store_category.id_category}selected="true"{/if}>{$store_category.name}</option>
                   {/foreach}
                 </select>
              </div>
              <div class="col-md-2">
                 <input class="form-control assoc-control" type="number" name="shipping|{$category_hash}" value="{$category.shipping}">
              </div>
              <div class="col-md-2">
                 <input class="form-control assoc-control" type="number" name="margin|{$category_hash}" value="{$category.margin}">
              </div>
              <div class="col-md-2">
                 <input class="form-control assoc-control" type="number" name="extra_margin|{$category_hash}" value="{$category.extra_margin}">
              </div>
              <div class="col-md-2">
                 <input class="form-control assoc-control" type="number" name="origin_desc|{$category_hash}" value="{$category.origin_desc}">
              </div>
           </div>
         {/foreach}

         <div class="panel-footer">
            <button type="submit" value="1" name="submitAssociationForm" class="btn btn-default pull-right"><i class="process-icon-save"></i> Guardar </button>
         </div>
      </form>
   </div>

</div>


<script type="text/javascript">

   //utility function
   function getFormData(data) {
     var unindexed_array = data;
     var indexed_array = {};

     $.map(unindexed_array, function(n, i) {
     indexed_array[n['name']] = n['value'];
     });

     return indexed_array;
   }

   function initAssocForm()
   {
       try{
           association_form_content = Fusion.getCookie("show_association_form_content");
           if ( association_form_content != "" ) {
              $('#association-form-content').removeClass('hidecontent');
           }else{
              $('#association-form-content').addClass('hidecontent');
           }
       }catch(e){
          setTimeout(initAssocForm, 250);
       };
   }

   $(document).on('click', '[data-target]' , function(event) {
       event.preventDefault();
       var target = $(this).attr('data-target');
       $('input[name^="'+target+'"].assoc-control').val( $('[name="'+target+'"]').val() );
   });

   $(document).on('click', '[data-hide="association-form-content"]' , function(event) {
       event.preventDefault();

       $('#association-form-content').toggleClass('hidecontent');

       if( $('#association-form-content').hasClass('hidecontent') ){
          change_to = '';
       }else{
          change_to = '1';
       }
       Fusion.setCookie("show_association_form_content", change_to, 365);
   });

   $(document).on('submit', '#association-form' , function(event) {
       event.preventDefault();

       var form_data = $(this).serializeArray();
       var data = {
         _data : JSON.stringify(getFormData(form_data)),
         _action : 'saveAssociations'
       };

       $.ajax({
         type: "POST",
         url: this.process_handler,
         data: data,
         success: function(result){
             if(result.status == 'OK'){
                 alert('Sucesso');
             }else{
                 alert('ERRO');
             }
         },
         error: function (request, status, error) { },
         dataType: "json"
       });

   });

   $( document ).ready(function() {
     initAssocForm();
   });

</script>