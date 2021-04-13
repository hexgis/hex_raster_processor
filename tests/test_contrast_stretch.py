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
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), 'test_file.tif')

    if not os.path.exists(output_path):
        homura.download(url=download_url, path=output_path)

    return output_path


@pytest.fixture
def downloaded_file():
    download_url = 'https://storage.googleapis.com/xskylab-data/data/' + \
        'application-tests/image_test.TIF'
    return download_file(download_url)


def test_contrast_stretch_command(downloaded_file):
    contrast = GdalContrastStretch()
    assert contrast._get_contrast_command()
    assert 'gdal' in contrast._get_contrast_command()


def test_contrast_stretch_completed(downloaded_file):
    contrast = GdalContrastStretch()
    assert contrast.get_image(input_file=downloaded_file)


def test_contrast_stretch_without_input_file():
    contrast = GdalContrastStretch()
    with pytest.raises(subprocess.CalledProcessError):
        contrast.get_image(input_file='test.tif')
