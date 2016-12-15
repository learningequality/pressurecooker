clean:
	rm -r dist/ || true

dist:
	python setup.py bdist_wheel --universal

release_staging: dist
	twine upload -s --sign-with gpg2 dist/*py2.py3-none-any.whl -r pypitest

release: dist
	# make sure we upload the universal whl file
	twine upload -s --sign-with gpg2 dist/*py2.py3-none-any.whl