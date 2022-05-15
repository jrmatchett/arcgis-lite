"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='arcgis_lite',
    version='0.1.2',
    description='Lightweight implementation of the ArcGIS REST API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='J. R. Matchett',
    author_email='jrmatchett@me.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: GIS'
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[],
    extras_requires={
        'geodata': ['geopandas']
    },
    python_requires='~=3.7',
    project_urls={
        'Bug Reports': 'https://github.com/jrmatchett/arcgis-lite/issues',
        'Source': 'https://github.com/jrmatchett/arcgis-lite',
    }
)
