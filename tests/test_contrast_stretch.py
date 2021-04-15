#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `hex_raster_processor` package."""
import pytest
import os
import homura
import tempfile
import timeout_decorator
import subprocess

from hex_raster_processor.contrast_stretch import GdalContrastStretch


@timeout_decorator.timeout(120)
def download_file(
    download_url: str,
    output_path: str = None
):
    """ Test function to download file for tests.

    Args:
        download_url (str): download url.
        output_path (str, optional): Path to output file.
            Defaults to None.

    Returns:
        str: path to downloaded file.
    """
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), 'test_file.tif')

    if not os.path.exists(output_path):
        homura.download(url=download_url, path=output_path)

    return output_path


@pytest.fixture
def downloaded_file():
    """ Test fixture to download image. """
    download_url = 'https://storage.googleapis.com/xskylab-data/data/' + \
        'application-tests/image_test.TIF'
    return download_file(download_url=download_url)


def test_contrast_stretch_command(downloaded_file):
    """ Test GdalContrastStretch get command. """
    contrast = GdalContrastStretch()
    assert contrast._get_contrast_command()
    assert 'gdal' in contrast._get_contrast_command()


def test_contrast_stretch_completed(downloaded_file):
    """ Test GdalContrastStretch get image method. """
    contrast = GdalContrastStretch()
    assert contrast.get_image(input_file=downloaded_file)


def test_contrast_stretch_without_input_file():
    """ Test GdalContrastStretch raise error for image with error. """
    contrast = GdalContrastStretch()
    with pytest.raises(subprocess.CalledProcessError):
        contrast.get_image(input_file='test.tif')
