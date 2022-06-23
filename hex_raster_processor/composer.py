#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import tempfile
import shutil

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

        filename = f'{filename}_{type_name}.TIF'
        return os.path.join(output_path, filename)

    @classmethod
    def get_temporary_filename(cls):
        """Get temporary filename from tempfile package.

        Returns tempfile._get_candidate_names() joined with tempdir.

        Returns:
            str: temporary filename.
        """
        return os.path.join(
            tempfile._get_default_tempdir(),
            next(tempfile._get_candidate_names())
        )

    @classmethod
    def delete_temporary_file(cls, filepath: str):
        """Delete filepath using shutil package.

        Args:
            filepath (str): path to file

        Returns:
            bool: file removed.
        """
        if os.path.exists(filepath) and os.path.isfile(filepath):
            os.remove(filepath)

        return os.path.exists(filepath) and os.path.isfile(filepath)

    @classmethod
    def get_gdal_translate_8bits_command(cls):
        """Returns gdal merge shell command.

        docs available on https://gdal.org/programs/gdal_merge.html.

        Returns:
            str: shell command.
        """
        return 'gdal_translate -of GTiff -ot Byte -scale 0 65535 ' + \
            '0 255 {quiet} {input_path} {output_path}'

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
        scale: bool = True,
        quiet: bool = True
    ):
        """Creates image composition using gdal merge with ordered filelist.

        docs available on https://gdal.org/programs/gdal_merge.html.

        Args:
            filename (str): output filename.
            ordered_filelist (str): input filelist to create composition.
            output_path (str): output dir to save file.
            bands (list): list of bands to create image name.
                E.g.: [6,5,4] returns r6g5b4.TIF filename.
            scale (bool, optional): Scale image to 8 bits. Defaults to True.
            quiet (bool, optional): don't show proces logs. Defaults to True.

        Raises:
            ValidationBandError: error while reading ordered_filelist.

        Returns:
            str: output path to created file.
        """
        type_name = f'r{bands[0]}g{bands[1]}b{bands[2]}'

        for band in ordered_filelist:
            Utils.validate_band(band)

        filepath = Composer.get_image_output_path(
            filename=filename,
            output_path=output_path,
            type_name=type_name
        )

        quiet_param = ''
        if quiet:
            quiet_param = ' -q '
            logger.info(
                msg=f'Creating composition from {filename} to {filepath}'
            )

        merged_file = Composer.get_temporary_filename()
        command = Composer.get_gdal_merge_command()
        command = command.format(
            quiet=quiet_param,
            output_path=merged_file
        )
        command += ' '.join(map(str, ordered_filelist))
        Utils.subprocess(command)
        temporary_file = merged_file

        if scale:
            scale_file = Composer.get_temporary_filename()
            command = Composer.get_gdal_translate_8bits_command()
            command = command.format(
                quiet=quiet_param,
                input_path=merged_file,
                output_path=scale_file
            )
            Utils.subprocess(command)
            temporary_file = scale_file

        shutil.move(temporary_file, filepath)

        if scale_file:
            Composer.delete_temporary_file(scale_file)

        Composer.delete_temporary_file(merged_file)

        if Utils.validate_image_bands(filepath, ordered_filelist):
            return {
                'name': filepath.split('/')[-1],
                'path': filepath,
                'type': type_name
            }
