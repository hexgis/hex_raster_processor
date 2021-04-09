#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import logging

from osgeo import ogr, osr
from .composer import Composer
from .utils import Utils
from .gdal_datasets import GdalDatasets

logger = logging.getLogger()


class GdalUtils(GdalDatasets):
    """
    Utility methods for Gdal processes and their results

    Inherits from gdal_datasets::GdalDatasets to get
    get_color_text_file classmethod for color text files
    """

    @classmethod
    def get_gdal_outsize_command(
        cls,
        scale: bool = True,
        quiet: bool = True
    ):
        """
        Returns a gdal translate command to resize image.
        Check https://gdal.org/programs/gdal_translate.html for more details

        Arguments:
            scale (bool, optional): scale image
            quiet (bool, optional): show logs

        Returns:
            str: gdal translate command with format parameters.
                string params: x, y, img_format, input_path and output_path
        """
        command = 'gdal_translate -ot Byte -outsize {x}% {y}%' \
            ' -of {img_format} {input_path} {output_path}'

        if scale:
            command += ' -scale '

        if quiet:
            command += ' -q '

        return command

    @classmethod
    def get_gdal_dem_color_command(cls):
        """
        Returns a gdaldem command to create a colorized image
        check http://www.gdal.org/gdaldem.html for more details

        Returns:
            command (str): gdaldem color-relief command format
                Parameters: input, color_text and output paramters
        """
        return 'gdaldem color-relief -alpha ' + \
            '{input_path} {color_text} {output_path}'

    @classmethod
    def create_composition_thumbs(cls, ordered_images: list):
        """
        Creates a temporary thumbnails for selected composition

        Arguments:
            ordered_images (list): ordered image list for composition

        Returns:
            tuple: path to created thumbs, filename
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.tif', delete=False)
        output_path = tempfile.TemporaryDirectory()
        bands = [9, 9, 9]

        try:
            composition = Composer.create_composition(
                ordered_filelist=ordered_images,
                filename=temp_file.name,
                output_path=output_path.name,
                bands=bands
            )
        except Exception as exc:
            logger.log('Error at GdalUtils create_compositon_thumbs ' +
                       'for {} with exception: {}'.format(ordered_images, exc))
            raise

        return composition['path'], temp_file.name

    @staticmethod
    def thumbs(
        input_image: str,
        output_path: str,
        size: list = [15, 15],
        img_format: str = 'JPEG',
        scale: bool = True,
        quiet: bool = True
    ):
        """
        Creates thumbnails for tif input image in JPEG format

        Arguments:
            input_image (str): input file path
            output_path (str): output_path filename in jpg format
            size (list): list of sizes in % X% Y%. Default: [5, 5]

        Returns:
            thumbs (str): JPEG path to created preview
        """
        try:
            assert os.path.exists(input_image)
            command = GdalUtils.get_gdal_outsize_command(
                quiet=quiet, scale=scale
            )
            command = command.format(
                input_path=input_image,
                img_format=img_format,
                output_path=output_path,
                x=size[0],
                y=size[1]
            )
            subprocess.call(command, shell=True)
        except AssertionError as exc:
            print("Input file does not exists "
                  "Exception at GdalUtils.thumbs with params: "
                  "input_image={} output_path= {} and size=[{},{}]".format(
                      input_image, output_path, size[0], size[1]))
            raise ValueError(exc)
        except Exception as exc:
            print("Exception at GdalUtils.thumbs with params: "
                  "input_image={} output_path= {} and size=[{},{}]".format(
                      input_image, output_path, size[0], size[1]))
            raise ValueError(exc)

        if os.path.exists(output_path):
            return output_path

        return False

    @staticmethod
    def composition_rgb_thumbs(
        ordered_images,
        output_path,
        size=[100, 100],
        scale=True,
        quiet=True
    ):
        """
        Generates a thumbnail for images on JPEG format
        Creates a composition using Composer from raster_processor

        Arguments:
            ordered_images (list): ordered image list for composition
            output_path (str): output path to file in jpg format
            size (list): list of sizes in % X% Y%. Default: [5, 5]
            scale (bool): scale image
            quiet (bool): verbose logs

        Returns:
            A jpeg thumbnail
        """
        files = []
        temp_files = dict()
        command = GdalUtils.get_gdal_outsize_command(
            quiet=quiet, scale=scale
        )

        for img in ordered_images:

            temp_files[img] = tempfile.NamedTemporaryFile(
                prefix='cmp', suffix='.tif'
            )
            thumbs_command = command.format(
                input_path=img,
                img_format="GTiff",
                output_path=temp_files[img].name,
                x=size[0],
                y=size[1],
            )
            subprocess.call(thumbs_command, shell=True)

            if os.path.exists(temp_files[img].name):
                files.append(temp_files[img].name)

        composition, _ = GdalUtils.create_composition_thumbs(files)

        if composition:
            files.append(composition)
            thumbs = GdalUtils.thumbs(
                input_image=composition, output_path=output_path
            )

        return thumbs or False

    @staticmethod
    def generate_footprint(
        image_filename,
        simplify=None,
        out_type='wkt',
        EPSG=4674
    ):
        """
        Generates footprint for input tif image in WKT format

        Arguments:
            image_filename (str): path to file
            simplifly (float): number of distance tolerance for
                simplification
            out_type (str): output data format. E.g.: WKT/JSON

        Returns:
            geom (str): parsed geometry
        """
        temp_1 = tempfile.NamedTemporaryFile(prefix='fp', suffix='.tif')
        temp_2 = tempfile.NamedTemporaryFile(prefix='fp', suffix='.vrt')
        temp_3 = tempfile.NamedTemporaryFile(prefix='fp', suffix='.vrt')
        temp_dir = tempfile.TemporaryDirectory()

        footprint_path = os.path.join(
            temp_dir.name,
            next(tempfile._get_candidate_names()) + '.shp')

        subprocess.call('gdalwarp -dstnodata 0 -dstalpha -of GTiff ' +
                        image_filename + ' ' + temp_1.name, shell=True)
        subprocess.call('gdal_translate -b mask -of vrt -a_nodata 0 ' +
                        temp_1.name + ' ' + temp_2.name, shell=True)
        subprocess.call('gdal_translate -b 1 -of vrt -a_nodata 0 ' +
                        temp_2.name + ' ' + temp_3.name, shell=True)
        subprocess.call('gdal_polygonize.py -8 ' + temp_3.name + ' -b 1 ' +
                        '-f "ESRI Shapefile" ' + footprint_path, shell=True)

        dataset = ogr.Open(footprint_path)
        layer = dataset.GetLayer()
        feature = layer[0]
        geom = feature.GetGeometryRef()

        in_spatial_ref = layer.GetSpatialRef()
        out_spatial_ref = osr.SpatialReference()
        out_spatial_ref.ImportFromEPSG(EPSG)
        coord_transf = osr.CoordinateTransformation(in_spatial_ref,
                                                    out_spatial_ref)
        if simplify:
            geom = geom.Simplify(simplify)

        geom.Transform(coord_transf)

        if out_type == 'wkt':
            output = geom.ExportToWkt()
        elif out_type == 'json':
            output = geom.ExportToJson()
        return output

    @staticmethod
    def create_normalized_thumbs(
        input_image,
        output_path,
        size=[5, 5],
        img_format='JPEG',
        img_type='NDVI',
        scale=False,
        quiet=True
    ):
        """
        *Creates thumbnails for tif input image in JPEG format*

        Used only to create ndvi thumbs because scale parameter
        is no applicable to default thumbs

        Arguments:
            input_image (str): input file path
            output_path (str): output path where file will be saved
            size (list): list of sizes in % X% Y%. Default: [5, 5]
            img_format (str): output image format. Default is: 'JPEG'
            img_type (str): type of image to create thumbs. Default: 'NDVI'
            scale (bool): scale image
            quiet (bool): verbose logs

        Returns:
            thumbs (str): JPEG path to created preview
        """
        if not quiet:
            log = "-- Creating NDVI thumbs for {} image in {}"
            print(log.format(input_image, output_path))

        Utils.check_creation_folder(os.path.dirname(output_path))  # Check dir

        color_text_file = GdalUtils.get_color_text_file(img_type)
        temp_file = tempfile.NamedTemporaryFile(prefix='fp', suffix='.tif')

        command = GdalUtils.get_gdal_dem_color_command()
        command = command.format(
            input_path=input_image,
            color_text=color_text_file,
            output_path=temp_file.name
        )
        Utils._subprocess(command)

        return GdalUtils.thumbs(
            input_image=temp_file.name,
            output_path=output_path,
            scale=scale,
            size=size,
            img_format=img_format
        )
