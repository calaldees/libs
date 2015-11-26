.PHONY: help
help:
	# test
	# install
	# run


# Install ----------------------------------------------------------------------

.PHONY: install
install: node_modules/phantom env/selenium env/bin/py.test

node_modules/phantom:
	npm install phantom

env:
	virtualenv --no-site-packages -p python3 env
	env/bin/pip3 install --upgrade pip

env/selenium: env
	env/bin/pip3 install selenium
	
env/bin/py.test:
	env/bin/pip3 install pytest
	

# Tests ------------------------------------------------------------------------

test_social_login:
	/Users/allan.callaghan/code/personal/KaraKara/website/env/bin/py.test -q --pdb ./tests/test_social_login.py

test_multisocket:
	env/bin/py.test --pdb test_multisocket.py


# Clean ------------------------------------------------------------------------

.PHONY: clean	
clean:
	rm -rf env
	rm -rf node_modules
	rm ghostdriver.log