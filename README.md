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

## Analysis
### Extract
#### `clip`
Extracts features using the features of a polygon feature class. Extracted
features are cut along the edges of the operator polygons.

```python
from fudgeo import GeoPackage, FeatureClass, MemoryGeoPackage
from spyops.analysis.extract import clip

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
mem = MemoryGeoPackage.create()
source = gpkg['hydro_a']
operator = gpkg['index_a'].copy(
    name='index_082J16_a', where_clause="""DATANAME = '082J16'""", geopackage=mem)
target = FeatureClass(geopackage=gpkg, name='clipped_hydro_a')

fc = clip(source, operator=operator, target=target)
```

#### `select`
Select features from a feature class using a where clause (optional) and
write results to a target feature class.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.analysis.extract import select

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['structures_a']
target = FeatureClass(geopackage=gpkg, name='selected_structures_a')

fc = select(source, target=target, where="""ENTITY = 'Golf course' AND VALIDATE = 1987""")
```

#### `split`
Extracts features for each polygon in the operator feature class and uses
values from the specified field to name the output feature classes.

```python
from fudgeo import GeoPackage
from spyops.analysis.extract import split

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['index_a']
output = GeoPackage.create('/another/path/hydro_split.gpkg')

fcs = split(source, operator=operator, field='DATANAME', geopackage=output)
```

#### `split_by_attributes`
Split an input table or feature class by groups of attributes.

```python
from fudgeo import GeoPackage
from spyops.analysis.extract import split_by_attributes

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['transmission_l']
output = GeoPackage.create('/another/path/transmission_split.gpkg')

fcs = split_by_attributes(source, group_fields=('ENTITY', 'CODE'), geopackage=output)
```

#### `table_select`
Select rows from a table using a where clause (optional) and 
write results to a target table.

```python
from fudgeo import GeoPackage, Table
from spyops.analysis.extract import table_select

gpkg = GeoPackage('/some/path/world_tables.gpkg')
source = gpkg['cities']
target = Table(geopackage=gpkg, name='cities_peru')

tbl = table_select(source, target=target, where_clause="""FIPS_CNTRY = 'PE'""")
```


### Overlay
#### `erase`
Removes the portion of the input feature class that overlaps with the
operator feature class.

```python
from fudgeo import GeoPackage, FeatureClass, MemoryGeoPackage
from spyops.analysis.overlay import erase

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
mem = MemoryGeoPackage.create()
source = gpkg['hydro_a']
operator = gpkg['index_a'].copy(
    name='index_082J16_a', where_clause="""DATANAME = '082J16'""", geopackage=mem)
target = FeatureClass(geopackage=gpkg, name='erased_hydro_a')

fc = erase(source, operator=operator, target=target)
```

#### `intersect`
Extracts the portion of the input feature class that overlaps with the
operator feature class.  Optionally, extends the output feature class
with attributes from the operator feature class.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.analysis.overlay import intersect
from spyops.shared.enumeration import AlgorithmOption, AttributeOption, OutputTypeOption

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['structures_a']

# all attributes and output will be polygon
target = FeatureClass(geopackage=gpkg, name='sh_intersection_a')
fc = intersect(source, operator=operator, target=target)

# only fid and output will be points for the intersections
target = FeatureClass(geopackage=gpkg, name='sh_intersection_only_pt')
fc = intersect(source, operator=operator, target=target,
               attribute_option=AttributeOption.ONLY_FID,
               output_option=OutputTypeOption.POINT)

# algorithm options, applies to polygon inputs (source / operator)
target = FeatureClass(geopackage=gpkg, name='sh_intersection_classic_pt')
fc = intersect(source, operator=operator, target=target,
               algorithm_option=AlgorithmOption.CLASSIC)
```

#### `symmetrical_difference`
Extracts the portion of the input feature class and operator feature class
that do not intersect.  Optionally, extends the output feature class
with attributes from the operator feature class.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.analysis.overlay import symmetrical_difference
from spyops.shared.enumeration import AlgorithmOption, AttributeOption

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['structures_a']

# inputs (source / operator) must have same geometry type (e.g. polygon)
target = FeatureClass(geopackage=gpkg, name='sh_sym_diff_a')
fc = symmetrical_difference(source, operator=operator, target=target)

# all attributes except the original FID columns will be copied to the output
target = FeatureClass(geopackage=gpkg, name='sh_sym_diff_sans_a')
fc = symmetrical_difference(source, operator=operator, target=target, 
                            attribute_option=AttributeOption.SANS_FID)

# algorithm options, applies to polygon inputs (source / operator)
target = FeatureClass(geopackage=gpkg, name='sh_sym_diff_classic_a')
fc = symmetrical_difference(source, operator=operator, target=target, 
                            algorithm_option=AlgorithmOption.CLASSIC)
```

#### `union`
Combines the geometries from the source and operator feature classes into
a single output feature class. The output contains all features from both
inputs, with overlapping areas split into separate features. Optionally,
extends the output feature class with attributes from the operator feature
class. Only polygon geometry types are supported.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.analysis.overlay import union
from spyops.shared.enumeration import AlgorithmOption, AttributeOption

gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['structures_a']

# inputs (source / operator) must have polygon geometry
target = FeatureClass(geopackage=gpkg, name='sh_union_a')
fc = union(source, operator=operator, target=target)

# all attributes except the original FID columns will be copied to the output
target = FeatureClass(geopackage=gpkg, name='sh_union_sans_a')
fc = union(source, operator=operator, target=target, 
           attribute_option=AttributeOption.SANS_FID)

# algorithm options, applies to polygon inputs (source / operator)
target = FeatureClass(geopackage=gpkg, name='sh_union_classic_a')
fc = union(source, operator=operator, target=target, 
           algorithm_option=AlgorithmOption.CLASSIC)
```

## Management
### Features
#### `multipart_to_singlepart`
Generates a feature class with single-part geometries by splitting
multipart input features.  A column named ORIG_FID is added to the output
feature class to track the original feature identifier.

```python
from fudgeo import GeoPackage, FeatureClass
from spyops.management.features import multipart_to_singlepart
from spyops.shared.enumeration import AlgorithmOption, AttributeOption

gpkg = GeoPackage('/some/path/ntdb_zm_small.gpkg')
source = gpkg['structures_zm_ma']

# output will be single-part features
target = FeatureClass(geopackage=gpkg, name='structures_explode_zm_a')
fc = multipart_to_singlepart(source, target=target)
assert source.is_multi_part is True
assert fc.is_multi_part is False
```


## Settings
Setting can be used globally or on a specific function call using context managers.

### General
The default for `spyops` is to avoid overwriting existing GeoPackages, Feature Classes, and Tables.  

```python
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

# set overwrite globally
ANALYSIS_SETTINGS.overwrite = True

# set overwrite on a specific function call
with Swap(Setting.OVERWRITE, True):
    fc = clip(source, operator=operator, target=target)
```

### Coordinates
#### Output Coordinate System
The `output_coordinate_system` setting can be used to specify the coordinate reference system (CRS) for the `target`
feature class.  The default is `None`, which means that the `target` feature class will have the CRS of the 
`source` feature class.

```python
from pyproj import CRS
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

# set globally, can be set using a pyproj CRS, 
# fudgeo SpatialReferenceSystem object, or fudgeo FeatureClass object
ANALYSIS_SETTINGS.output_coordinate_system = CRS(4326) 
ANALYSIS_SETTINGS.output_coordinate_system = operator.spatial_reference_system 
ANALYSIS_SETTINGS.output_coordinate_system = source

# can clear the setting by using None
ANALYSIS_SETTINGS.output_coordinate_system = None

# or set via context during a function call
with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, CRS(4326)):
    fc = clip(source, operator=operator, target=target)

# use None to ignore the current output_coordinate_system setting
with Swap(Setting.OUTPUT_COORDINATE_SYSTEM, None):
    fc = clip(source, operator=operator, target=target)
```

If the `source` and / or `operator` feature class(es) have different Spatial Reference Systems and 
`geographic_transformations` (see below) are not specified then a "best guess" will be made as to the transformation
needed to transform the `source` and / or `operator` feature class(es).

#### Geographic Transformations
The `geographic_transformations` setting can be used to specify transformations between coordinate systems and / or 
datums.  When transforming spatial data having different datums it is essential to use the grid files to ensure that 
the datum transformations are as accurate as possible.

Use the `pyproj` [sync](https://pyproj4.github.io/pyproj/stable/cli.html#Sub-commands)
to download grid files for geographic transformations.

```commandline
pyproj sync --verbose --all --include-already-downloaded --target-directory /Users/username/folder/grids
```

Once downloaded the grid files can be specified for use by `spyops` using the `configure_grids` function.

```python
from spyops.crs.util import configure_grids

configure_grids('/Users/username/folder/grids')
```

Transformations can be specified `geographic_transformations` setting, transformations that apply to the 
Spatial Reference Systems of the `source`, `operator` feature classes and / or the `output_coordinate_system` will be
prefered when performing coordinate transformations.

```python
from pyproj import CRS
from spyops.analysis.extract import clip
from spyops.crs.transform import get_transforms
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

output_crs = CRS(4326)

# specify transformations for the source to the output coordinate system
# this is just an example, in practice more likley to check the description
# of the transformation to ensure a specific transformation is being used
transformation = get_transforms(source, output_crs)
if transformation.is_required:
    if transformation.best:
        xforms = [transformation.best]
    else:
        xforms = [o.transformer for o in transformation.options]
else:
    xforms = None
with (Swap(Setting.OUTPUT_COORDINATE_SYSTEM, output_crs),
      Swap(Setting.GEOGRAPHIC_TRANSFORMATIONS, xforms)):
    fc = clip(source, operator=operator, target=target)
```

If no `geographic_transformations` are specified then a "best guess" will be made as to the transformation needed.
The "best guess" is "best" based on `pyroj` determiniation and if this does not exist (for example, a grid file is 
missing) then the first transformation in the list of available transformations is used.


#### XY Tolerance
In the dimension category, the `xy_tolerance` setting can be used to specify a tolerance value for XY coordinates.
The default for `xy_tolerance` is `None`, for the most part it is recommended to use the default unless you have a 
specific reason to change it, for example, if dealing with some dirty data or need to downgrade the data fidelity.

```python
from spyops.analysis.extract import clip
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

# set on the function call as an argument in units of the source coordinate reference system
fc = clip(source, operator=operator, target=target, xy_tolerance=0.001)

# or set globally (not recommended) in units of the source coordinate reference system
ANALYSIS_SETTINGS.xy_tolerance = 0.001 

# or set via context during a function call
with Swap(Setting.XY_TOLERANCE, 0.001):
    fc = clip(source, operator=operator, target=target)
```

The units of the `xy_tolerance` are interpreted as being the same as the coordinate reference system of the `source` 
feature class in the function call.  In situatations where the `source` and / or `operator` units differ from one 
another or are different from the `output_coordinate_system` units, the `xy_tolerance` will be converted to the correct
units as based on the CRS of the `target` (either from `source` or from `output_coordinate_system`).
Be cautious when working with a mixture of different coordinate reference systems that have different units 
(e.g. metres, feet, US Survey Feet, decimal degrees, etc.).

#### M/Z Options
The `output_m_option` and `output_z_option` settings can be used to control how M and Z values are handled in the 
output feature class based in the inputs. The `z_value` setting can be used to specify a constant Z 
value for the output feature class when z values are present or specified for output.  The `z_value` will only be used
to replace NaN values.

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
    fc = clip(source, operator=operator, target=target)
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
gpkg = GeoPackage('/some/path/ntdb_zm.gpkg')
source = gpkg['hydro_a']
operator = gpkg['index_a']
target = FeatureClass(geopackage=gpkg, name='clipped_hydro_a')
fc = clip(source, operator=operator, target=target)

# use strings instead of hydrated objects
gpkg = GeoPackage('/some/data/ntdb_zm.gpkg')
target = FeatureClass(geopackage=gpkg, name='clipped_hydro_a')
with Swap(Setting.CURRENT_WORKSPACE, gpkg):
    fc = clip('hydro_a', operator='index_a', target=target)
```

The `scratch_folder` setting can be used to specify a temporary folder.  Not presently used by any internal operations.

```python
from pathlib import Path
from spyops.environment import ANALYSIS_SETTINGS, Setting
from spyops.environment.context import Swap

path = Path('/some/data')
with Swap(Setting.SCRATCH_FOLDER, path):
    ...
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
* added `union` (Analysis - Overlay)
* added `multipart_to_singlepart` (Management - Features) and alias as `explode`
* Settings support for `overwrite`
* Settings support for dimensions `xy_tolerance`, `output_m_option`, `output_z_option`, and `z_value`  
* Settings support for workspace `current_workspace`, `scratch_workspace`, and `scratch_folder`
* Settings support for coordinates `output_coordinate_system` and `geographic_transformations`
