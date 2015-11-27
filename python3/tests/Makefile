.PHONY: help
help:
	# test
	# install
	# run


# Install ----------------------------------------------------------------------

.PHONY: install
install: node_modules/phantom env/selenium env/bin/py.test js/underscore-min.js js/websocket.js

node_modules/phantom:
	npm install phantom

env:
	virtualenv --no-site-packages -p python3 env
	env/bin/pip3 install --upgrade pip

env/selenium: env
	env/bin/pip3 install selenium
	
env/bin/py.test:
	env/bin/pip3 install pytest

js:
	mkdir js

js/underscore-min.js: js
	cd js && curl https://raw.github.com/jashkenas/underscore/master/underscore-min.js --compressed -O

js/jquery-min.js: js
	cd js && curl http://code.jquery.com/jquery-2.1.4.min.js --compressed -o jquery-min.js

js/websocket.js: js
	ln -s ../../../js/websocket.js js/websocket.js

js/utils.js: js
	ln -s ../../../js/utils.js js/utils.js


# Tests ------------------------------------------------------------------------

test_social_login:
	/Users/allan.callaghan/code/personal/KaraKara/website/env/bin/py.test -q --pdb ./tests/test_social_login.py

test_socket:
	env/bin/py.test test_subscription_socket.py


# Clean ------------------------------------------------------------------------

.PHONY: clean	
clean:
	rm -rf env
	rm -rf node_modules
	rm -rf js
	rm ghostdriver.log
