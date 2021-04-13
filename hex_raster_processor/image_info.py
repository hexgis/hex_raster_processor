# -*- coding: utf-8 -*-

import os


class Image:
    """ Class for hex_raster_processor.Image.

    Used to create default methods to image from image_path as:
        - remove_file: deletes file from system files.
        - rename_file: rename file
    """

    def __init__(self, image_path):
        self.set_attributes(image_path)

    def remove_file(self):
        """ Removes file from system files. """
        os.remove(self.image_path)

    def rename_file(self, new_filename: str):
        """
        Renames file using os.rename method.

        Args:
            new_filename (str): filename.
        """
        new_path = os.path.join(self.image_dir, new_filename)
        os.rename(self.image_path, new_path)
        self.set_attributes(os.path.join(self.image_dir, new_filename))

    def set_attributes(self, image_path: str):
        """
        Set class Image attributes.

        Args:
            image_path (str): path to file to get path, dir and name.
        """
        self.image_path = os.path.abspath(image_path)
        self.image_dir = os.path.dirname(self.image_path)
        self.image_name = os.path.basename(self.image_path).split(".")[0]
