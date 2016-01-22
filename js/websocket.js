// Websocket -------------------------------

// Authenicate client with session key on socket connect
function _websocket_first_message_auth(socket, session_cookie_name) {
	session_cookie_name = session_cookie_name || "_session";
	socket.send(document.cookie.match(/session_cookie_name=([^;\s]+)/)[1]);  // Um? this needs to be a variable
}


function SocketReconnect(options, parent) {
	options = _.extend({
		title: 'SocketReconnect',
		hostname: location.hostname,
		port: 9873,
		disconnected_retry_interval: 5,
	}, options)
	parent = _.extend({
		encode: function(msg){return msg;},
		decode: function(msg){return msg;},
		onmessage: function(msg){},
		onconnected: function(){},
		ondisconnected: function(){},
	}, parent);
	
	parent.ondisconnected();

	// When the socket is not connected this will be the dummy underlying send method
	function send_disconnected(msg) {
		log.warn(options.title+".send called when disconnected", msg);
		return false;
	}

	// Wrapper will be returned and have a consistant 'send' method
	// as the underlying socket object is recreated/change on disconnect,
	// the 'send' method will always be avalable.
	var exported = {
		send: send_disconnected,
		retry_interval: null,
	};
	
	
	function _init() {
		var socket = new WebSocket("ws://"+options.hostname+":"+options.port+"/");

		socket.onopen = function() {
			//console.debug(options.title+": onopen");
			if (exported.retry_interval) {
				clearInterval(exported.retry_interval);
				exported.retry_interval = null;
			}
			parent.onconnected();
		};
		socket.onclose  = function() {
			//console.debug(options.title+": onclose");
			socket = null;
			exported.send = send_disconnected;
			if (!exported.retry_interval) {
				exported.retry_interval = setInterval(_init, options.disconnected_retry_interval * 1000);
			}
			parent.ondisconnected();
		};
		socket.onmessage = function(msg) {
			_.each(_.filter(msg.data.split('\n'), function(element){return element;}), function(element, index, list){
				parent.onmessage(element);
			});
		};
		
		function socket_send(msg) {
			return socket.send(parent.encode(msg)+'\n');
		}
		
		exported.send = socket_send;
	}
	_init();
	
	return exported;
}



function JsonSocketReconnect(options, parent) {
	options = _.extend({
		title: 'JsonSocketReconnect',
	}, options);
	
	parent = _.extend({
		onmessage: function(msg){},
		onconnected: function(){},
		ondisconnected: function(){},
	}, parent);
	
	var me = _.extend({}, parent, {
		encode: function(msg){return JSON.stringify(msg);},
		decode: function(msg){return JSON.parse(msg);},
		onmessage: function(msg){parent.onmessage(me.decode(msg));},
		onconnected: function(){parent.onconnected();},
		ondisconnected: function(){parent.ondisconnected();},
	});
	
	var exported = SocketReconnect(options, me);
	
	return exported;
}


function SubscriptionSocketReconnect(options, parent) {
	options = _.extend({
		title: 'SubscriptionSocketReconnect',
		subscriptions: [],
	}, options);

	parent = _.extend({
		onmessage: function(msg){console.debug(options.title+': message: '+msg);},
		onconnected: function(){console.debug(options.title+': connected');},
		ondisconnected: function(){console.debug(options.title+': disconnected');},
	}, parent);
	
	var me = _.extend({}, parent, {
		onmessage: function(msg){
			if (msg && msg.action == 'message' && msg.data.length>0) {
				_.each(msg.data, function(element, index, list){
					parent.onmessage(element);
				});
			}
		},
		onconnected: function(){
			if (!_.isEmpty(options.subscriptions)) {
				send_subscriptions();
			}
			parent.onconnected();
		},
		ondisconnected: function(){
			parent.ondisconnected();
		},
	});
	
	var exported = JsonSocketReconnect(options, me);
	
	send_subscriptions = function() {
		exported.send({
			action: 'subscribe',
			data: options.subscriptions,
		});
	};
	
	// Exports
	exported = _.extend(exported, {
		update_subscriptions: function(){
			// TODO? This is broken!
			//subscriptions.clear()
			options.subscriptions = _.toArray(arguments); //Update existing array rather than replace?  _.union(options.subscriptions,
			send_subscriptions();
		},
		send_message_array: function(messages){
			exported.send({
				action: 'message',
				data: messages,
			});
		},
		send_message: function(){
			exported.send({
				action: 'message',
				data: _.toArray(arguments),
			});
		},
	});
	
	//delete exported.send;  // This is broken .. even when copying the entire exported object. Need more information about delete.
	
	return exported;
}
