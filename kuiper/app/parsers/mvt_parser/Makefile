PWD = $(shell pwd)

clean:
	rm -rf $(PWD)/build $(PWD)/dist $(PWD)/mvt.egg-info

dist:
	python3 setup.py sdist bdist_wheel

upload:
	python3 -m twine upload dist/*
