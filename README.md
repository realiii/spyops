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

## Analysis
### Extract
#### `clip`
Extracts features using the features of a polygon feature class. Extracted
features are cut along the edges of the operator polygons.

#### `select`
Select features from a feature class using a where clause (optional) and
write results to a target feature class.

#### `split`
Extracts features for each polygon in the operator feature class and uses
values from the specified field to name the output feature classes.

#### `split_by_attributes`
Split an input table or feature class by groups of attributes.

#### `table_select`
Select rows from a table using a where clause (optional) and 
write results to a target table.

### Overlay
#### `erase`
Removes the portion of the input feature class that overlaps with the
operator feature class.

#### `intersect`
Extracts the portion of the input feature class that overlaps with the
operator feature class.  Optionally, extends the output feature class
with attributes from the operator feature class.

### `symmetrical_difference`
Extracts the portion of the input feature class and operator feature class
that do not intersect.  Optionally, extends the output feature class
with attributes from the operator feature class.

## Settings
Setting can be used globally or on a specific function call using context managers.

### General
The default for `spyops` is to avoid overwriting existing GeoPackages, Feature Classes, and Tables.  

```python
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting

# set overwrite globally
ANALYSIS_SETTINGS.overwrite = True

# set overwrite on a specific function call
with Swap(Setting.OVERWRITE, True):
    result = clip(source, operator=operator, target=target)
```

### Dimension
In the dimension category, the `xy_tolerance` setting can be used to specify a tolerance value for XY coordinates.
The `output_m_option` and `output_z_option` settings can be used to control how M and Z values are handled in the 
output feature class based in the inputs. The `z_value` setting can be used to specify a constant Z 
value for the output feature class when z values are present or specified for output.  The `z_value` will only be used
to replace NaN values.

The default for `xy_tolerance` is `None`, for the most part it is recommended to use the default unless you have a 
specific reason to change it, for example, if dealing with some dirty data or need to downgrade the data fidelity.
The units of the tolerance value are the same as the coordinate reference system.

```python
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

# set on the function call as an argument
result = clip(source, operator=operator, target=target, xy_tolerance=0.001)

# or set globally (not recommended)
ANALYSIS_SETTINGS.xy_tolerance = 0.001  # in units of the coordinate reference system

# or set via context during a function call
with Swap(Setting.XY_TOLERANCE, 0.001):
    result = clip(source, operator=operator, target=target)
```

The defaults for `output_m_option` and `output_z_option` are `OutputMOption.SAME` and `OutputZOption.SAME` respectively.
`SAME` means that if an input feature class has M or Z values then the output feature class will have the same values.
Other options are `OutputMOption.ENABLED` / `OutputZOption.ENABLED`, which will enable M and Z values in the output 
feature class regardless of the M and Z settings in the input feature classes.  Similarly 
`OutputMOption.DISABLED` / `OutputZOption.DISABLED` will remove M and Z values from the output feature class.

```python
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap
from spyops.environment.enumeration import OutputMOption, OutputZOption

# set globally (disable to force into 2D)
ANALYSIS_SETTINGS.output_m_option = OutputMOption.DISABLED
ANALYSIS_SETTINGS.output_z_option = OutputZOption.DISABLED

# or set via context during a function call
with (Swap(Setting.OUTPUT_M_OPTION, OutputMOption.DISABLED), 
      Swap(Setting.OUTPUT_Z_OPTION, OutputZOption.DISABLED)):
    result = clip(source, operator=operator, target=target)
```

### Workspace
In the workspace category are the `current_workspace` and `scratch_workspace` settings can be used to specify 
the current workspace for analysis operations. These settings allow you to control where intermediate and final 
results are stored during analysis tasks.  The main benefit of specifying a `current_workspace` is that it allows 
you use strings to specify feature classes and tables instead of fully hydrated `FeatureClass` and `Table` objects.
The `scratch_workspace` setting is used to specify a workspace for temporary results.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

# fully hydrated objects
gpkg = GeoPackage('/some/data/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['index_a']
target = FeatureClass(geopackage=gpkg, name='clipped_hydro_a')
result = clip(source, operator=operator, target=target)

# use strings hydrated objects
gpkg = GeoPackage('/some/data/ntdb_zm.gpkg')
target = FeatureClass(geopackage=gpkg, name='clipped_hydro_a')
with Swap(Setting.CURRENT_WORKSPACE, gpkg):
    result = clip('hydro_a', operator='index_a', target=target)
```

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
