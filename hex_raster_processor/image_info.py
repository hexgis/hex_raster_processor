# -*- coding: utf-8 -*-

import os

from .utils import Utils


class Image:
    """Class for hex_raster_processor.Image.

    Used to create default methods to image from image_path as:
        - remove_file: deletes file from system files.
        - rename_file: rename file
    """

    def __init__(self, image_path):
        self._set_image_attributes(image_path)

    def _set_image_attributes(self, image_path: str):
        """Private method to set class Image attributes.

        Args:
            image_path (str): path to file to get path, dir and name.
        """
        self.image_path = os.path.abspath(image_path)
        self.image_dir = os.path.dirname(self.image_path)
        self.image_basename = os.path.basename(self.image_path)
        self.image_name = self.image_basename.split(".")[0]

    def get_tempfile(self):
        """ Returns temporary directory with Image.image_basename """
        return os.path.join(Utils.create_tempdir(), self.image_basename)

    def remove_file(self):
        """ Removes Image.image_path from system files. """
        os.remove(self.image_path)

    def rename_file(self, new_filename: str):
        """
        Renames Image.image_path using os.rename method to `new_filename`.

        Args:
            new_filename (str): filename.
        """
        new_path = os.path.join(self.image_dir, new_filename)
        os.rename(self.image_path, new_path)
        self._set_image_attributes(os.path.join(self.image_dir, new_filename))
