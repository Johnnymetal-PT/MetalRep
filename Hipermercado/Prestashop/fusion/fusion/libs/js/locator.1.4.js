function FSLocator() {

    this.location_list = false;
    this.locator_url = '';

    this.eventListner = () => {
        var self = this;

        $('body').on('click', '.location-overlay', function (event) {
            event.preventDefault();
            self.closeLocator();
        });

        $('body').on('click', '.location-selector, .location-selector-alt', function (event) {
            event.preventDefault();
            self.refreshLocatorPosition();
            self.locatorToggleOpen();
        });

        $('body').on('click', '.close-locator', function (event) {
          	event.preventDefault();
          	self.refreshLocatorPosition();
          	self.locatorToggleOpen();
        });

        $('body').on('click', '.locate-list-item', function (event) {
          	event.preventDefault();
          	$.ajax({ type: 'POST', cache: false, url: self.locator_url+'?locate='+$(this).data('locale-id'), contentType: "application/json", dataType: 'json',
          	    complete: function(){},
          	    beforeSend: function(){ self.locationChangeRequest() },
          	    success: function(data){
                  var redirectTo = self.removeparametersFromURL(window.location.href);
                  window.location.replace(redirectTo);
                }
          	});
        });

        $(document).click(function(event) {
            var $target = $(event.target);
            if(!$target.closest('.locate-wind').length&&!$target.closest('.location-selector').length) {
                self.closeLocator();
            }
        });

        window.addEventListener('resize', function(event){
          	self.refreshLocatorPosition();
        });

        $(window).scroll(function() {
        });
    };

    this.removeparametersFromURL = (url_string) => {
        URL = url_string;
        if (url_string.indexOf("#") > 1) {
            URL = url_string.split("#")[0];
            url_update= true;
        }
        if (url_string.indexOf("?") > 1) {
            URL = url_string.split("?")[0];
            url_update= true;
        }
        return URL;
    }

    this.locationChangeRequest = () => {};

    this.locatorToggleOpen = () => {
        if($('.locate-wind').hasClass('open')){
            this.closeLocator();
        }else{
            this.openLocator();
        }
    };

    this.closeLocator = () => {
        $('body').removeClass('lockBodyScroll');
        $('.location-overlay').removeClass('is-visible');
        $('.locate-wind').removeClass('open');
    };

    this.openLocator = () => {
        if(this.location_list==false){
            this.loadLocationsWindow();
        }
        $('body').addClass('lockBodyScroll');
        $('.location-overlay').addClass('is-visible');
        $('.locate-wind').addClass('open');
    };

    this.loadLocationsWindow = () => {
        var self = this;
        $.ajax({ type: 'POST', cache: false, url: self.locator_url+'?getlist=1', contentType: "application/json", dataType: 'json',
      	    complete: function(){},
      	    beforeSend: function(){ self.locationChangeRequest() },
      	    success: function(data){
                $('.locate-wind').html(data.list_html);
                self.location_list = true;
                $('.locate-wind').removeClass('loading');
            }
      	});
    };

    this.refreshLocatorPosition = () => {
        console.log('refreshLocatorPosition');
        if($(window).width() > 991){
            var position = $('.location-selector').offset();
            var offset_left = 14, offset_top = 30;
            $('.locate-wind').css('margin-left',(position.left-offset_left)+'px');
            $('.locate-wind').css('margin-top',(position.top+offset_top)+'px');
        }else{
            $('.locate-wind').css('margin-left','auto');
            $('.locate-wind').css('margin-top', 'auto');
        }
    };

    this.init = () => {
        this.locator_url = $('.locate-wind').attr('data-locator');
        this.eventListner();
        console.log('FSLocator');
    };

};

var locator = new FSLocator();

$(function (){
    locator.init();
});







function locationFilter(){
  	var substring = document.getElementById("location-search-input").value;
  	substring = substring.toLowerCase();
  	$(".locate-list-item").each(function(index) {
    		var string = $(this).attr('data-location');
    		string = string.toLowerCase();
    		var check = string.includes(substring);
    		if ( !check ) {
    			   $(this).hide();
    		}else{
    			   $(this).show();
    		}
  	});
}




