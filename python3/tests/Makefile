.PHONY: help
help:
	# test
	# install
	# run


# Install ----------------------------------------------------------------------

.PHONY: install
install: node_modules/phantomjs env/selenium env/bin/py.test js/underscore-min.js js/jquery-min.js js/websocket.js js/utils.js

node_modules/phantomjs:
	# This only installs PhantomJS 1.9.8
	# We require >=2.0.0 for the modern version of RFC 6455 rather than hixie-76
	# http://stackoverflow.com/questions/9680820/how-to-know-which-websocket-version-the-client-uses
	# https://github.com/Medium/phantomjs/issues/288
	npm install phantomjs@2.0.0

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
	cd js && curl https://raw.githubusercontent.com/jashkenas/underscore/master/underscore-min.js --compressed -O

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
	env/bin/py.test test_*
	pkill -9 phantomjs  # fuck you phantomjs! why wont you close


# Clean ------------------------------------------------------------------------

.PHONY: clean	
clean:
	rm -rf env
	rm -rf node_modules
	rm -rf js
	rm ghostdriver.log
