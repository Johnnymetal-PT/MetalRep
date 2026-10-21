$(".btn-top").hide();
$(document).ready(function () {
    $('#wrapwrap').scroll(function() {
      if ($(this).scrollTop() > 100) {
         $('.btn-top').fadeIn();
      } else {
         $('.btn-top').fadeOut();
      }
    });

    $(".btn-top").on("click", function (e) {
        return e.preventDefault(), $("#wrapwrap").animate({ scrollTop: 0 }, 800), !1;
    });

});