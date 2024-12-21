

all:
	@echo woof

freeze:
	pip freeze >requirements.txt

venv:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

install-venv:
	pip install -r requirements.txt
