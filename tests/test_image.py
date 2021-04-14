#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import os
import pytest
import subprocess

from hex_raster_processor.image_info import Image


@pytest.fixture
def get_default_data():
    """Default data fixture for Image tests.

    Returns:
        dict: object with bands, product, url, output_dir and local_path.
    """
    local_path = os.path.abspath(os.path.dirname('.'))
    local_path = os.path.join(local_path, 'test_media')

    return {
        "bands": [],
        "product": "LC08_L1TP_221071_20170521_20170526_01_T1",
        "url": "https://landsat-pds.s3.amazonaws.com/c1/L8/221/071",
        "output_dir": "test_media/",
        "local_path": local_path
    }


@pytest.fixture
def create_image(get_default_data):
    """ Fixture to create image data.

    Returns:
        tuple: image1, image2, path1, path2
    """
    local_path = get_default_data.get("local_path")
    product = get_default_data.get("product")

    path_1 = os.path.join(local_path, product + "_r4b3g2.TIF")
    path_2 = os.path.join(local_path, product + "_r4b3g2")

    image_1 = Image(path_1)
    image_2 = Image(path_2)

    create_files(image_1.image_dir, product + "_r4b3g2.TIF")
    create_files(image_2.image_dir, product + "_r4b3g2")

    return image_1, image_2, path_1, path_2


def create_files(dir, file):
    """ Fixture to create files data. """
    subprocess.call('mkdir {} -p '.format(dir), shell=True)
    subprocess.call('touch {} '.format(os.path.join(dir, file)), shell=True)


def test_image_info(create_image, get_default_data):
    """ Fixture to create files data. """
    local_path = get_default_data.get("local_path")
    product = get_default_data.get("product")

    data = create_image
    assert(data[0].image_path == data[2])
    assert(data[1].image_path == data[3])
    assert(data[0].image_dir == local_path)
    assert(data[1].image_dir == local_path)
    assert(data[0].image_name == product + "_r4b3g2")
    assert(data[1].image_name == product + "_r4b3g2")


def test_image_rename(create_image, get_default_data):
    """ Test Image rename method. """
    local_path = get_default_data.get("local_path")

    data = create_image
    image = data[0]
    image.rename_file("my_image")

    assert(image.image_path == os.path.join(local_path, 'my_image'))
    assert(image.image_name == 'my_image')
    assert(image.image_dir == local_path)
    assert(os.path.exists(image.image_path))
    image.remove_file()
    assert(not os.path.exists(image.image_path))


def test_remove_file(create_image):
    """ Test remove files from Image. """
    data = create_image
    assert(os.path.exists(data[0].image_path))
    assert(os.path.exists(data[1].image_path))

    data[0].remove_file()
    data[1].remove_file()

    assert(not os.path.exists(data[0].image_path))
    assert(not os.path.exists(data[1].image_path))


def test_create_tempfile(create_image):
    """ Test Image method to create tempfile. """
    image_1 = create_image[0]
    image_2 = create_image[1]

    temp = image_1.get_tempfile()
    assert not os.path.exists(temp)
    assert not os.path.isdir(os.path.basename(temp))

    temp = image_2.get_tempfile()
    assert not os.path.exists(temp)
    assert not os.path.isdir(os.path.basename(temp))
