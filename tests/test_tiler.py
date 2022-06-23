#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import os
import pytest
import shutil
import subprocess

from hex_raster_processor.tiler import Tiler
from hex_raster_processor.exceptions import TMSError

from .test_base import download_images


@pytest.fixture
def get_default_data():
    """Returns default data for Tiler tests.

    Returns:
        dict: object with bands, product, url and output_dir.
    """
    return {
        "bands": [],
        "product": "LC08_L1TP_221071_20170521_20170526_01_T1",
        "url": "https://storage.googleapis.com/" +
               "gcp-public-data-landsat/LC08/01/221/071",
        "output_dir": "test_media/",
    }


@pytest.fixture
def create_data(get_default_data):
    """Fixture data (SetUp).

    Returns:
        dict: object with zoom, tifffile, output_path and output_path_check.
    """
    output_dir = get_default_data.get("output_dir")
    product = get_default_data.get("product")

    download_images(bands=[4])

    tiffile = os.path.join(output_dir, product + "_B4.TIF")
    output_path = os.path.join(output_dir, 'tms')
    output_path_check = os.path.join(output_path, product + "_B4.tms")

    return {
        "zoom": 7,
        "tiffile": tiffile,
        "output_path": output_path,
        "output_path_check": output_path_check
    }


def test_os_environ_gdal_tiler():
    """ Test if tilers-tools is present on system environmets. """
    assert 'tilers-tools' in os.environ["PATH"]


def test_call_gdal_tiler(create_data):
    """ Tests if gdal_tiler.py is valid and test data creation using it. """

    zoom = 7
    cmd = 'gdal_tiler.py -p tms --src-nodata 0 --zoom={} -t {} {}'.format(
        zoom, create_data['output_path'], create_data['tiffile'])
    subprocess.call(cmd, shell=True)

    assert os.path.exists(create_data['output_path'])
    assert os.path.exists(create_data['output_path_check'])

    output_path = os.path.join(create_data['output_path_check'], '7')
    assert os.path.exists(output_path)

    output_path = os.path.join(create_data['output_path_check'], '8')
    assert not os.path.exists(output_path)

    cmd = 'gdal_tiler.py -p tms --src-nodata 0 --zoom=7:8 -t {} {}'.format(
        create_data['output_path'], create_data['tiffile']),
    subprocess.call(cmd, shell=True)

    output_path = os.path.join(create_data['output_path_check'], '8')
    assert os.path.exists(output_path)
    shutil.rmtree(create_data['output_path_check'])


def test_tiler_make_tiles(create_data):
    """ Tests if Tiler.make_tiles creates a pyramid data. """

    data = Tiler.make_tiles(
        image_path=create_data['tiffile'],
        base_link=create_data['output_path'],
        output_folder=create_data['output_path'],
        zoom=[7, 8],
        quiet=False,
        nodata=[0]
    )

    assert os.path.isfile(create_data['tiffile'])
    assert len(data) == 2
    assert data[0] == create_data['output_path_check']
    assert os.path.exists(data[0])
    assert os.path.isfile(data[1])

    zoom_7 = os.path.join(data[0], '7')
    zoom_8 = os.path.join(data[0], '8')
    zoom_9 = os.path.join(data[0], '9')

    assert os.path.exists(zoom_7)
    assert os.path.exists(zoom_8)
    assert not os.path.exists(zoom_9)


def test_tiler_make_tiles_with_gdal_contrast(create_data):
    """ Tests if Tiler.make_tiles creates a pyramid data. """
    data = Tiler.make_tiles(
        image_path=create_data['tiffile'],
        base_link=create_data['output_path'],
        output_folder=create_data['output_path'],
        zoom=[7, 8],
        contrast=True,
        quiet=False,
        nodata=[0]
    )

    assert os.path.isfile(create_data['tiffile'])
    assert len(data) == 2
    assert data[0] == create_data['output_path_check']
    assert os.path.exists(data[0])
    assert os.path.isfile(data[1])

    zoom_7 = os.path.join(data[0], '7')
    zoom_8 = os.path.join(data[0], '8')
    zoom_9 = os.path.join(data[0], '9')

    assert os.path.exists(zoom_7)
    assert os.path.exists(zoom_8)
    assert not os.path.exists(zoom_9)


def test_tiler_make_tiles_exception(create_data):
    """ When nodata is different of datasource bands count. """
    with pytest.raises(TMSError):
        Tiler.make_tiles(
            image_path=create_data['tiffile'],
            base_link=create_data['output_path'],
            output_folder=create_data['output_path'],
            zoom=[7, 8],
            quiet=False,
            nodata=[0, 0],
        )

    """ When image path is a invalid datasource. """
    with pytest.raises(Exception):
        Tiler.make_tiles(
            image_path=None,
            base_link=create_data['output_path'],
            output_folder=create_data['output_path'],
            zoom=[7, 8],
            quiet=False,
            nodata=[0, 0],
        )

    """ When Linkbase is None. """
    with pytest.raises(Exception):
        Tiler.make_tiles(
            image_path=create_data['tiffile'],
            base_link=None,
            output_folder=create_data['output_path'],
            zoom=[7, 8],
            quiet=False,
            nodata=[0],
        )

    """ When exists only image_path. """
    with pytest.raises(Exception):
        Tiler.make_tiles(
            image_path=create_data['tiffile'],
        )


def test_tiler_make_tiles_with_move(create_data):
    """ Tests if Tiler.make_tiles creates a pyramid data. """
    output_folder = os.path.join(create_data['output_path'], 'tiles')
    tms_path, xml_path = Tiler.make_tiles(
        image_path=create_data['tiffile'],
        base_link=create_data['output_path'],
        output_folder=output_folder,
        move=True,
        zoom=[7, 10],
        quiet=False,
        nodata=[0]
    )

    assert os.path.isfile(create_data['tiffile'])
    assert os.path.exists(tms_path)
    assert os.path.isfile(xml_path)

    zoom_7 = os.path.join(tms_path, '7')
    zoom_8 = os.path.join(tms_path, '8')
    zoom_9 = os.path.join(tms_path, '9')
    zoom_10 = os.path.join(tms_path, '10')
    zoom_11 = os.path.join(tms_path, '11')

    assert os.path.exists(zoom_7)
    assert os.path.exists(zoom_8)
    assert os.path.exists(zoom_9)
    assert os.path.exists(zoom_10)
    assert not os.path.exists(zoom_11)


def test_tiler_make_tiles_with_move_stress(create_data):
    """ Tests if Tiler.make_tiles creates a pyramid data. """
    output_folder = os.path.join(create_data['output_path'], 'tiles')

    for i in range(5):
        tms_path, xml_path = Tiler.make_tiles(
            image_path=create_data['tiffile'],
            base_link=create_data['output_path'],
            output_folder=output_folder,
            move=True,
            zoom=[6, 7],
            quiet=False,
            nodata=[0]
        )
        assert os.path.isfile(create_data['tiffile'])
        assert os.path.exists(tms_path)
        assert os.path.isfile(xml_path)

        zoom_6 = os.path.join(tms_path, '6')
        zoom_7 = os.path.join(tms_path, '7')
        zoom_8 = os.path.join(tms_path, '8')

        assert os.path.exists(zoom_6)
        assert os.path.exists(zoom_7)
        assert not os.path.exists(zoom_8)
