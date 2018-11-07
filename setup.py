#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pressurecooker
from setuptools import setup, find_packages


with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    "beautifulsoup4>=4.6.3",
    "ffmpy>=0.2.2",
    "le-utils>=0.1.14",
    "matplotlib==2.0.0",
    "numpy==1.12.1",
    "Pillow>=3.3.1",
    "youtube-dl>=2018.11.7",
    "Wand==0.4.4",
    "webvtt-py>=0.4.2",
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pressurecooker',
    version=pressurecooker.__version__,
    description="A collection of utilities for media processing.",
    long_description=readme + '\n\n',
    author="Learning Equality",
    author_email='dev@learningequality.org',
    url='https://github.com/learningequality/pressurecooker',
    packages=find_packages(),
    package_dir={'presurecooker':
                 'presurecooker'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords=['media', 'mediaprocessing', 'video',
              'compression', 'thumbnails', 'pressurecooker'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
