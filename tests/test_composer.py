#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import pytest

from hex_raster_processor.composer import Composer
from hex_raster_processor.utils import Utils
from hex_raster_processor.exceptions import ValidationBandError

from .test_base import download_images

QUIET = True


@pytest.fixture
def get_default_data():
    """Default data for Composer tests.

    Returns:
        dict: object with bands, product, url and output_dir.
    """
    return {
        "bands": [],
        "product": "LC08_L1TP_221071_20170521_20170526_01_T1",
        "url": "https://landsat-pds.s3.amazonaws.com/c1/L8/221/071",
        "output_dir": "test_media/",
    }


def test_create_composition_with_downloaded_images(get_default_data):
    """ Test download and create composition with downloaded images """

    product = get_default_data.get("product")
    output_dir = get_default_data.get("output_dir")

    download = download_images(bands=[6, 5, 4])
    assert(len(download) == 5)

    composition = Composer.create_composition(
        filename=product,
        ordered_filelist=download[:3],
        output_path=Utils.check_creation_folder(output_dir),
        bands=[6, 5, 4],
        quiet=QUIET
    )

    assert(composition["type"] == "r6g5b4")
    assert(composition["name"] == "{}_r6g5b4.TIF".format(product))


def test_create_composition_with_downloaded_images_error(get_default_data):
    """ Test download and create composition with downloaded images error """

    product = get_default_data.get("product")
    output_dir = get_default_data.get("output_dir")

    download = download_images(bands=[6, 5, 4])
    assert(len(download) == 5)

    test_error = [download[0], download[1], 'test_error.tif']

    with pytest.raises(ValidationBandError):
        Composer.create_composition(
            filename=product,
            ordered_filelist=test_error,
            output_path=Utils.check_creation_folder(output_dir),
            bands=[6, 5, 4],
            quiet=QUIET
        )
