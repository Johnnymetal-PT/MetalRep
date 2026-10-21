/* Fusion Request  */

function FusionReq(options)
{
    let defaults = {
        module : null,
        cache : false,
        request_type : 'POST',
        request_format : 'json',
        error : () => {},
        success : () => {},
        complete : () => {},
        before : () => {},
        after : () => {}
    };

    options = { ...defaults, ...options };

    let _this = this;

    this.save = ( data ) => {

        if( options.module!==null ){
            url = fusion.urls.modules + '&configure='+options.module+'&submit'+options.module+'=1';
        }else{
            url = window.location.href;
        }

        $.ajax({ type: options.request_type, cache: options.cache, url: url, data : data, dataType: options.request_format,
            complete: function(){ options.complete(); },
            beforeSend: function(){ options.before(); },
            success: function( data ){
                options.success( data );
            },
            error: function (xhr, ajaxOptions, thrownError) {
                options.error(xhr, ajaxOptions, thrownError);
            }
        });

    }
}
