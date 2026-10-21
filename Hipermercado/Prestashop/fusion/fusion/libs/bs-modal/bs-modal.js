/* v 1.2.3 */
function plModal(options) {
		this.contentSelector = 'body';
		// defaul params
		let defaults = {
				id: false,
				autoCloseTimeout: 1000,
				closeTimeout: false,
				show_progress_bar: false,
				title : "",
				content : "",
				content_from : false,
				theme : "white",
				ajaxLoader : "ajax-loader",
				removeAfterClose : false
		};

		this.options = { ...defaults, ...options };

		// functions
		this.initModal = function(){
				var progress_bar = (this.options.show_progress_bar===true?'<div class="progress"><div class="progress-percent"></div><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100" style="width: 0%"></div></div><div class="steps"><span class="current">0</span><span class="steps-division">/</span><span class="total">0</span></div>':'');
				if(this.options.content_from!==false){
						this.options.content = $(this.options.content_from).html();
						$(this.options.content_from).html(" ");
				}

				var html_modal = `
				<div class="pl-float-wind theme-`+this.options.theme+(this.options.removeAfterClose?' rmafter ':'')+`" id="`+this.options.id+`">
				  <div class="pl-float-wind-close">
				    <span class="pl-float-wind-head"></span>
				    <a href="#" class="close-pl-float-wind"> <i class="material-icons">close</i> </a>
				  </div>
				  <div class="pl-float-wind-cont">
				    <div class="row">
				      <div class="col-md-12 inner"> `+this.options.content+` </div>
				      <div class="col-md-12 progress-inner">`+progress_bar+`</div>
				    </div>
				    <div class="progress-feed"></div>
				    <div class="progress-content"></div>
				  </div>
				</div>
				`;
				$(this.contentSelector).append(html_modal);
		};

		this.attachContent = function( content ){
				$('#'+this.options.id+' .pl-float-wind-cont>.row>.col-md-12.inner').html(content);
				return this;
		};

		this.create = function(options){
				if(this.options.id==false)
						this.options.id = 'md-'+Date.now()+'-'+Math.random().toString(36).substr(2, 9);
				if(!$('#'+this.options.id).length ){
				 		this.initModal();
				 		$('#'+this.options.id+' .pl-float-wind-head').html(this.options.title);
			 	}
			 	if(this.options.show_progress_bar)
						this.progressBar(0, 0, 0, true);
				return this;
		};

		this.destroy = function(){
				$('#'+this.options.id).remove();
		};

		this.close = function( timeout ){
				if( this.options.closeTimeout || timeout ){
						setTimeout( function(){
								this.close();
						}, this.options.autoCloseTimeout);
				}else{
						if($('#'+this.options.id).hasClass('open')){
								$('#'+this.options.id).removeClass('open');
						}
						$('.pl-overlay').removeClass('is-visible');
				}
				if(this.options.removeAfterClose){
						this.destroy();
				}
				return this;
		};

		this.open = function(){
			 	if(!$('#'+this.options.id).length ){
			 			return false;
			 	}
				$('.pl-overlay').addClass('is-visible');
				$('.pl-overlay').attr('wind-link', this.options.id);
				$('#'+this.options.id).addClass('open');
				return this;
		};

		this.content = function(content, append){
				append = (typeof append !== 'undefined') ?  append : false;
				if( !$('#'+this.options.id+' .progress-content').hasClass('is-visible') ){
						$('#'+this.options.id+' .progress-content').addClass('is-visible')
				}
				if(append)
						$('#'+this.options.id+' .progress-content').append(''+content+'');
				else
						$('#'+this.options.id+' .progress-content').html(''+content+'');
				return this;
		};

		this.isLoad = function(){
				$('#'+this.options.id).addClass(this.options.ajaxLoader);
				return this;
		};

		this.isLoaded = function(){
				$('#'+this.options.id).removeClass(this.options.ajaxLoader);
				return this;
		};

		this.progressFeed = function(msg){
				if( !$('#'+this.options.id+' .progress-feed').hasClass('is-visible') ){
						$('#'+this.options.id+' .progress-feed').addClass('is-visible')
				}
				$('#'+this.options.id+' .progress-feed').append('<p>'+msg+'</p>');
				$('#'+this.options.id+' .progress-feed').animate({ scrollTop: $('#'+this.options.id+' .progress-feed').prop("scrollHeight")}, 300);
				return this;
		};

		this.progressBar = function(progress, current_step, total_steps, ignore_hidden){
				ignore_hidden = (typeof ignore_hidden == 'undefined') ? false : ignore_hidden;
				if( ignore_hidden === false ){
						this.showProgressBar();
				}
				$('#'+this.options.id+' .progress .progress-bar').css('width', progress+'%');
				$('#'+this.options.id+' .progress .progress-percent').html( Math.round(progress * 10) / 10+'%');
				$('#'+this.options.id+' .steps .current').html(current_step);
				if (typeof total_steps !== 'undefined')
						$('#'+this.options.id+' .steps .total').html(total_steps);
				return this;
		};

		this.hideProgressBar = function(){
				$('#'+this.options.id+' .progress-inner').fadeOut(200);
				return this;
		};

		this.showProgressBar = function(){
				if( !$('#'+this.options.id+' .progress-inner').is(":visible") ){
						$('#'+this.options.id+' .progress-inner').fadeIn(200);
				}
				return this;
		};

		this.changeTitle = function(title){
				this.options.title = title;
				$('#'+this.options.id+' .pl-float-wind-head').html(this.options.title);
		};

		this.changeContent = function(content){
				this.attachContent(content);
		};

		if(typeof options !== 'undefined'){
				this.create(options);
		}
}

function BSForm( fields )
{
		this.fields = fields;

		this.id = 'f_' + Math.random().toString(36).substr(2, 9);

		this.submit = ( submit_calback ) =>
		{
				let self = this;
				$(document).on('submit', '#'+this.id, function (event) {
						event.preventDefault();
						submit_calback(this, self.getFormData($(this)), event);
				});
				return this;
		};

		this.getFormData = ($form) => {
		    var unindexed_array = $form.serializeArray();
		    var indexed_array = {};
		    $.map(unindexed_array, function(n, i){
		        indexed_array[n['name']] = n['value'];
		    });
		    return indexed_array;
		}

		this.render = () =>
		{
				let content = '';
				$.each( this.fields, function( field_name, params ) {

						var value = ( typeof params.value === 'function' ) ? params.value() : params.value;
						var required = ( typeof params.required !== 'undefined' ) ? params.required : false;
						var placeholder = ( typeof params.placeholder !== 'undefined' ) ? params.placeholder : '';

						if( params.type == 'select' ){

								content += '<label>'+params.label+'</label> <select name="'+field_name+'">';
								$.each(params.options, function( option_value, label ) {
										content += '<option value="'+option_value+'" '+(option_value == value ?'selected="true"':'')+' >'+label+'</option>';
								});
								content += '</select>';

						}else if( params.type == 'submit' || params.type == 'button' ){

								content += `
								<div class="actions">
									<button type="`+params.type+`"">`+params.label+`</button>
								</div>`;

						}else if( params.type == 'hidden' ){

								content += `<input type="`+params.type+`" name="`+field_name+`" value="`+value+`" hidden="true">`;

						}else{

								content += `
								<div>
									<label>`+params.label+`</label>
									<input type="`+params.type+`" name="`+field_name+`" value="`+value+`" `+(required?'required="true"':'')+` placeholder="`+placeholder+`">
								</div>`;

						}
				});
				return `<form id="`+this.id+`"> `+content+` </form>`;
		};
}

$(function () {

		console.log('Ready PlModal');

		if($("#content").length){
	  		$('#content').append('<div class="pl-overlay"></div>');
	  }

		if($("#main-div").length){
	  		$('#main-div').append('<div class="pl-overlay"></div>');
	  }

		$('body').on('click', '.close-pl-float-wind', function (event) {
				event.preventDefault();
				$('.pl-overlay').removeClass('is-visible');
				$('.pl-float-wind').removeClass('open');
				$(".pl-float-wind").each(function( index ) {
				    if( $(this).hasClass('rmafter') ){
				      	$(this).remove();
				    }
			  });
		});

		$('body').on('click', '.pl-overlay', function (event) {
				$(this).removeClass('is-visible');
				var windlink = $(this).attr('wind-link');
				console.log(windlink);
				$('#'+windlink).removeClass('open');
				if( $('#'+windlink).hasClass('rmafter') ){
						$('#'+windlink).remove();
				}
		});
});

/*
teste.open({
	id : 'teste-modal-clone',
	title : "Titulo do modal clone",
	content : "conteudo do modal clone",
	autoCloseTimeout : 1000
});*/
