#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tiler module to create files as Tile Map service

Uses package from https://github.com/vss-devel/tilers-tools
to create tiles images for input tif.
"""

import os
import json
import subprocess

from . import exceptions
from . import contrast_stretch
from . import image_info
from . import utils

os.environ["PATH"] += ":{}".format(
    os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'tilers-tools')
)


class Tiler:
    """Class for tiler data using tiler-tools.

    Uses package from https://github.com/vss-devel/tilers-tools
    """

    @classmethod
    def _get_image_info(cls, image_path: str):
        """Get image info using `gdalinfo` as json data.

        Args:
            image_path (str): path to image.

        Returns:
            dict: json object from `gdalinfo -json` shell command.
        """
        command = 'gdalinfo -json {0}'.format(image_path)
        command = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE)
        return json.loads(command.communicate()[0].decode())

    @classmethod
    def _get_gdal_tiler_command(cls):
        """Returns gdal_tiler.py shell command.

        Returns:
            str: tiler shell command with string parameters.
                String parameters: quiet, nodata, min_zoom, max_zoom,
                    output_path and input_file.
        """
        return 'gdal_tiler.py {quiet} -p tms --src-nodata {nodata} ' + \
            '--zoom={min_zoom}:{max_zoom} -t {output_path} {input_file}'

    @classmethod
    def _get_gdal_translate_scale_command(cls):
        """Returns gdal_translate shell command.

        Returns:
            str: gdal_translate shell command with string parameters.
                String parameters: quiet, output_path and input_image.
        """
        return 'gdal_translate {quiet} -ot Byte -scale ' + \
            '{input_file} {output_path}'

    @classmethod
    def gdal_translate_byte_and_scale(
        cls,
        input_image: image_info.Image,
        output_path: str = None,
        quiet: bool = True
    ):
        """Translates raster using -ot Byte using gdal_merge.

        Args:
            input_image (image_info.Image):
                `hex_raster_processor.image_info.Image` instance.
            output_path (str, optional): Output path to file.
                If is None, will be created in temporary path.
                Defaults to None.
            quiet (bool, optional): show logs. Defaults to True.

        Returns:
            str: path to converted image.
        """
        quiet_param = ''
        if quiet:
            quiet_param = ' -q '

        if not output_path:
            output_path = input_image.get_tempfile()

        command = Tiler._get_gdal_translate_scale_command()
        command = command.format(
            input_file=input_image.image_path,
            output_path=output_path,
            quiet=quiet_param
        )
        log = 'Converting image with command:\t {}'.format(command)
        utils.Utils.print(log, quiet)

        utils.Utils.subprocess(command)
        utils.Utils.print('Translate finished!', quiet=quiet)
        return output_path

    @classmethod
    def create_tms(
        cls,
        image_path: str,
        output_folder: str = 'tms/',
        nodata: list = [0, 0, 0],
        zoom: list = [2, 15],
        quiet: bool = True
    ):
        """Private method to Generates TMS Pyramid for input image path.

        Args:
            image_path (str): path for image.
            output_folder (str, optional): output folder to store files.
                Defaults to 'tms/'.
            nodata (list, optional): nodata values.
                Must be same as source bands length.
                Defaults to [0, 0, 0].
            zoom (list, optional): Zoom levels. Defaults to [2, 15].
            quiet (bool, optional): show logs.
                Defaults to True.

        exceptions.TMSError: for invalid datasource bands.

        Returns:
            str: output path to directory for processed tiles.
        """

        log = 'Validating image and bands with nodata info...'
        utils.Utils.print(log, quiet=quiet)

        if not utils.Utils.validate_image_bands(image_path, nodata):
            log = (
                'Input image is not a valid datasource, '
                'nodata length must be same as datasource bands'
            )
            utils.Utils.print(log, quiet=quiet)
            raise exceptions.TMSError(1, log)

        utils.Utils.print('Done!\n', quiet=quiet)

        quiet_param = ''
        if quiet:
            quiet_param = ' -q '

        command = Tiler._get_gdal_tiler_command()
        command = command.format(
            nodata=','.join(map(str, nodata)),
            output_path=output_folder,
            input_file=image_path,
            min_zoom=min(zoom),
            max_zoom=max(zoom),
            quiet=quiet_param,
        )

        log = f'Generating tiles with command: {command}'
        utils.Utils.print(log, quiet=quiet)
        utils.Utils.subprocess(command)

        log = (
            f'Tiler process terminated!'
            f'Tiles Available on {output_folder}'
        )
        utils.Utils.print(log, quiet=quiet)

        return output_folder

    @classmethod
    def create_xml(
        cls,
        image_path: str,
        image: image_info.Image,
        base_link: str,
        max_zoom: int = 15,
        output_folder: str = 'tms/',
        quiet: bool = True
    ):
        """Generates XML file with link for TMS directory from base_link.

        Join base_link with TMS path to create link to service.

        Args:
            image_path (str): path to image.
            image (image_info.Image):
                `hex_raster_processor.image_info.Image` instance.
            base_link (str): base link that indicates where files
                will be available.
            max_zoom (int, optional): max zoom to image. Defaults to 15.
            output_folder (str, optional): output path. Defaults to 'tms/'.
            quiet (bool, optional): show logs. Defaults to True.

        Raises:
            exceptions.XMLError: image info could not be founded not.

        Returns:
            str: output path to xml file.
        """

        utils.Utils.print(
            'Getting info from image using gdalinfo...', quiet=quiet)

        if base_link.endswith('/'):
            base_link = os.path.join(base_link, '')

        try:
            image_data = Tiler._get_image_info(image_path=image_path)
            upper_left = image_data['cornerCoordinates']['upperLeft']
            lower_right = image_data['cornerCoordinates']['lowerRight']
            utils.Utils.print('Done!\n', quiet=quiet)
        except Exception as exc:
            raise exceptions.XMLError(1, exc)

        coordinates_data_window = (
            '\t\t<UpperLeftX>-20037508.34</UpperLeftX>\n'
            '\t\t<UpperLeftY>20037508.34</UpperLeftY>\n'
            '\t\t<LowerRightX>20037508.34</LowerRightX>\n'
            '\t\t<LowerRightY>-20037508.34</LowerRightY>'
        )

        coordinates_target_window = (
            f'\t\t<UpperLeftX> {upper_left[0]} </UpperLeftX>\n'
            f'\t\t<UpperLeftY> {upper_left[1]} </UpperLeftY>\n'
            f'\t\t<LowerRightX> {lower_right[0]} </LowerRightX>\n'
            f'\t\t<LowerRightY> {lower_right[1]} </LowerRightY>'
        )

        xml_data = (
            f'<GDAL_WMS>\n'
            f'\t<Service name="TMS">\n'
            f'\t\t<ServerUrl>{base_link}/{image.image_name}.tms/'
            f'${{z}}/${{x}}/${{y}}.png</ServerUrl>\n'
            f'\t\t<SRS>EPSG:3857</SRS>\n'
            f'\t\t<ImageFormat>image/png</ImageFormat>\n'
            f'\t</Service>\n'
            f'\t<DataWindow>\n'
            f'{coordinates_data_window}\n'
            f'\t\t<TileLevel>{max_zoom}</TileLevel>\n'
            f'\t\t<TileCountX>1</TileCountX>\n'
            f'\t\t<TileCountY>1</TileCountY>\n'
            f'\t\t<YOrigin>bottom</YOrigin>\n'
            f'\t</DataWindow>\n'
            f'\t<TargetWindow>\n'
            f'{coordinates_target_window}\n'
            f'\t</TargetWindow>\n'
            f'\t<Projection>EPSG:3857</Projection>\n'
            f'\t<BlockSizeX>256</BlockSizeX>\n'
            f'\t<BlockSizeY>256</BlockSizeY>\n'
            f'\t<BandsCount>4</BandsCount>\n'
            f'\t<ZeroBlockHttpCodes>'
            f'204,303,400,404,500,501'
            f'</ZeroBlockHttpCodes>\n'
            f'\t<ZeroBlockOnServerException>'
            f'true'
            f'</ZeroBlockOnServerException>\n'
            f'\t<Cache>\n'
            f'\t\t<Path>./gdalwmscache/cache_{image.image_name}.tms</Path>\n'
            f'\t</Cache>\n'
            f'</GDAL_WMS>'
        )

        filename = f'{image.image_name}.xml'
        output_path = os.path.join(output_folder, filename)

        utils.Utils.print('Creating xml file...', quiet=quiet)

        with open(output_path, 'w') as output_file:
            output_file.write(xml_data)

        utils.Utils.print('Done!', quiet)

        return filename

    @staticmethod
    def make_tiles(
        image_path: str,
        base_link: str,
        output_folder: str = 'tms/',
        zoom: list = [2, 15],
        nodata: list = [0, 0, 0],
        contrast: str = False,
        contrast_range: list = [0.02, 0.98],
        convert: bool = True,
        move: bool = False,
        quiet: bool = True
    ):
        """Generates tiles for input image creating Tile Map Service data.

        Uses tilers-tools package from
        dans-gdal-scripts (https://github.com/gina-alaska/dans-gdal-scripts/).

        Args:
            image_path (str): path to image
            base_link (str): base link to xml file where service
                will be available.
            output_folder (str, optional): output folder to store tms files.
                Defaults to 'tms/'.
            zoom (list, optional): min and max zoom. Defaults to [2, 15].
            nodata (list, optional): nodata value list. Lenght of nodata
                and bands list must be same. Defaults to [0, 0, 0].
            contrast_range (list, optional): list with contrast stretch
                values to cut image histogram, between 0.0 and 0.1.
                Defaults to [0.02, 0.98].
            convert (bool, optional): convert image using `-ot Byte` from
                `gdal_translate`. Defaults to True.
            move (bool, optional): Creates temporary folder to TMS images
                and move to final when process finishes. Defaults to False.
            quiet (bool, optional): show logs. Defaults to True.
            contrast (str, optional): apply contrast_range.
                Must be used with constrast_stretch argument.
                Defaults to False.

        Raises:
            exceptions.TMSError: move process error.

        Returns:
            tuple: TMS service name, XML name

        """
        input_image = image_info.Image(image_path)

        if convert:
            converted_image = Tiler.gdal_translate_byte_and_scale(
                input_image=input_image,
                output_path=input_image.get_tempfile(),
                quiet=quiet
            )
            converted_image = image_info.Image(converted_image)
        else:
            converted_image = input_image

        if contrast:
            contrasted_image = contrast_stretch.GdalContrastStretch.get_image(
                input_file=converted_image.image_path,
                output_path=converted_image.get_tempfile(),
                constrast_range=contrast_range
            )
            contrasted_image = image_info.Image(contrasted_image)
        else:
            contrasted_image = converted_image

        if move:
            output_folder_name = utils.Utils.create_tempdir()
        else:
            output_folder_name = utils.Utils.check_creation_folder(
                output_folder)

        tms = Tiler.create_tms(
            image_path=contrasted_image.image_path,
            output_folder=output_folder_name,
            nodata=nodata,
            zoom=zoom,
            quiet=quiet
        )

        xml = Tiler.create_xml(
            image_path=contrasted_image.image_path,
            image=input_image,
            base_link=base_link,
            max_zoom=max(zoom),
            output_folder=output_folder_name,
            quiet=quiet
        )

        if convert:
            converted_image.remove_file()

        tms_path = os.path.join(tms, f'{converted_image.image_name}.tms')
        xml_path = os.path.join(output_folder_name, xml)

        if move:
            output_path = utils.Utils.check_creation_folder(output_folder)
            log = (
                f'Trying to move files from '
                f'{tms_path} and {xml_path} to {output_path}'
            )
            try:
                utils.Utils.move_path_files(tms_path, output_path)
                utils.Utils.move_path_files(xml_path, output_path)
                utils.Utils.print(log, quiet=quiet)

                xml_path = os.path.join(output_path, xml)
                tms_path = os.path.join(
                    output_path, converted_image.image_name + '.tms')

                utils.Utils.print('Move process finished', quiet=quiet)
            except Exception as exc:
                log = 'Move process with error: {}'.format(exc)
                raise exceptions.TMSError(2, log)

        log = f'Tiles path: {tms_path}\nXML File: {xml}'
        utils.Utils.print(log, quiet=quiet)

        return tms_path, xml_path
