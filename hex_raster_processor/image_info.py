# -*- coding: utf-8 -*-

import os


class Image:
    """ Image class used to remove, rename and set attributes for image. """

    def __init__(self, image_path: str):
        """Initializes `Image` with default image_path to validation.

        Args:
            image_path (str): path to image
        """
        self._set_attributes(image_path)

    def _set_attributes(self, image_path: str):
        """Set image_path, image_dir and image_name attributes for `Image`

        Set Image.set_atrtibutes path, dir and image_name

        Args:
            image_path (str): path to image to extract `Image` attributes
        """

        self.image_path = os.path.abspath(image_path)
        self.image_dir = os.path.dirname(self.image_path)
        self.image_name = os.path.basename(self.image_path).split(".")[0]

    def remove_file(self):
        """Remove file from system files using remove from os package """
        os.remove(self.image_path)

    def rename_file(self, dst_name: str):
        """Renames file using os.rename package

        Set Image.set_atrtibutes path, dir and image_name

        Args:
            dst_name (str): dst filename
        """
        new_path = os.path.join(self.image_dir, dst_name)
        os.rename(self.image_path, new_path)
        self._set_attributes(os.path.join(self.image_dir, dst_name))
