#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile

from osgeo import ogr, osr

from .composer import Composer
from .utils import Utils
from .gdal_datasets import GdalDatasets


class GdalUtils(GdalDatasets):
    """
    Utility methods for Gdal processes and their results.

    Inherits from gdal_datasets::GdalDatasets to get
    get_color_text_file classmethod for color text files.
    """

    @classmethod
    def get_gdal_outsize_command(
        cls,
        scale: bool = True,
        quiet: bool = True
    ):
        """Returns a gdal translate command to resize the image.

        Check https://gdal.org/programs/gdal_translate.html for more details.

        Arguments:
            scale (bool, optional): scale image
            quiet (bool, optional): show logs

        Returns:
            str: gdal translate shell command with string parameters
                Parameters: x, y, img_format, input_path and output_path
        """
        command = 'gdal_translate -ot Byte -outsize {x}% {y}%' \
            ' -of {img_format} {input_path} {output_path}'

        if scale:
            command = command + ' -scale'

        if quiet:
            command = command + ' -q'

        return command

    @classmethod
    def get_gdal_dem_color_command(cls):
        """Returns a gdaldem command to create a colorized image.

        check http://www.gdal.org/gdaldem.html for more details

        Returns:
            str: gdaldem color-relief shell command with string parameters.
                Parameters: input_path, color_text and output_path paramters
        """
        return 'gdaldem color-relief -alpha {input_path}' \
            ' {color_text} {output_path}'

    @classmethod
    def create_composition_thumbs(cls, ordered_filelist: list):
        """Creates a temporary preview for selected composition.

        Arguments:
            ordered_filelist (list): ordered image list for composition

        Returns:
            tuple: path to created preview, temporary filename
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.tif', delete=False)
        output_path = tempfile.TemporaryDirectory()
        bands = [9, 9, 9]

        try:
            composition = Composer.create_composition(
                ordered_filelist=ordered_filelist,
                filename=temp_file.name,
                output_path=output_path.name,
                bands=bands
            )
        except Exception as exc:
            print('Error at GdalUtils create_compositon_thumbs '
                  'for {} with exception: {}'.format(ordered_filelist, exc))
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
        """Creates thumbnails for input image in JPEG format
        using gdal_translate shell command.

        Args:
            input_image (str):  input file path
            output_path (str): output_path filename in jpg format
            size (list, optional): list of sizes in % X% Y%. Default: [5, 5].
                Defaults to [15, 15].
            img_format (str, optional): output_path format. Defaults to 'JPEG'.
            scale (bool, optional): scale image. Defaults to True.
            quiet (bool, optional): show logs. Defaults to True.

        Raises:
            AssertionError: input image does not exists.
            ValueError: error while creating thumbs.

        Returns:
            str: path to created preview
        """
        try:
            assert os.path.exists(input_image)
            command = GdalUtils.get_gdal_outsize_command(
                quiet=quiet, scale=scale
            )
            command = command.format(
                input=input_image,
                img_format=img_format,
                output_path=output_path,
                x=size[0],
                y=size[1]
            )
            subprocess.call(command, shell=True)
        except AssertionError as exc:
            print('Input file does not exists '
                  'Exception at GdalUtils.thumbs with params: '
                  'input_image={} output_path= {} and size=[{},{}]'.format(
                      input_image, output_path, size[0], size[1]))
            raise
        except Exception as exc:
            print('Exception at GdalUtils.thumbs with params: '
                  'input_image={} output_path= {} and size=[{},{}]'.format(
                      input_image, output_path, size[0], size[1]))
            raise

        if os.path.exists(output_path):
            return output_path

        return False

    @staticmethod
    def composition_rgb_thumbs(
        ordered_images: list,
        output_path: str,
        size: list = [100, 100],
        scale: bool = True,
        quiet: bool = True
    ):
        """Generates a preview for ordered_images.

        Creates a composition using Composer from raster_processor.

        Args:
            ordered_images (list): ordered image list for composition
            output_path (str): output_path filename in jpg format
            size (list, optional): list of sizes in % X% Y%.
                Defaults to [100, 100].
            scale (bool, optional): scale image. Defaults to True.
            quiet (bool, optional): show logs. Defaults to True.

        Returns:
            str: path to created preview
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
                input=img,
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
        image_filename: str,
        simplify: float: 0,
        output_type: str = 'wkt',
        EPSG: int = 4674
    ):
        """
        Generates footprint for input tif image in WKT format

        Arguments:
            image_filename (str): 
            simplifly (float): 
            output_type (str): 

        Returns:
            geom (str): parsed geometry

        Args:
            image_filename (str): path to file.
            simplify (float): number of distance tolerance for geometry
                simplification.
            output_type (str, optional): output data format. E.g.: WKT/JSON.
                Defaults to 'wkt'.
            EPSG (int, optional): SRID. Defaults to 4674.

        Returns:
            str: footprint data.
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
        coord_transf = osr.CoordinateTransformation(
            in_spatial_ref, out_spatial_ref)

        if simplify:
            geom = geom.Simplify(simplify)

        geom.Transform(coord_transf)

        if output_type == 'wkt':
            output_path = geom.ExportToWkt()
        elif output_type == 'json':
            output_path = geom.ExportToJson()

        return output_path

    @staticmethod
    def create_normalized_thumbs(
        input_image: str,
        output_path: str,
        size: list = [15, 15],
        img_format: str = 'JPEG',
        img_type: str = 'NDVI',
        scale: bool = False,
        quiet: bool = True
    ):
        """Creates preview for input image in JPEG `img_format`.

        Do not use in case of default composition thumbs.

        Used only to create normalized thumbs that adds scale parameter
        to command. 

        Args:
            input_image (str): input file path.
            output_path (str): output path where file will be stored.
            size (list, optional):list of sizes in % X% Y%.
                Defaults to [15, 15].
            img_format (str, optional): output image format.
                Defaults to 'JPEG'.
            img_type (str, optional): image preview type. Defaults to 'NDVI'.
            scale (bool, optional): scale image. Defaults to False.
            quiet (bool, optional): [description]. Defaults to True.

        Returns:
            str: path to created preview.
        """
        if not quiet:
            log = "-- Creating NDVI thumbs for {} image in {}"
            print(log.format(input_image, output_path))

        Utils.check_creation_folder(os.path.dirname(output_path))  # Check dir

        color_text_file = GdalUtils.get_color_text_file(img_type)
        temp_file = tempfile.NamedTemporaryFile(prefix='fp', suffix='.tif')

        command = GdalUtils.get_gdal_dem_color_command()
        command = command.format(
            input=input_image,
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
