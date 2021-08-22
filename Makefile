build: fix mypy

req:
	pip install -r requirements.txt

black:
	black .

isort:
	isort .

flake8:
	flake8

mypy:
	mypy .

fix: black isort flake8
