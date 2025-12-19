# -*- coding: utf-8 -*-
"""
Constants for CRS tests
"""


CUSTOM_PROJ_STR: str = '+proj=longlat +ellps=airy +pm=lisbon +no_defs'
CUSTOM_CAMACUPA_UTM_32S: str = (
    'PROJCS["Camacupa UTM 32s custom",'
    'GEOGCS["GCS_Camacupa",'
    'DATUM["D_Camacupa",'
    'SPHEROID["Clarke_1880_RGS",6378249.145,293.465]],'
    'PRIMEM["Greenwich",0.0],'
    'UNIT["Degree",0.0174532925199433]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["False_Easting",269.9784017278618],'
    'PARAMETER["False_Northing",5399.568034557235],'
    'PARAMETER["Central_Meridian",9.0],'
    'PARAMETER["Scale_Factor",0.9996],'
    'PARAMETER["Latitude_Of_Origin",0.0],'
    'UNIT["Nautical_Mile",1852.0]]'
)
CUSTOM_COMPOUND_AUTH: str = (
    'PROJCS["NAD_1983_UTM_Zone_12N",'
    'GEOGCS["GCS_North_American_1983",'
    'DATUM["D_North_American_1983",'
    'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
    'PRIMEM["Greenwich",0.0],'
    'UNIT["Degree",0.0174532925199433]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["False_Easting",500000.0],'
    'PARAMETER["False_Northing",0.0],'
    'PARAMETER["Central_Meridian",-111.0],'
    'PARAMETER["Scale_Factor",0.9996],'
    'PARAMETER["Latitude_Of_Origin",0.0],'
    'UNIT["Meter",1.0]],'
    'VERTCS["NAVD88_height_(ftUS)",'
    'VDATUM["North_American_Vertical_Datum_1988"],'
    'PARAMETER["Vertical_Shift",0.0],'
    'PARAMETER["Direction",1.0],'
    'UNIT["US survey foot",0.304800609601219]]'
)
CUSTOM_COMPOUND_NO_AUTH_HORIZ: str = (
    'PROJCS["Camacupa_UTM_32s_custom",'
    'GEOGCS["GCS_Camacupa",'
    'DATUM["D_Camacupa",'
    'SPHEROID["Clarke_1880_RGS",6378249.145,293.465]],'
    'PRIMEM["Greenwich",0.0],'
    'UNIT["Degree",0.0174532925199433]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["False_Easting",269.978401727862],'
    'PARAMETER["False_Northing",5399.56803455723],'
    'PARAMETER["Central_Meridian",9.0],'
    'PARAMETER["Scale_Factor",0.9996],'
    'PARAMETER["Latitude_Of_Origin",0.0],'
    'UNIT["nautical mile",1852.0]],'
    'VERTCS["NAVD88_height_(ftUS)",'
    'VDATUM["North_American_Vertical_Datum_1988"],'
    'PARAMETER["Vertical_Shift",0.0],'
    'PARAMETER["Direction",1.0],'
    'UNIT["US survey foot",0.304800609601219]]'
)
CUSTOM_COMPOUND_NO_AUTH_VERT: str = (
    'PROJCS["NAD_1983_UTM_Zone_12N",'
    'GEOGCS["GCS_North_American_1983",'
    'DATUM["D_North_American_1983",'
    'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
    'PRIMEM["Greenwich",0.0],'
    'UNIT["Degree",0.0174532925199433]],'
    'PROJECTION["Transverse_Mercator"],'
    'PARAMETER["False_Easting",500000.0],'
    'PARAMETER["False_Northing",0.0],'
    'PARAMETER["Central_Meridian",-111.0],'
    'PARAMETER["Scale_Factor",0.9996],'
    'PARAMETER["Latitude_Of_Origin",0.0],'
    'UNIT["Meter",1.0]],'
    'VERTCS["Jimmy-O",'
    'VDATUM["North_American_Vertical_Datum_1988"],'
    'PARAMETER["Vertical_Shift",0.0],'
    'PARAMETER["Direction",1.0],'
    'UNIT["nautical mile",1852.0]]'
)
CUSTOM_THIRD_PARTY_AUTHORITY: str = """
    PROJCRS["Batavia / UTM zone 47N",
    BASEGEOGCRS["Batavia",
        DATUM["Batavia",
            ELLIPSOID["Bessel 1841",6377397.155,299.1528128,
                LENGTHUNIT["metre",1]]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433]],
        ID["EPSG",4211]],
    CONVERSION["UTM zone 47N",
        METHOD["Transverse Mercator",
            ID["EPSG",9807]],
        PARAMETER["Latitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",99,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["Scale factor at natural origin",0.9996,
            SCALEUNIT["unity",1],
            ID["EPSG",8805]],
        PARAMETER["False easting",500000,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]],
    CS[Cartesian,2],
        AXIS["easting",east,
            ORDER[1],
            LENGTHUNIT["metre",1]],
        AXIS["northing",north,
            ORDER[2],
            LENGTHUNIT["metre",1]],
    USAGE[
        SCOPE["unknown"],
        AREA["World."],
        BBOX[-90,-180,90,180]],
    ID["ThirdParty",54051]]
"""
COMPOUND_ESRI_EPSG_MIX: str = """
COMPOUNDCRS["NAD_1983_BC_Environment_Albers + NAVD88 depth",
    PROJCRS["NAD_1983_BC_Environment_Albers",
        BASEGEOGCRS["NAD83",
            DATUM["North American Datum 1983",
                ELLIPSOID["GRS 1980",6378137,298.257222101,
                    LENGTHUNIT["metre",1]]],
            PRIMEM["Greenwich",0,
                ANGLEUNIT["degree",0.0174532925199433]],
            ID["EPSG",4269]],
        CONVERSION["NAD_1983_BC_Environment_Albers",
            METHOD["Albers Equal Area",
                ID["EPSG",9822]],
            PARAMETER["Latitude of false origin",45,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8821]],
            PARAMETER["Longitude of false origin",-126,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8822]],
            PARAMETER["Latitude of 1st standard parallel",50,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8823]],
            PARAMETER["Latitude of 2nd standard parallel",58.5,
                ANGLEUNIT["degree",0.0174532925199433],
                ID["EPSG",8824]],
            PARAMETER["Easting at false origin",1000000,
                LENGTHUNIT["metre",1],
                ID["EPSG",8826]],
            PARAMETER["Northing at false origin",0,
                LENGTHUNIT["metre",1],
                ID["EPSG",8827]]],
        CS[Cartesian,2],
            AXIS["(E)",east,
                ORDER[1],
                LENGTHUNIT["metre",1]],
            AXIS["(N)",north,
                ORDER[2],
                LENGTHUNIT["metre",1]],
        USAGE[
            SCOPE["Not known."],
            AREA["Canada - British Columbia."],
            BBOX[48.25,-139.04,60.01,-114.08]],
        ID["ESRI",102190]],
    VERTCRS["NAVD88 depth",
        VDATUM["North American Vertical Datum 1988"],
        CS[vertical,1],
            AXIS["depth (D)",down,
                LENGTHUNIT["metre",1]],
        USAGE[
            SCOPE["Geodesy, engineering survey."],
            AREA["Mexico - onshore. United States (USA) - CONUS and Alaska - onshore - Alabama; Alaska; Arizona; Arkansas; California; Colorado; Connecticut; Delaware; Florida; Georgia; Idaho; Illinois; Indiana; Iowa; Kansas; Kentucky; Louisiana; Maine; Maryland; Massachusetts; Michigan; Minnesota; Mississippi; Missouri; Montana; Nebraska; Nevada; New Hampshire; New Jersey; New Mexico; New York; North Carolina; North Dakota; Ohio; Oklahoma; Oregon; Pennsylvania; Rhode Island; South Carolina; South Dakota; Tennessee; Texas; Utah; Vermont; Virginia; Washington; West Virginia; Wisconsin; Wyoming."],
            BBOX[14.51,172.42,71.4,-66.91]],
        ID["EPSG",6357]]]
"""
CUSTOM_THIRD_PARTY_AUTHORITY_60000: str = """
    PROJCS["Batavia / UTM zone 47N",
    GEOGCS["Batavia",
        DATUM["Batavia",
            SPHEROID["Bessel 1841",6377397.155,299.1528128]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4211"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",99],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",500000],
    PARAMETER["false_northing",0],
    UNIT["metre",1],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["ThirdParty","60000"]]
"""
NAD_1983_StatePlane_Texas_North_Central_FIPS_4202: str = 'PROJCS["NAD_1983_StatePlane_Texas_North_Central_FIPS_4202",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",600000.0],PARAMETER["False_Northing",2000000.0],PARAMETER["Central_Meridian",-98.5],PARAMETER["Standard_Parallel_1",32.13333333333333],PARAMETER["Standard_Parallel_2",33.96666666666667],PARAMETER["Latitude_Of_Origin",31.66666666666667],UNIT["Meter",1.0]]'
NAD_1927_StatePlane_Texas_North_Central_FIPS_4202: str = 'PROJCS["NAD_1927_StatePlane_Texas_North_Central_FIPS_4202",GEOGCS["GCS_North_American_1927",DATUM["D_North_American_1927",SPHEROID["Clarke_1866",6378206.4,294.9786982]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",2000000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-97.5],PARAMETER["Standard_Parallel_1",32.13333333333333],PARAMETER["Standard_Parallel_2",33.96666666666667],PARAMETER["Latitude_Of_Origin",31.66666666666667],UNIT["Foot_US",0.3048006096012192]]'
NAD_1983_UTM_Zone_15N: str = 'PROJCS["NAD_1983_UTM_Zone_15N",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-93.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'
NAD_1927_UTM_Zone_15N: str = 'PROJCS["NAD_1927_UTM_Zone_15N",GEOGCS["GCS_North_American_1927",DATUM["D_North_American_1927",SPHEROID["Clarke_1866",6378206.4,294.9786982]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",1640416.666666667],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-93.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Foot_US",0.3048006096012192]]'


if __name__ == '__main__':  # pragma: no cover
    pass
