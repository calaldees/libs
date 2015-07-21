var utils = {};

(function(external){
	
	function get_func(obj, cmd) {
		//console.log('get_func', obj, cmd);
		if (typeof(cmd) == "string") {cmd = cmd.split(".");}
		if (cmd.length == 1) {return obj[cmd.shift()];}
		if (cmd.length > 1) {
			var next_cmd = cmd.shift();
			var next_obj = obj[next_cmd];
			if (typeof(next_obj) == "undefined") {
				console.error(""+obj+" has no attribute "+next_cmd);
				return function(){};
			}
			return get_func(next_obj, cmd);}
		console.error('What?');
		return function(){};
	}
	
	external.functools = {
		get_func: get_func,
	};
}(utils));


(function(external){

	function getUrlParameter(sParam) {
		//http://stackoverflow.com/questions/19491336/get-url-parameter-jquery
		var sPageURL = window.location.search.substring(1);
		var sURLVariables = sPageURL.split('&');
		for (var i = 0; i < sURLVariables.length; i++) {
			var sParameterName = sURLVariables[i].split('=');
			if (sParameterName[0] == sParam) {
				return sParameterName[1];
			}
		}
		return '';
	}
	
	external.url = {
		getUrlParameter: getUrlParameter,
	};
}(utils));


(function (external) {
	external.path = {
		is_image: function(src) {
			return src && src.match(/\.(jpg|png|bmp|gif|jpeg|svg|tiff)$/);
		},
		is_audio: function(src) {
			return src && src.match(/\.(mp3|wav|ogg|flac|ac3|mp2)$/);
		},
		is_video: function(src) {
			return src && src.match(/\.(mp4|avi|mov|mkv|ogm|3gp)$/);
		}
	};
}(utils));

