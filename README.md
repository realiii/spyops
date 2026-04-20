# Spatial Python Operations (SPyOps)

Spatial Python Operations (SPyOps) is an evolving collection of GIS Analysis, Spatial Statistics, Spatial 
Operations, and Spatial Data Management functionality built on top of the OGC GeoPackage format.  The end goal is 
to provide open source access to enterprise level spatial analysis and data management functionality.

For a short introduction to the way in which GeoPackages are handled in `spyops` refer to
[`fudgeo`](https://pypi.org/project/fudgeo/) 


## Installation

`spyops` is available from the [Python Package Index](https://pypi.org/project/spyops/).


## Python Compatibility

The `spyops` library is compatible with Python 3.12 to 3.14.  Developed and 
tested on **macOS** and **Windows**, should be fine on **Linux** too.


## License

MIT


## Capabilities
- [Analysis - Extract](https://github.com/realiii/spyops/wiki/Analysis#extract)
- [Analysis - Overlay](https://github.com/realiii/spyops/wiki/Analysis#overlay)
- [Analysis - Proximity](https://github.com/realiii/spyops/wiki/Analysis#proximity)
- [Management - Features](https://github.com/realiii/spyops/wiki/Data-Management#features)
- [Management - Feature Class](https://github.com/realiii/spyops/wiki/Data-Management#feature-class)
- [Management - Fields](https://github.com/realiii/spyops/wiki/Data-Management#fields)
- [Management - General](https://github.com/realiii/spyops/wiki/Data-Management#general)
- [Management - Generalization](https://github.com/realiii/spyops/wiki/Data-Management#generalization)
- [Management - Indexes](https://github.com/realiii/spyops/wiki/Data-Management#indexes)
- [Management - Projections and Transformations](https://github.com/realiii/spyops/wiki/Data-Management#projections-and-transformations)
- [Management - Table](https://github.com/realiii/spyops/wiki/Data-Management#table)
- [Settings](https://github.com/realiii/spyops/wiki/Settings)


## Release History
### v0.0.1
- internal release
- added `clip` (Analysis - Extract)
- added `select` (Analysis - Extract) and aliased as `extract_features`
- added `split` (Analysis - Extract)
- added `split_by_attributes` (Analysis - Extract)
- added `table_select` (Analysis - Extract) and aliased as `extract_rows`
- added `erase` (Analysis - Overlay)
- added `intersect` (Analysis - Overlay)
- added `symmetrical_difference` (Analysis - Overlay)
- added `union` (Analysis - Overlay)
- added `buffer` (Analysis - Proximity)
- added `multiple_buffer` (Analysis - Proximity)
- added `create_feature_class` (Management - Feature Class)
- added `recalculate_feature_class_extent` (Management - Feature Class)
- added `add_xy_coordinates` (Management - Features)
- added `calculate_geometry_attributes` (Management - Features)
- added `check_geometry` (Management - Features)
- added `copy_features` (Management - Features)
- added `delete_features` (Management - Features)
- added `feature_envelope_to_polygon` (Management - Features)
- added `feature_to_point` (Management - Features)
- added `feature_vertices_to_points` (Management - Features)
- added `minimum_bounding_geometry` (Management - Features)
- added `multipart_to_singlepart` (Management - Features) and aliased as `explode`
- added `polygon_to_line` (Management - Features)
- added `repair_geometry` (Management - Features)
- added `split_line_at_vertices` (Management - Features)
- added `xy_table_to_point` (Management - Features)
- added `xy_to_line` (Management - Features) and aliased as `xy_table_to_line`
- added `add_field` (Management - Fields) with support for multiple
- added `alter_field` (Management - Fields)
- added `calculate_field` (Management - Fields)
- added `delete_field` (Management - Fields)
- added `copy` (Management - General)
- added `delete` (Management - General) with support for multiple
- added `rename` (Management - General)
- added `dissolve` (Management - Generalization)
- added `add_attribute_index` (Management - Indexes)
- added `add_spatial_index` (Management - Indexes)
- added `remove_attribute_index` (Management - Indexes)
- added `remove_spatial_index` (Management - Indexes)
- added `define_projection` (Management - Projections and Transformations)
- added `project` (Management - Projections and Transformations)
- added `copy_rows` (Management - Table)
- added `create_table` (Management - Table)
- added `delete_rows` (Management - Table) and aliased as `truncate_table`
- added `get_count` (Management - Table)
- Settings support for `overwrite`
- Settings support for dimensions `xy_tolerance`, `output_m_option`, `output_z_option`, and `z_value`  
- Settings support for workspace `current_workspace`, `scratch_workspace`, and `scratch_folder`
- Settings support for coordinates `output_coordinate_system`,  `geographic_transformations`, and `extent`
