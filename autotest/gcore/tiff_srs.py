#!/usr/bin/env pytest
###############################################################################
# $Id$
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test read/write round-tripping of SRS for GeoTIFF format.
# Author:   Even Rouault, <even dot rouault at mines dash paris dot org>
#
###############################################################################
# Copyright (c) 2011-2012, Even Rouault <even dot rouault at mines-paris dot org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################


import pytest

from osgeo import gdal
from osgeo import osr


###############################################################################
# Test fix for #4677:


def test_tiff_srs_without_linear_units():

    sr = osr.SpatialReference()
    sr.ImportFromProj4('+proj=vandg +datum=WGS84')

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_without_linear_units.tif', 1, 1)
    ds.SetProjection(sr.ExportToWkt())
    ds = None

    ds = gdal.Open('/vsimem/tiff_srs_without_linear_units.tif')
    wkt = ds.GetProjectionRef()
    sr2 = osr.SpatialReference()
    sr2.SetFromUserInput(wkt)
    ds = None

    gdal.Unlink('/vsimem/tiff_srs_without_linear_units.tif')

    assert sr.IsSame(sr2) == 1, 'did not get expected SRS'

###############################################################################
# Test writing a COMPDCS without VerticalCSType


def test_srs_write_compd_cs():

    sr = osr.SpatialReference()
    # EPSG:7400 without the Authority
    sr.SetFromUserInput("""COMPD_CS["unknown",
    GEOGCS["NTF (Paris)",
        DATUM["Nouvelle_Triangulation_Francaise_Paris",
            SPHEROID["Clarke 1880 (IGN)",6378249.2,293.4660212936265,
                AUTHORITY["EPSG","7011"]],
            TOWGS84[-168,-60,320,0,0,0,0],
            AUTHORITY["EPSG","6807"]],
        PRIMEM["Paris",2.5969213],
        UNIT["grad",0.01570796326794897],
        AUTHORITY["EPSG","4807"]],
    VERT_CS["NGF-IGN69 height",
        VERT_DATUM["Nivellement General de la France - IGN69",2005,
            AUTHORITY["EPSG","5119"]],
        UNIT["metre",1,
            AUTHORITY["EPSG","9001"]],
        AXIS["Up",UP]]]""")

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_compd_cs.tif', 1, 1)
    ds.SetProjection(sr.ExportToWkt())
    ds = None

    gdal.SetConfigOption('GTIFF_REPORT_COMPD_CS', 'YES')
    ds = gdal.Open('/vsimem/tiff_srs_compd_cs.tif')
    wkt = ds.GetProjectionRef()
    gdal.SetConfigOption('GTIFF_REPORT_COMPD_CS', None)
    sr2 = osr.SpatialReference()
    sr2.SetFromUserInput(wkt)
    ds = None

    gdal.Unlink('/vsimem/tiff_srs_compd_cs.tif')

    assert sr.IsSame(sr2) == 1, 'did not get expected SRS'

###############################################################################
# Test reading a COMPDCS without VerticalCSType


def test_srs_read_compd_cs():

    gdal.SetConfigOption('GTIFF_REPORT_COMPD_CS', 'YES')
    ds = gdal.Open('data/vertcs_user_defined.tif')
    wkt = ds.GetProjectionRef()
    gdal.SetConfigOption('GTIFF_REPORT_COMPD_CS', None)

    assert wkt == 'COMPD_CS["NAD27 / UTM zone 11N + EGM2008 height",PROJCS["NAD27 / UTM zone 11N",GEOGCS["NAD27",DATUM["North_American_Datum_1927",SPHEROID["Clarke 1866",6378206.4,294.978698213898,AUTHORITY["EPSG","7008"]],AUTHORITY["EPSG","6267"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4267"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-117],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","26711"]],VERT_CS["EGM2008 height",VERT_DATUM["EGM2008 geoid",2005,AUTHORITY["EPSG","1027"]],UNIT["foot",0.3048,AUTHORITY["EPSG","9002"]],AXIS["Up",UP]]]'

###############################################################################
# Test reading a GeoTIFF with both StdParallel1 and ScaleAtNatOrigin defined (#5791)


def test_tiff_srs_weird_mercator_2sp():

    ds = gdal.Open('data/weird_mercator_2sp.tif')
    gdal.PushErrorHandler()
    wkt = ds.GetProjectionRef()
    gdal.PopErrorHandler()
    assert gdal.GetLastErrorMsg() != '', 'warning expected'
    sr2 = osr.SpatialReference()
    sr2.SetFromUserInput(wkt)
    ds = None

    sr = osr.SpatialReference()
    # EPSG:7400 without the Authority
    sr.SetFromUserInput("""PROJCS["Global Mercator",
    GEOGCS["NAD83",
        DATUM["North_American_Datum_1983",
            SPHEROID["GRS 1980",6378137,298.2572221010002,
                AUTHORITY["EPSG","7019"]],
            TOWGS84[0,0,0,0,0,0,0],
            AUTHORITY["EPSG","6269"]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433],
        AUTHORITY["EPSG","4269"]],
    PROJECTION["Mercator_2SP"],
    PARAMETER["standard_parallel_1",47.667],
    PARAMETER["central_meridian",0],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]]]""")

    assert sr.IsSame(sr2) == 1, 'did not get expected SRS'

###############################################################################
# Test reading ESRI WGS_1984_Web_Mercator_Auxiliary_Sphere


def test_tiff_srs_WGS_1984_Web_Mercator_Auxiliary_Sphere():

    ds = gdal.Open('data/WGS_1984_Web_Mercator_Auxiliary_Sphere.tif')
    wkt = ds.GetProjectionRef()
    sr = osr.SpatialReference()
    sr.SetFromUserInput(wkt)
    wkt = sr.ExportToPrettyWkt()
    ds = None

    assert wkt == """PROJCS["WGS 84 / Pseudo-Mercator",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Mercator_1SP"],
    PARAMETER["central_meridian",0],
    PARAMETER["scale_factor",1],
    PARAMETER["false_easting",0],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs"]]"""

###############################################################################
# Test writing and reading various angular units


def test_tiff_srs_angular_units():

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (arc-second)",
    DATUM["WGS_1984 (arc-second)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["arc-second",4.848136811095361e-06]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["arc-second",4.84813681109536E-06' in wkt
    ds = None

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (arc-minute)",
    DATUM["WGS_1984 (arc-minute)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["arc-minute",0.0002908882086657216]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["arc-minute",0.000290888208665722]' in wkt
    ds = None

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (grad)",
    DATUM["WGS_1984 (grad)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["grad",0.01570796326794897]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["grad",0.015707963267949' in wkt
    ds = None

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (gon)",
    DATUM["WGS_1984 (gon)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["gon",0.01570796326794897]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["gon",0.015707963267949]' in wkt
    ds = None

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (radian)",
    DATUM["WGS_1984 (radian)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["radian",1]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["radian",1]' in wkt
    ds = None

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_angular_units.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 (custom)",
    DATUM["WGS_1984 (custom)",
        SPHEROID["WGS 84",6378137,298.257223563]],
    PRIMEM["Greenwich",0],
    UNIT["custom",1.23]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_angular_units.tif')
    wkt = ds.GetProjectionRef()
    assert 'UNIT["custom",1.23]' in wkt
    ds = None

    gdal.Unlink('/vsimem/tiff_srs_angular_units.tif')

###############################################################################
# Test writing and reading a unknown datum but with a known ellipsoid


def test_tiff_custom_datum_known_ellipsoid():

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_custom_datum_known_ellipsoid.tif', 1, 1)
    ds.SetProjection("""GEOGCS["WGS 84 based",
    DATUM["WGS_1984_based",
        SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]]],
    PRIMEM["Greenwich",0],
    UNIT["degree",1]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_custom_datum_known_ellipsoid.tif')
    wkt = ds.GetProjectionRef()
    assert wkt == 'GEOGCS["WGS 84 based",DATUM["WGS_1984_based",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST]]'
    ds = None

    gdal.Unlink('/vsimem/tiff_custom_datum_known_ellipsoid.tif')

###############################################################################
# Test reading a GeoTIFF file with only PCS set, but with a ProjLinearUnitsGeoKey
# override to another unit (us-feet) ... (#6210)


def test_tiff_srs_epsg_2853_with_us_feet():

    old_val = gdal.GetConfigOption('GTIFF_IMPORT_FROM_EPSG')
    gdal.SetConfigOption('GTIFF_IMPORT_FROM_EPSG', 'YES')
    ds = gdal.Open('data/epsg_2853_with_us_feet.tif')
    gdal.SetConfigOption('GTIFF_IMPORT_FROM_EPSG', old_val)
    wkt = ds.GetProjectionRef()
    assert 'PARAMETER["false_easting",11482916.66' in wkt and 'UNIT["us_survey_feet",0.3048006' in wkt and '2853' not in wkt

    gdal.SetConfigOption('GTIFF_IMPORT_FROM_EPSG', 'NO')
    ds = gdal.Open('data/epsg_2853_with_us_feet.tif')
    gdal.SetConfigOption('GTIFF_IMPORT_FROM_EPSG', old_val)
    wkt = ds.GetProjectionRef()
    assert 'PARAMETER["false_easting",11482916.66' in wkt and 'UNIT["us_survey_feet",0.3048006' in wkt and '2853' not in wkt

###############################################################################
# Test reading a SRS with a PCSCitationGeoKey = "LUnits = ..."


def test_tiff_srs_PCSCitationGeoKey_LUnits():

    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/tiff_srs_PCSCitationGeoKey_LUnits.tif', 1, 1)
    ds.SetProjection("""PROJCS["UTM Zone 32, Northern Hemisphere",
    GEOGCS["GRS 1980(IUGG, 1980)",
        DATUM["unknown",
            SPHEROID["GRS80",6378137,298.257222101],
            TOWGS84[0,0,0,0,0,0,0]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",9],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",50000000],
    PARAMETER["false_northing",0],
    UNIT["Centimeter",0.01]]""")
    ds = None
    ds = gdal.Open('/vsimem/tiff_srs_PCSCitationGeoKey_LUnits.tif')
    wkt = ds.GetProjectionRef()
    assert wkt == 'PROJCS["UTM Zone 32, Northern Hemisphere",GEOGCS["GRS 1980(IUGG, 1980)",DATUM["unknown",SPHEROID["GRS80",6378137,298.257222101],TOWGS84[0,0,0,0,0,0,0]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",9],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",50000000],PARAMETER["false_northing",0],UNIT["Centimeter",0.01],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
    ds = None

    gdal.Unlink('/vsimem/tiff_srs_PCSCitationGeoKey_LUnits.tif')

###############################################################################
# Test reading a geotiff key ProjectionGeoKey (Short,1): Unknown-3856


def test_tiff_srs_projection_3856():

    ds = gdal.Open('data/projection_3856.tif')
    wkt = ds.GetProjectionRef()
    ds = None

    assert 'EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs' in wkt

###############################################################################
# Test reading a geotiff with a LOCAL_CS and a Imagine citation


def test_tiff_srs_imagine_localcs_citation():

    ds = gdal.Open('data/imagine_localcs_citation.tif')
    wkt = ds.GetProjectionRef()
    ds = None

    assert wkt.startswith('LOCAL_CS["Projection Name = UTM Units = meters GeoTIFF Units = meters"')

###############################################################################
# Test reading a geotiff with a EPSG code and a TOWGS84 key that must
# override the default coming from EPSG


def test_tiff_srs_towgs84_override():

    ds = gdal.Open('data/gtiff_towgs84_override.tif')
    wkt = ds.GetProjectionRef()
    ds = None

    assert 'TOWGS84[584.8,67,400.3,0.105,0.013,-2.378,10.29]' in wkt, wkt

###############################################################################
# Test reading PCSCitationGeoKey (#7199)


def test_tiff_srs_pcscitation():

    ds = gdal.Open('data/pcscitation.tif')
    wkt = ds.GetProjectionRef()
    ds = None

    assert wkt.startswith('PROJCS["mycitation",')

###############################################################################
# Test reading file with ProjectedCSTypeGeoKey and GeographicTypeGeoKey


def test_tiff_srs_ProjectedCSTypeGeoKey_GeographicTypeGeoKey():

    ds = gdal.Open('data/utmsmall.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetAuthorityCode(None) == "26711"


def _test_tiff_srs(sr, expect_fail):
    """
    This is not a test by itself; it gets called by the tests below.
    """
    ds = gdal.GetDriverByName('GTiff').Create('/vsimem/TestTiffSRS.tif', 1, 1)
    ds.SetProjection(sr.ExportToWkt())
    ds = None

    ds = gdal.Open('/vsimem/TestTiffSRS.tif')
    wkt = ds.GetProjectionRef()
    sr2 = osr.SpatialReference()
    sr2.SetFromUserInput(wkt)
    ds = None

    gdal.Unlink('/vsimem/TestTiffSRS.tif')

    if sr.IsSame(sr2) != 1:
        if expect_fail:
            pytest.xfail('did not get expected SRS. known to be broken currently. FIXME!')

        print(sr)
        print(sr2)
        assert False, 'did not get expected SRS'
    else:
        if expect_fail:
            print('Succeeded but expected fail...')


###############################################################################
# Write a geotiff and read it back to check its SRS

epsg_list = [
    [3814, False],  # tmerc
    [28991, False],  # sterea
    # [2046, False],  # tmerc south oriented DISABLED. Not sure about the axis
    [3031, False],  # polar stere (ticket #3220)
    [3032, False],  # polar stere (ticket #3220)
    [32661, False],  # stere
    [3408, False],  # laea
    [2062, False],  # lcc 1SP
    #[2065, True],  # krovak South-West
    [5221, True],  # krovak east-north
    [2066, False],  # cass
    [2964, False],  # aea
    [3410, False],  # cea
    [3786, False],  # eqc spherical, method=9823
    [32663, False],  # eqc elliptical, method=9842
    [4087, False],  # eqc WGS 84 / World Equidistant Cylindrical method=1028
    [4088, False],  # eqc World Equidistant Cylindrical (Sphere) method=1029
    [2934, False],  # merc
    [27200, False],  # nzmg
    [2057, False],  # omerc Hotine_Oblique_Mercator_Azimuth_Center
    [3591, False],  # omerc Hotine_Oblique_Mercator
    [29100, False],  # poly
    [2056, False],  # somerc
    [2027, False],  # utm
    [4326, False],  # longlat
    [26943, False],  # lcc 2SP,
    [4328, False],  # geocentric
    [3994, False],  # mercator 2SP
    [26920, False],  # UTM NAD83 special case
    [26720, False],  # UTM NAD27 special case
    [32630, False],  # UTM WGS84 north special case
    [32730, False],  # UTM WGS84 south special case
    [22700, False],  # unknown datum 'Deir_ez_Zor'
    [3857, True],  # Web Mercator
    [102113, True],  # ESRI WGS_1984_Web_Mercator
]


@pytest.mark.parametrize('use_epsg_code', [0, 1])
@pytest.mark.parametrize(
    'epsg_code,epsg_proj4_broken',
    epsg_list,
    ids=[str(r[0]) for r in epsg_list],
)
def test_tiff_srs(use_epsg_code, epsg_code, epsg_proj4_broken):
    sr = osr.SpatialReference()
    if epsg_code > 32767:
        sr.SetFromUserInput('ESRI:' + str(epsg_code))
    else:
        sr.ImportFromEPSG(epsg_code)
    expect_fail = False
    if use_epsg_code == 0:
        proj4str = sr.ExportToProj4()
        # print(proj4str)
        sr.SetFromUserInput(proj4str)
        expect_fail = epsg_proj4_broken

    _test_tiff_srs(sr, expect_fail)


@pytest.mark.parametrize(
    'proj4',
    [
        '+proj=eqdc +lat_0=%.16g +lon_0=%.16g +lat_1=%.16g +lat_2=%.16g" +x_0=%.16g +y_0=%.16g' % (1, 2, 3, 4, 5, 6),
        '+proj=mill +lat_0=%.16g +lon_0=%.16g +x_0=%.16g +y_0=%.16g +R_A' % (1, 2, 3, 4),
        '+proj=gnom +lat_0=%.16g +lon_0=%.16g +x_0=%.16g +y_0=%.16g' % (1, 2, 3, 4),
        '+proj=robin +lon_0=%.16g +x_0=%.16g +y_0=%.16g' % (1, 2, 3),
        '+proj=sinu +lon_0=%.16g +x_0=%.16g +y_0=%.16g' % (1, 2, 3),
    ],
    ids=[
        'eqdc',
        'mill',
        'gnom',
        'robin',
        'sinu',
    ]
)
def test_tiff_srs_proj4(proj4):
    sr = osr.SpatialReference()
    sr.SetFromUserInput(proj4)
    _test_tiff_srs(sr, False)


def _create_geotiff1_1_from_copy_and_compare(srcfilename, options = []):
    if int(gdal.GetDriverByName('GTiff').GetMetadataItem('LIBGEOTIFF')) < 1600:
        pytest.skip()

    src_ds = gdal.Open(srcfilename)
    tmpfile = '/vsimem/tmp.tif'
    gdal.GetDriverByName('GTiff').CreateCopy(tmpfile, src_ds, options = options)
    f = gdal.VSIFOpenL(tmpfile, 'rb')
    data = gdal.VSIFReadL(1, 100000, f)
    gdal.VSIFCloseL(f)
    gdal.Unlink(tmpfile)
    assert data == open(src_ds.GetDescription(), 'rb').read()


def test_tiff_srs_read_epsg4326_geotiff1_1():
    ds = gdal.Open('data/epsg4326_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetAuthorityCode(None) == '4326'


def test_tiff_srs_write_epsg4326_geotiff1_1():
    _create_geotiff1_1_from_copy_and_compare('data/epsg4326_geotiff1_1.tif',
                                             options = ['GEOTIFF_VERSION=1.1'])


def test_tiff_srs_read_epsg26711_geotiff1_1():
    ds = gdal.Open('data/epsg26711_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetAuthorityCode(None) == '26711'


def test_tiff_srs_write_epsg26711_geotiff1_1():
    _create_geotiff1_1_from_copy_and_compare('data/epsg26711_geotiff1_1.tif',
                                             options = ['GEOTIFF_VERSION=1.1'])


def test_tiff_srs_read_epsg4326_3855_geotiff1_1():
    ds = gdal.Open('data/epsg4326_3855_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetName() == 'WGS 84 + EGM2008 height'
    assert sr.GetAuthorityCode('COMPD_CS|GEOGCS') == '4326'
    assert sr.GetAuthorityCode('COMPD_CS|VERT_CS') == '3855'


def test_tiff_srs_write_epsg4326_3855_geotiff1_1():
    _create_geotiff1_1_from_copy_and_compare('data/epsg4326_3855_geotiff1_1.tif')


def test_tiff_srs_read_epsg4979_geotiff1_1():
    ds = gdal.Open('data/epsg4979_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetAuthorityCode(None) == '4979'


def test_tiff_srs_write_epsg4979_geotiff1_1():
    _create_geotiff1_1_from_copy_and_compare('data/epsg4979_geotiff1_1.tif')


# Deprecated way of conveying GeographicCRS 3D
def test_tiff_srs_read_epsg4326_5030_geotiff1_1():
    ds = gdal.Open('data/epsg4326_5030_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetAuthorityCode(None) == '4979'


def test_tiff_srs_read_epsg26711_3855_geotiff1_1():
    ds = gdal.Open('data/epsg26711_3855_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    assert sr.GetName() == 'NAD27 / UTM zone 11N + EGM2008 height'
    assert sr.GetAuthorityCode('COMPD_CS|PROJCS') == '26711'
    assert sr.GetAuthorityCode('COMPD_CS|VERT_CS') == '3855'


def test_tiff_srs_write_epsg26711_3855_geotiff1_1():
    _create_geotiff1_1_from_copy_and_compare('data/epsg26711_3855_geotiff1_1.tif')


# ProjectedCRS 3D not really defined yet in GeoTIFF 1.1, but this is
# a natural extension
def test_tiff_srs_read_epsg32631_4979_geotiff1_1():
    ds = gdal.Open('data/epsg32631_4979_geotiff1_1.tif')
    sr = ds.GetSpatialRef()
    # PROJ 6.0 didn't include the ID of the base CRS
    assert sr.ExportToWkt().replace(',ID["EPSG",4979]','') == 'PROJCRS["WGS 84 / UTM zone 31N",BASEGEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4979]],CONVERSION["UTM zone 31N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",3,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]],ID["EPSG",16031]],CS[Cartesian,3],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],AXIS["ellipsoidal height (h)",up,ORDER[3],LENGTHUNIT["metre",1]]]'.replace(',ID["EPSG",4979]','')
