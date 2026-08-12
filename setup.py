#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

LONG_DESCRIPTION = open('README.md').read()

VERSION = (0, 38, '0')

# pragma: no cover
if VERSION[-1] != "final":
    project_version = '.'.join(map(str, VERSION))
else:
    # pragma: no cover
    project_version = '.'.join(map(str, VERSION[:-1]))

setup(
    name="django-psa",
    version=project_version,
    description='Django app for working with '
                'various PSA REST API. Defines '
                'models (tickets, companies, '
                'etc.) and callbacks. ',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords='django connectwise halo autotask rest api python',
    packages=find_packages(),
    author='TopLeft Technologies Ltd.',
    author_email='sam@topleft.team',
    url="https://github.com/topleft-team/django-psa",
    include_package_data=True,
    license='MIT',
    python_requires='>=3.12',
    install_requires=[
        'requests',
        'django>=4.2,<7.0',
        'setuptools',
        'python-dateutil',
        'retrying',
        'redis',
        'django-extensions',
        'django-model-utils',
        'django-braces',
    ],
    # Django likes to inspect apps for /migrations directories, and can't if
    # package is installed as an egg. zip_safe=False disables installation as
    # an egg.
    zip_safe=False,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.2',
        'Framework :: Django :: 6.0',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Development Status :: 3 - Alpha',
    ],
)
