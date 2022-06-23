#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import os
import homura

from hex_raster_processor.utils import Utils


def remove_file(input_file):
    """
    Void method to remove input_file from filesystem

    Arguments:
        * input_file (str): path to file
    """
    if os.path.exists(input_file):
        os.remove(input_file)


def get_bands(bands=[6, 5, 4]):
    """
    Get bands list from bands argument

    Arguments:
        * bands (list): bands list name

    Returns:
        * bands (list): parsed bands list
    """
    bands = ["_B{}.TIF".format(i) for i in bands]
    bands.extend(["_BQA.TIF", "_MTL.txt"])
    return bands


def download_image(url, path):
    """
    Download bands on defined PATH for test_process
    """
    if os.path.exists(path):
        return path

    try:
        homura.download(url, path=path)
        return path
    except Exception as exc:
        log = "Error while trying to download files: {}"
        print(log.format(exc))

    return False


def download_images(
    scene="LC08_L1TP_221071_20170521_20170526_01_T1",
    url=None,
    output_dir="test_media/",
    bands=[6, 5, 4]
):
    """
    Download bands on defined PATH for test_process

    Arguments:
        * scene (str): Landsat scene product name
        * bands (list): Landsat bands download list
        * url (str): url to download
        * output_dir (str): output dir to download image

    Returns:
        * downloaded (list): list with downloaded images
    """
    downloaded_images = []
    path = Utils.check_creation_folder(output_dir)

    if not url:
        url = "https://storage.googleapis.com/" + \
            "gcp-public-data-landsat/LC08/01/221/071"

    scene_bands = [{
        "url": "{url}/{scene}/{scene}{band}".format(
            url=url,
            scene=scene,
            band=band
        ),
        "band": band.split(".")[0]
    } for band in get_bands(bands)]

    for band in scene_bands:
        path = band["url"].split("/")[-1]
        path = os.path.join(output_dir, path)
        img = download_image(url=band["url"], path=path)
        downloaded_images.append(img)

    return downloaded_images
