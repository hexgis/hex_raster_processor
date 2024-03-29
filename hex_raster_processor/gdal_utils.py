#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import logging

from osgeo import ogr, osr

from .composer import Composer
from .utils import Utils
from .gdal_datasets import GdalDatasets
from .contrast_stretch import GdalContrastStretch

logger = logging.getLogger()


class GdalUtils(GdalDatasets):
    """Utility methods for Gdal processes and their results.

    Inherits from gdal_datasets::GdalDatasets to get
    get_color_text_file classmethod for color text files.
    """

    @classmethod
    def get_gdal_outsize_command(
        cls,
        scale: bool = True,
        quiet: bool = True
    ) -> str:
        """Returns a gdal translate command to resize image.

        Check https://gdal.org/programs/gdal_translate.html for more details.

        Arguments:
            scale (bool, optional): scale image. Defaults to True.
            quiet (bool, optional): show logs. Defaults to True.

        Returns:
            str: gdal translate shell command with string parameters.
                Parameters: x, y, img_format, input_path and output_path.
        """

        command = 'gdal_translate -ot Byte -outsize {x}% {y}%' \
            ' -of {img_format} {input_path} {output_path}'

        if scale:
            command += ' -scale '

        if quiet:
            command += ' -q '

        return command

    @classmethod
    def get_gdal_dem_color_command(cls) -> str:
        """Returns gdaldem command to create a colorized image.

        Check http://www.gdal.org/gdaldem.html for more details

        Returns:
            str: gdaldem color-relief shell command with string parameters.
                Parameters: input_path, color_text and output_path paramters
        """

        return 'gdaldem color-relief {input_path}' \
            ' {color_text} {output_path}'

    @classmethod
    def create_composition_thumbs(cls, ordered_filelist: list) -> tuple:
        """Creates a temporary preview for selected composition.

        Arguments:
            ordered_filelist (list): ordered image list for composition.

        Returns:
            tuple: path to created preview, temporary filename.
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
            log = (
                f'Error at GdalUtils create_compositon_thumbs '
                f'for {ordered_filelist} with exception: {exc}'
            )
            logger.exception(log)
            logger.exception(exc)
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
    ) -> str:
        """Creates thumbnails for input image.

        Uses gdal_translate shell command to create thumbnails.

        Args:
            input_image (str):  input file path.
            output_path (str): output_path filename in jpg format.
            size (list, optional): list of sizes in % X% Y%. Default: [5, 5].
                Defaults to [15, 15].
            img_format (str, optional): image output format.
                Defaults to 'JPEG'.
            scale (bool, optional): scale image. Defaults to True.
            quiet (bool, optional): show logs. Defaults to True.

        Raises:
            AssertionError: input image does not exists.
            ValueError: error while creating thumbs.

        Returns:
            str: path to created preview.
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
            Utils.subprocess(command)
        except AssertionError:
            log = (
                f'Input file does not exists. '
                f'Exception at GdalUtils.thumbs with params: '
                f'input_image={input_image}, output_path={output_path} '
                f'and size=[{size[0]},{size[1]}]'
            )
            logger.info(log)
            raise
        except Exception as exc:
            log = (
                f'Exception at GdalUtils.thumbs with params: '
                f'input_image={input_image}, output_path={output_path} '
                f'and size=[{size[0]},{size[1]}]'
            )
            logger.exception(log)
            logger.exception(exc)
            raise

        if os.path.exists(output_path):
            return output_path

    @staticmethod
    def composition_rgb_thumbs(
        ordered_images: list,
        output_path: str,
        size: list = [100, 100],
        scale: bool = True,
        quiet: bool = True
    ) -> str:
        """Generates a preview for ordered_images.

        Creates a composition using Composer from raster_processor.

        Args:
            ordered_images (list): ordered image list for composition.
            output_path (str): output_path filename in jpg format.
            size (list, optional): list of sizes in % X% Y%.
                Defaults to [100, 100].
            scale (bool, optional): scale image. Defaults to True.
            quiet (bool, optional): show logs. Defaults to True.

        Returns:
            str: path to created preview.
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
                img_format='GTiff',
                output_path=temp_files[img].name,
                x=size[0],
                y=size[1],
            )

            Utils.subprocess(thumbs_command)

            if os.path.exists(temp_files[img].name):
                files.append(temp_files[img].name)

        composition, _ = GdalUtils.create_composition_thumbs(files)

        if composition:
            files.append(composition)
            thumbs = GdalUtils.thumbs(
                input_image=composition,
                output_path=output_path
            )

        return thumbs or False

    @staticmethod
    def generate_footprint(
        image_filename: str,
        simplify: float = 0,
        output_type: str = 'wkt',
        EPSG: int = 4674
    ) -> str:
        """Generates footprint for input tif image in WKT format.

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

        Utils.subprocess('gdalwarp -dstnodata 0 -dstalpha -of GTiff ' +
                         image_filename + ' ' + temp_1.name)
        Utils.subprocess('gdal_translate -b mask -of vrt -a_nodata 0 ' +
                         temp_1.name + ' ' + temp_2.name)
        Utils.subprocess('gdal_translate -b 1 -of vrt -a_nodata 0 ' +
                         temp_2.name + ' ' + temp_3.name)
        Utils.subprocess('gdal_polygonize.py -8 ' + temp_3.name + ' -b 1 ' +
                         '-f "ESRI Shapefile" ' + footprint_path)

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
    def create_normalized_color_image(
        input_image: str,
        output_path: str,
        img_type: str = 'NDVI',
        contrasted: bool = True,
        quiet: bool = True
    ) -> str:
        """Creates normalized and colorized image.

        Args:
            input_image (str): input file path.
            output_path (str): output path where file will be stored.
            img_type (str, optional): image preview type.
                Defaults to 'NDVI'.
            contrasted (bool, optional): Apply contrast 0.02 - 0.98 on image.
                Defaults to True.
            quiet (bool, optional): runs on background. Defaults to False.

        Returns:
            str: path to colorized image.
        """

        if not quiet:
            print(f"-- Creating normalized and colorized image for"
                  f" {input_image} image in {output_path}")

        Utils.check_creation_folder(os.path.dirname(output_path))

        color_text_file = GdalUtils.get_color_text_file(img_type)
        command = GdalUtils.get_gdal_dem_color_command()

        if contrasted:
            temporary_file = tempfile.NamedTemporaryFile(
                prefix='contrasted_', suffix='.tif')

            command = command.format(
                input_path=input_image,
                color_text=color_text_file,
                output_path=temporary_file.name
            )

            Utils.subprocess(command)

            input_image = GdalContrastStretch.get_image(
                input_file=temporary_file.name,
                output_path=output_path
            )
        else:
            command = command.format(
                input_path=input_image,
                color_text=color_text_file,
                output_path=output_path
            )
            Utils.subprocess(command)

        return output_path

    @staticmethod
    def create_normalized_thumbs(
        input_image: str,
        output_path: str,
        size: list = [15, 15],
        img_format: str = 'JPEG',
        img_type: str = 'NDVI',
        contrasted: bool = True,
        scale: bool = False,
        quiet: bool = True
    ) -> str:
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
            contrasted (bool, optional): Apply contrast 0.02 - 0.98 on image.
                Defaults to True.
            scale (bool, optional): scale image. Defaults to False.
            quiet (bool, optional): runs on background. Defaults to True.

        Returns:
            str: path to created preview.
        """

        if not quiet:
            print(f"-- Creating thumbs for {input_image} in {output_path}")

        Utils.check_creation_folder(os.path.dirname(output_path))
        temp_file = tempfile.NamedTemporaryFile(prefix='fp', suffix='.tif')

        colorized_image = GdalUtils.create_normalized_color_image(
            input_image=input_image,
            output_path=temp_file.name,
            img_type=img_type,
            contrasted=contrasted,
            quiet=quiet
        )

        return GdalUtils.thumbs(
            input_image=colorized_image,
            output_path=output_path,
            scale=scale,
            size=size,
            img_format=img_format
        )
