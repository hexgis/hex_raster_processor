#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tiler module to create files as Tile Map service

Uses package from https://github.com/vss-devel/tilers-tools
to create tiles images for input tif.
"""

import os
import json
import subprocess

from .contrast_stretch import GdalContrastStretch
from .exceptions import TMSError, XMLError
from .image_info import Image
from .utils import Utils

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
                    output_path and input_image.
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
        input_image: Image,
        output_path: str = None,
        quiet: bool = True
    ):
        """Translates raster using -ot Byte using gdal_merge.

        Args:
            input_image (Image): `hex_raster_processor.Image` instance.
            output_path (str, optional): Output path.
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
        Utils._print(log, quiet)

        Utils._subprocess(command)
        Utils._print('Translate finished!', quiet=quiet)
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

        TMSError: for invalid datasource bands.

        Returns:
            str: output path to directory for processed tiles.
        """

        log = 'Validating image and bands with nodata info...'
        Utils._print(log, quiet=quiet)

        if not Utils.validate_image_bands(image_path, nodata):
            log = 'Input image is not a valid datasource, ' + \
                'nodata length must be same as datasource bands'
            Utils._print(log, quiet=quiet)
            raise TMSError(1, log)

        Utils._print('Done!\n', quiet=quiet)

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

        log = 'Generating tiles with command: {}'.format(command)
        Utils._print(log, quiet=quiet)

        Utils._subprocess(command)

        log = 'Tiler process finished!' + \
            'Tiles Available on {}'.format(output_folder)
        Utils._print(log, quiet=quiet)

        return output_folder

    @classmethod
    def create_xml(
        cls,
        image_path: str,
        image: Image,
        base_link: str,
        max_zoom: int = 15,
        output_folder: str = 'tms/',
        quiet: bool = True
    ):
        """Generates XML file with link for TMS directory from base_link.

        Join base_link with TMS path to create link to service.

        Args:
            image_path (str): path to image.
            image (Image): `hex_raster_processor.Image` instance.
            base_link (str): base link that indicates where files
                will be available.
            max_zoom (int, optional): max zoom to image. Defaults to 15.
            output_folder (str, optional): output path. Defaults to 'tms/'.
            quiet (bool, optional): show logs. Defaults to True.

        Raises:
            XMLError: image info could not be founded not.

        Returns:
            str: output path to xml file.
        """

        Utils._print('Getting info from image using gdalinfo...', quiet=quiet)

        if base_link.endswith('/'):
            base_link = os.path.join(base_link, '')

        try:
            image_info = Tiler._get_image_info(image_path=image_path)
            upper_left = image_info['cornerCoordinates']['upperLeft']
            lower_right = image_info['cornerCoordinates']['lowerRight']
            Utils._print('Done!\n', quiet=quiet)
        except Exception as exc:
            raise XMLError(1, exc)

        coordinates = "<UpperLeftX> {0} </UpperLeftX >\n\
            <UpperLeftY> {1} </UpperLeftY>\n\
            <LowerRightX> {2} </LowerRightX>\n\
            <LowerRightY> {3} </LowerRightY>\n"\
        .format(
            upper_left[0],
            upper_left[1],
            lower_right[0],
            lower_right[1]
        )

        xml_data = '<GDAL_WMS>\n\
            <Service name="TMS">\n\
                <ServerUrl>{0}/{1}.tms/${{z}}/${{x}}/${{y}}.png</ServerUrl>\n\
                <SRS>EPSG:3857</SRS>\n\
                <ImageFormat>image/png</ImageFormat>\n\
            </Service>\n\
            <DataWindow>\n\
                {3}\n\
                <TileLevel>{2}</TileLevel>\n\
                <TileCountX>1</TileCountX>\n\
                <TileCountY>1</TileCountY>\n\
                <YOrigin>bottom</YOrigin>\n\
            </DataWindow>\n\
            <TargetWindow>\n\
                {3}\n\
            </TargetWindow>\n\
            <Projection>EPSG:3857</Projection>\n\
            <BlockSizeX>256</BlockSizeX>\n\
            <BlockSizeY>256</BlockSizeY>\n\
            <BandsCount>4</BandsCount>\n\
            <ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>\n\
            <ZeroBlockOnServerException>true</ZeroBlockOnServerException>\n\
            <Cache>\n\
                <Path>./gdalwmscache/cache_{4}.tms</Path>\n\
            </Cache>\n\
        </GDAL_WMS>'.format(
            base_link,
            image.image_name,
            max_zoom,
            coordinates,
            image.image_name
        )

        filename = image.image_name + '.xml'
        output_path = os.path.join(output_folder, filename)

        Utils._print('Creating xml file...', quiet=quiet)

        with open(output_path, 'w') as f:
            f.write(xml_data)

        Utils._print('Done!\n', quiet)

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
            TMSError: move process error.

        Returns:
            tuple: TMS service name, XML name

        """
        input_image = Image(image_path)

        if convert:
            converted_image = Tiler.gdal_translate_byte_and_scale(
                input_image=input_image,
                output_path=input_image.get_tempfile(),
                quiet=quiet
            )
            converted_image = Image(converted_image)
        else:
            converted_image = input_image

        if contrast:
            contrasted_image = GdalContrastStretch.get_image(
                input_file=converted_image.image_path,
                output_path=converted_image.get_tempfile(),
                constrast_range=contrast_range
            )
            contrasted_image = Image(contrasted_image)
        else:
            contrasted_image = converted_image

        if move:
            output_folder_name = Utils.create_tempdir()
        else:
            output_folder_name = Utils.check_creation_folder(output_folder)

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

        tms_path = os.path.join(tms, converted_image.image_name + '.tms')
        xml_path = os.path.join(output_folder_name, xml)

        if move:
            output_path = Utils.check_creation_folder(output_folder)
            log = 'Trying to move files from {} and {} to {}'.format(
                tms_path, xml_path, output_path)

            try:
                Utils.move_path_files(tms_path, output_path)
                Utils.move_path_files(xml_path, output_path)
                Utils._print(log, quiet=quiet)

                xml_path = os.path.join(output_path, xml)
                tms_path = os.path.join(
                    output_path, converted_image.image_name + '.tms')

                Utils._print('Move process finished', quiet=quiet)
            except Exception as exc:
                log = 'Move process with error: {}'.format(exc)
                raise TMSError(2, log)

        log = 'Tiles path: {}\nXML File: {}'.format(tms_path, xml)
        Utils._print(log, quiet=quiet)

        return tms_path, xml_path
