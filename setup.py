# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='gsocketpool',
    version='0.1.5',
    description='A simple connection pool for gevent',
    author='Studio Ousia',
    author_email='ikuya@ousia.jp',
    url='http://github.com/studio-ousia/gsocketpool',
    packages=find_packages(),
    license=open('LICENSE').read(),
    include_package_data=True,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ),
    install_requires=[
        'gevent',
    ],
    tests_require=[
        'nose',
        'mock',
    ],
    test_suite = 'nose.collector'
)
