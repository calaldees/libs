// Websocket -------------------------------
var socket_retry_interval = null;
function setup_websocket(on_connect, on_message, options) {
	console.log("setup_websocket");
	
	//default options
	//  port
	//  first_message_session_id_auth
	
	$('body').addClass('websocket_disconnected');

	var socket = new WebSocket("ws://"+location.hostname+":"+options.port+"/");

	socket.onopen = function(){ // Authenicate client with session key on socket connect
		var cookie = document.cookie.match(/_session=(.+?)(\;|\b)/);  // TODO - replace with use of settings['session_key'] or server could just use the actual http-header
		if (cookie) {
			socket.send(cookie[1]);
		}
		else {
			console.warn("No session cookie to authenticate websocket write access");
		}
		$('body').removeClass('websocket_disconnected');
		if (socket_retry_interval) {
			clearInterval(socket_retry_interval);
			socket_retry_interval = null;
		}
		console.log("Websocket: Connected");
		on_connect();
	};
	socket.onclose  = function() {
		socket = null;
		$('body').addClass('websocket_disconnected');
		console.log("Websocket: Disconnected");
		if (!socket_retry_interval) {
			socket_retry_interval = setInterval(function(){setup_websocket(on_connect, on_message)}, battlescape.data.settings.websocket.disconnected_retry_interval * 1000);
		}
	};
	socket.onmessage = function(msg) {
		var data = JSON.parse(msg.data);
		on_message(data);
	};
}
