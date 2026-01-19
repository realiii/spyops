# Spatial Python Operations (SPyOps)

Spatial Python Operations (SPyOps) is an evolving collection of GIS Analysis, Spatial Statistics, Spatial 
Operations, and Spatial Data Management functionality built on top of the OGC GeoPackage format.  The end goal is 
to provide open source access to enterprise level spatial analysis and data management functionality.

For details on OGC GeoPackages, please see the [OGC web page](http://www.geopackage.org/) and for a short
introduction to the way in which GeoPackages are handled in `spyops` refer to the
[`fudgeo` package](https://pypi.org/project/fudgeo/) 


## Installation

`spyops` is available from the [Python Package Index](https://pypi.org/project/spyops/).


## Python Compatibility

The `spyops` library is compatible with Python 3.11 to 3.14.  Developed and 
tested on **macOS** and **Windows**, should be fine on **Linux** too.


## License

MIT


## Current Limitations
* Feature classes used in extract or overlay operations must be in the same coordinate reference system


## Release History

### v0.0.1
* internal release
* added `clip` (Analysis - Extract)
* added `select` (Analysis - Extract) and aliased as `extract_features`
* added `split` (Analysis - Extract)
* added `split_by_attributes` (Analysis - Extract)
* added `table_select` (Analysis - Extract) and aliased as `extract_rows`
* added `erase` (Analysis - Overlay)
* added `intersect` (Analysis - Overlay)
* added `symmetrical_difference` (Analysis - Overlay)
* Settings support for `overwrite`
* Settings support for dimensions `xy_tolerance`, `output_m_option`, `output_z_option`, and `z_value`  
* Settings support for workspace `current_workspace`, and `scratch_workspace`
