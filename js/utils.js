var utils = {};

(function(external){
	
	function get(cmd, obj, fallback_return) {
		obj = obj || window;
		if (typeof(cmd) == "string") {cmd = cmd.split(".");}
		if (cmd.length == 1) {return obj[cmd.shift()];}
		if (cmd.length > 1) {
			var next_cmd = cmd.shift();
			var next_obj = obj[next_cmd];
			if (typeof(next_obj) == "undefined") {
				//console.error(""+obj+" has no attribute "+next_cmd);
				return fallback_return;
			}
			return get(cmd, next_obj, fallback_return);
		}
		//console.error('Failed to aquire ');
		return fallback_return;
	}
	function get_func(cmd, obj) {return get(cmd, obj, function(){})}
	function get_dict(cmd, obj) {return get(cmd, obj, {})}
	
	function run_funcs(data) {
		//console.log('message', data);
		if (_.isArray(data)) {
			_.each(data, function(element, index, list){
				run_funcs(element);
			});
		}
		if (_.has(data, 'func')) {
			var f = get_func(data.func);
			if (typeof(f) == "function") {
				f(data);
			}
			else {
				console.error(""+data.func+" could not be located");
			}
			
		}
	}
	
	external.functools = {
		get: get,
		get_func: get_func,
		get_dict: get_dict,
		run_funcs: run_funcs,
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
		},
		is_data: function(src) {
			return src && src.match(/\.(json|xml|csv)$/);
		},
	};
}(utils));

