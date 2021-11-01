# Lightweight Implementation of the ArcGIS REST API

This package contains tools for working with the [ArcGIS REST API](https://developers.arcgis.com/rest/).
It is primarily focused on managing data in hosted feature layers and is designed to be minimal in size,
require no external dependencies for basic functionality, and used in memory-limited computing environments.
Feature layer query results can optionally be converted to a [GeoPandas](https://geopandas.org/) `GeoDataFrame`
for more sophisticated analyses. For a more extensive set of tools, please see Esri's
[ArcGIS API for Python](https://developers.arcgis.com/python/).

## Installation

* Install with pip using `pip install git+https://github.com/jrmatchett/arcgis-lite.git`, or by downloading
the source code and running `python setup.py install` from the package's root directory.

## Modules

* `gis` provides classes for connecting to ArcGIS Online and ArcGIS Enterprise Portal.

* `features` provides classes and methods for querying, creating, updating, and deleting features in a hosted feature layer.
