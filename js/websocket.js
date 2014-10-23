// Websocket -------------------------------

// Authenicate client with session key on socket connect
function _websocket_first_message_auth(socket, session_cookie_name) {
	session_cookie_name = session_cookie_name || "_session";
	socket.send(document.cookie.match(/session_cookie_name=([^;\s]+)/)[1]);  // Um? this needs to be a variable
}



function WebSocketReconnect(onopen, onmessage, options) {
	console.debug("WebSocketReconnect", options);
	
	//default options
	options = _.extend({
		hostname: location.hostname,
		port: 9873,
		format: 'json',
		auth: function(socket) {},
		disconnected_retry_interval: 5,
		disconnected_class: 'websocket_disconnected',
	}, options) 
	
	$('body').addClass('websocket_disconnected');

	// When the socket is not connected this will be the dummy underlying send method
	function send_disconnected(msg) {
		log.warn("WebSocket.send called when disconnected", msg);
		return false;
	}

	// Wrapper will be returned and have a consistant 'send' method
	// as the underlying socket object is recreated/change on disconnect,
	// the 'send' method will always be avalable.
	var websocket_wrapper = {
		send: send_disconnected,
		retry_interval: null,
	};
	
	// Internal method
	function _init() {__init(onopen, onmessage, options);}
	function __init(onopen, onmessage, options) {
		var socket = new WebSocket("ws://"+options.hostname+":"+options.port+"/");
	
		socket.onopen = function() {
			console.debug("WebSocketReconnect: Connected");
			options.auth(socket);  // optional function to auth once connected
			$('body').removeClass(options.disconnected_class);
			if (websocket_wrapper.retry_interval) {
				clearInterval(websocket_wrapper.retry_interval);
				websocket_wrapper.retry_interval = null;
			}
			onopen();
		};
		socket.onclose  = function() {
			console.debug("WebSocketReconnect: Disconnected");
			socket = null;
			websocket_wrapper.send = send_disconnected;
			$('body').addClass(options.disconnected_class);
			if (!websocket_wrapper.retry_interval) {
				websocket_wrapper.retry_interval = setInterval(_init, options.disconnected_retry_interval * 1000);
			}
		};
		socket.onmessage = function(msg) {
			msg = msg.data;
			if (options.format=='json') {
				msg = JSON.parse(msg);
			}
			onmessage(msg);
		};
		
		function socket_send(msg) {
			if (options.format=='json') {
				msg = JSON.stringify(msg)+"\n";
			}
			return socket.send(msg);
		}
		
		websocket_wrapper.send = socket_send;
	}
	_init();
	
	return websocket_wrapper;
}
