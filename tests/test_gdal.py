#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import os
import pytest

from hex_raster_processor.gdal_utils import GdalUtils
from hex_raster_processor.composer import Composer
from hex_raster_processor.utils import Utils

from .test_base import download_images, remove_file

KEEP_FILES = False
QUIET = False


@pytest.fixture
def get_default_data():
    """Default fixture data for Image GdalUtils and Utils.

    Returns:
        dict: object with bands, product, url, output_dir and image_types.
    """
    return {
        "bands": [],
        "product": "LC08_L1TP_221071_20170521_20170526_01_T1",
        "url": "https://landsat-pds.s3.amazonaws.com/c1/L8/221/071",
        "output_dir": "test_media/",
        "img_types": ["NDVI", "NDWI", "NBR", "NDMI", "NDSI", "NPCRI"]
    }


def test_thumbs_composition_band(get_default_data):
    """ Test thumbs composition band. """
    downloaded = download_images(bands=[4])
    output_dir = get_default_data.get("output_dir")
    output_path = os.path.join(output_dir, 'thumbs_band.jpeg')

    assert(downloaded)
    assert(not os.path.exists(output_path))

    thumbs = GdalUtils.thumbs(downloaded[0], output_path, quiet=QUIET)
    assert(os.path.exists(output_path))
    assert(thumbs)

    if not KEEP_FILES:
        remove_file(output_path)
        remove_file(output_path + ".aux.xml")


def test_thumbs_composition(get_default_data):
    """ Test thumbs composition. """
    downloaded = download_images(bands=[6, 5, 4])
    output_dir = get_default_data.get("output_dir")
    product = get_default_data.get("product")

    assert(downloaded)

    band_number = 6
    for band in downloaded[:3]:
        output = os.path.join(
            output_dir, 'thumbs_B{}.jpeg'.format(band_number)
        )
        thumbs = GdalUtils.thumbs(band, output, quiet=QUIET)
        band_number = band_number - 1
        if not KEEP_FILES:
            remove_file(output)
            remove_file(output + ".aux.xml")

    composition = Composer.create_composition(
        filename=product,
        ordered_filelist=downloaded[:3],
        output_path=Utils.check_creation_folder(output_dir),
        bands=[6, 5, 4],
        quiet=QUIET
    )
    assert(composition)
    assert(composition['type'] == 'r6g5b4')

    output = os.path.join(output_dir, 'thumbs_composition.jpeg')
    remove_file(output)
    assert(not os.path.exists(output))

    thumbs = GdalUtils.thumbs(composition['path'], output, quiet=QUIET)
    assert(thumbs)
    assert(os.path.exists(output))
    if not KEEP_FILES:
        remove_file(output)
        remove_file(output + ".aux.xml")


def test_thumbs_composition_rgb(get_default_data):
    """ Test thumbs composition rgb. """
    output_dir = get_default_data.get("output_dir")
    downloaded = download_images(bands=[6, 5, 4])
    assert(len(downloaded) == 5)  # +BQA and MTL
    output = os.path.join(output_dir, 'composite_file.jpeg')
    thumbs = GdalUtils.composition_rgb_thumbs(downloaded[:3], output)
    assert(thumbs)

    if not KEEP_FILES:
        remove_file(output)
        remove_file(output + ".aux.xml")


def test_generate_footprint(get_default_data):
    """ Test gdal create thumbs. """
    downloaded = download_images(bands=[4])
    assert(downloaded)
    footprint = GdalUtils.generate_footprint(downloaded[0], simplify=50)
    assert(footprint is not None)
    assert(footprint != 'POLYGON EMPTY')


def test_create_text_files(get_default_data):
    """ Test gdal create text files. """
    for img_type in get_default_data.get("img_types"):
        text_file = GdalUtils.get_color_text_file(img_type)
        assert os.path.exists(text_file)
        assert "/tmp/" in text_file


def test_gdaldem_command_creation(get_default_data):
    """ Test gdaldem command creation. """
    command = GdalUtils.get_gdal_dem_color_command()
    assert command
    assert "gdaldem" in command


def test_normalized_thumbs_creation(get_default_data):
    """ Test normalized thumbs creation. """
    product = get_default_data.get("product")
    output_dir = get_default_data.get("output_dir")

    downloaded = download_images(bands=[4])
    assert downloaded

    for img_type in get_default_data.get("img_types"):
        output_path = "{}_{}_thumbs.jpg".format(product, img_type.lower())
        output_path = os.path.join(output_dir, output_path)

        thumbs = GdalUtils.create_normalized_thumbs(
            input_image=downloaded[0],
            output_path=output_path,
            size=[10, 10],
            img_format='JPEG',
            img_type=img_type,
            quiet=QUIET
        )

        assert thumbs
        assert "jpg" in thumbs
        assert os.path.exists(thumbs)
