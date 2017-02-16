import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-channels-jsonrpc',
    version='1.1.2',
    packages=find_packages(),
    install_requires=[
          'channels',
      ],
    include_package_data=True,
    license='MIT License',
    description='A JSON-RPC implementation for Django channels consumer.',
    long_description='Works with django channels. See README on gihub repo',
    url='https://github.com/millerf/django-channels-jsonrpc/',
    author='Fabien Millerand - MILLER/f',
    author_email='fab@millerf.com',
    test_suite='channels_jsonrpc.tests.tests',
    tests_require=['django', 'channels'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ],
)