#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Utils used on raster_processor module. """

import os
import subprocess
import shutil
import tempfile

try:
    from osgeo import gdal
except ImportError as error:
    print("Error importing GDAL {}".format(error))
    subprocess.call("python --version", shell=True)
    import gdal


class Utils:
    """ Misc utility methods """

    @staticmethod
    def _print(msg: str, quiet: bool):
        """Used to print messages if quiet is False.

        Arguments:
            msg (str): message to print.
            quiet (bool): show logs.
        """
        if not quiet:
            print(msg)

    @staticmethod
    def _subprocess(command: str):
        """Void function to call subprocess run process.

        Arguments:
            command: command for subprocess
        """
        subprocess.run(command, shell=True, check=True)

    @staticmethod
    def remove_file(input_file: str):
        """Method to remove input_file from argument.

        Arguments:
            input_file (str): input file to remove

        Returns:
            bool: removed image
        """
        if os.path.exists(input_file):
            return os.remove(input_file)

    @staticmethod
    def move_path_files(
        src: str,
        dest: str,
        src_remove: bool = True
    ):
        """Void method to move files from source to destiny path arguments.

        Uses shutil to move entire directory.

        Arguments:
            src (str): source path
            dest (str): destination path
            src_remove (bool, optional): remove files after copy?
                Defaults: True
        """
        if os.path.isdir(src):
            dir_path = os.path.basename(src)
            if dir_path in os.listdir(dest):
                shutil.rmtree(os.path.join(dest, dir_path))
            shutil.move(src, dest)

        if os.path.isfile(src):
            shutil.copy(src, dest)

        if src_remove:
            if os.path.isdir(src):
                shutil.rmtree(src)
            else:
                Utils.remove_file(src)

    @staticmethod
    def create_tempdir(dir_name: str = None):
        """Creates temporary directory using tempfile.

        Arguments:
            dir_name (str, optional): name of directory

        Returns:
            str: path to temporary directory
        """
        if not dir_name:
            dir_name = os.path.join(
                tempfile.gettempdir(),
                next(tempfile._get_candidate_names())
            )

        os.makedirs(dir_name, exist_ok=True)

        return dir_name

    @staticmethod
    def check_creation_folder(directory):
        """Check whether a directory exists, if not the will be created.

        Arguments:
            directory (str): directory path

        Returns:
            str: path to directory.
        """
        if not os.path.exists(directory) and \
           not os.path.isdir(directory):
            os.makedirs(directory, check_exists=True)

        return directory

    @staticmethod
    def validate_image_bands(image_path: str, filelist: list):
        """Check if the image_path exists and check its bands.

        Will check if image_path is a valid datasource
        and number of bands is equals to filelist length.

        Arguments:
            image_path (str): image path
            data (list): images filelist

        Returns:
            bool: image validation
        """

        if not os.path.isfile(image_path):
            return False

        try:
            ds = gdal.Open(image_path)
        except Exception as exc:
            print(exc)
            return False

        return ds.RasterCount == len(filelist)
