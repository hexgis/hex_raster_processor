#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

from .utils import Utils

logger = logging.getLogger()


class Composer:
    """Processes and creates image compositions using gdal
    from https://gdal.org/.
    """

    @classmethod
    def get_image_output_path(
        cls,
        filename: str,
        output_path: str,
        type_name: str
    ):
        """Returns output path for image composition.

        Args:
            filename (str): input filename.
            output_path (str): output path name.
            type_name (str): output type for image.
                E.g.: r6g5b4, r11g8b4.

        Returns:
            str: output_path joined with type name.
        """

        if filename.endswith('.TIF') or \
           filename.endswith('.tif') or \
           filename.endswith('.tiff') or \
           filename.endswith('.TIFF'):
            return os.path.join(output_path, filename)

        filename = '{}_{}.TIF'.format(filename, type_name)
        return os.path.join(output_path, filename)

    @classmethod
    def get_gdal_merge_command(cls):
        """Returns gdal merge shell command.

        docs available on https://gdal.org/programs/gdal_merge.html.

        Returns:
            str: shell command.
        """
        return 'gdal_merge.py {quiet} -separate -co PHOTOMETRIC=RGB ' + \
            '-o {output_path} '

    @staticmethod
    def create_composition(
        filename: str,
        ordered_filelist: str,
        output_path: str,
        bands: list,
        quiet: bool = True
    ):
        """Creates image composition using gdal merge with ordered filelist.

        docs available on https://gdal.org/programs/gdal_merge.html.

        Args:
            filename (str): output name for file.
                E.g.: my_file, my_file.tif
            ordered_filelist (str): list of images to merge.
            output_path (str): output path name for image.
            bands (list): list with bands numbers to create image number.
                E.g.: 6,5,4 -> r6g5b4
            quiet (bool, optional): show logs.
                Defaults to True.

        Returns:
            str: output path for merged image
        """

        type_name = 'r{0}g{1}b{2}'.format(*bands)

        file_path = Composer.get_image_output_path(
            filename=filename,
            output_path=output_path,
            type_name=type_name
        )

        quiet_param = ''

        if quiet:
            quiet_param = ' -q '
            log = 'Creating file composition from {} to {}'.format(
                filename, file_path)
            Utils._print(log, quiet=quiet)

        command = Composer.get_gdal_merge_command()
        command = command.format(quiet=quiet_param, output_path=file_path)
        command += ' '.join(map(str, ordered_filelist))

        for band in ordered_filelist:
            Utils.validate_band(band)

        Utils._subprocess(command)

        is_valid = Utils.validate_image_bands(file_path, ordered_filelist)

        if is_valid:
            return {
                'name': file_path.split('/')[-1],
                'path': file_path,
                'type': type_name
            }
