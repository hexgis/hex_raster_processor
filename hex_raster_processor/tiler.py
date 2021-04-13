#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tiler module to create files as Tile Map service

      Uses package from https://github.com/vss-devel/tilers-tools
      to create tiles images for input tif.
      """

import os
import json
import subprocess

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
    def _get_image_info(cls, image_path):
        """
        Get info from raster using gdalinfo

        Arguments:
            * image_path: absolute image path

        Returns:
            * json data from gdalinfo command
        """
        command = 'gdalinfo -json {0}'.format(image_path)
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        return json.loads(proc.communicate()[0].decode())

    @classmethod
    def _get_tiler_command(cls):
        """Returns tiler command

        Returns:
            str: tiler shell command
        """
        return 'gdal_tiler.py {quiet} -p tms --src-nodata {nodata} ' + \
            '--zoom={min_zoom}:{max_zoom} -t {output_path} {input_image}'

    @classmethod
    def _convert_to_byte_scale(
        cls,
        input_image: str,
        output_folder: str = "~/tms/",
        quiet: bool = True
    ):
        """
        Translates raster using -ot Byte using gdal_merge

        Arguments:
            * input_image: image instance
            * output_folder: output folder for image

        Returns:
            * Image instance of output_image
        """

        command = 'gdal_translate {2} -ot Byte -scale {0} {1}'

        quiet_param = '-q'
        if not quiet:
            print('Converting image with command:\t {}'.format(command))
            quiet_param = ''

        image_name = '{}.TIF'.format(input_image.image_name)
        output_image_path = os.path.join(output_folder, image_name)
        output_image = Image(output_image_path)
        command = command.format(
            input_image.image_path, output_image.image_path, quiet_param
        )

        Utils._subprocess(command)
        Utils._print("Translate finished!", quiet=quiet)
        return output_image

    @classmethod
    def _generate_tms(
        cls,
        image_path: str,
        output_folder: str = "~/tms/",
        nodata: list = [0, 0, 0],
        zoom: list = [2, 15],
        quiet: bool = True
    ):
        """Generates TMS Pyramid for input image path.

        Args:
            image_path (str): path for image.
            output_folder (str, optional): output folder to store files.
                Defaults to "~/tms/".
            nodata (list, optional): nodata values.
                Must be same as source bands length.
                Defaults to [0, 0, 0].
            zoom (list, optional): Zoom levels. Defaults to [2, 15].
            quiet (bool, optional): show logs.
                Defaults to True.

        Raises:
            TMSError: for invalid datasource bands.

        Returns:
            str: output path to directory for processed tiles.
        """

        log = 'Validating image and bands with nodata info...'
        Utils._print(log, quiet=quiet)
        if not Utils.validate_image_bands(image_path, nodata):
            log = 'Validation error: check log for more details.'
            Utils._print(log, quiet=quiet)
            raise TMSError(1, 'Input image is not a valid datasource, ' +
                           'nodata length must be same as datasource bands')
        Utils._print('OK', quiet=quiet)

        quiet_param = '-q'

        if not quiet:
            quiet_param = ''

        command = Tiler._get_tiler_command()
        command = command.format(
            nodata=','.join(map(str, nodata)),
            output_path=output_folder,
            input_image=image_path,
            min_zoom=min(zoom),
            max_zoom=max(zoom),
            quiet=quiet_param,
        )

        log = 'Generating tiles with command: {}'.format(command)
        Utils._print(log, quiet=quiet)

        Utils._subprocess(command)

        log = 'Tiler process finished! Tiles Available on {}'.format(
            output_folder)
        Utils._print(log, quiet=quiet)

        return output_folder

    @classmethod
    def _generate_xml(
        cls, image_path, naming_image,
        base_link, output_folder="~/tms/", quiet=True
    ):
        """
        Generates XML for image on same path of image

        Arguments:
            * image_path: path for image
            * naming_image: names image as .xml extension
            * base_link: http for xml file
            * output_folder: folder for output xml

        Return:
            * Name of xml file
        """

        Utils._print("Getting info from image using gdalinfo...", quiet=quiet)

        try:
            image_info = Tiler._get_image_info(image_path=image_path)
            upper_left = image_info['cornerCoordinates']['upperLeft']
            lower_right = image_info['cornerCoordinates']['lowerRight']
            Utils._print("OK", quiet=quiet)
        except Exception as exc:
            raise XMLError(10, exc)

        target_window = "<TargetWindow>\n\
            <UpperLeftX>{0}</UpperLeftX>\n\
            <UpperLeftY>{1}</UpperLeftY>\n\
            <LowerRightX>{2}</LowerRightX>\n\
            <LowerRightY>{3}</LowerRightY>\n\
        </TargetWindow>".format(
            upper_left[0], upper_left[1], lower_right[0], lower_right[1])

        tms_xml = "<GDAL_WMS>\n\
            <Service name=\"TMS\">\n\
                <ServerUrl>{0}/{1}.tms/${{z}}/${{x}}/${{y}}.png</ServerUrl>\n\
                <SRS>EPSG:3857</SRS>\n\
                <ImageFormat>image/png</ImageFormat>\n\
            </Service>\n\
            <DataWindow>\n\
                <UpperLeftX>-20037508.34</UpperLeftX>\n\
                <UpperLeftY>20037508.34</UpperLeftY>\n\
                <LowerRightX>20037508.34</LowerRightX>\n\
                <LowerRightY>-20037508.34</LowerRightY>\n\
                <TileLevel>{2}</TileLevel>\n\
                <TileCountX>1</TileCountX>\n\
                <TileCountY>1</TileCountY>\n\
                <YOrigin>bottom</YOrigin>\n\
            </DataWindow>\n\
            {3}\n\
            <Projection>EPSG:3857</Projection>\n\
            <BlockSizeX>256</BlockSizeX>\n\
            <BlockSizeY>256</BlockSizeY>\n\
            <BandsCount>4</BandsCount>\n\
            <ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>\n\
            <ZeroBlockOnServerException>true</ZeroBlockOnServerException>\n\
            <Cache>\n\
                <Path>./gdalwmscache/cache_{4}.tms</Path>\n\
            </Cache>\n\
        </GDAL_WMS>".format(
            base_link, naming_image.image_name,
            15, target_window, naming_image.image_name
        )

        xml_name = naming_image.image_name + ".xml"
        xml = os.path.join(output_folder, xml_name)

        Utils._print("Creating xml file...", quiet=quiet)

        with open(xml, 'w') as f:
            f.write(tms_xml)

        Utils._print("OK", quiet)

        return xml_name

    @staticmethod
    def make_tiles(
        image_path, base_link, output_folder="~/tms/",
        zoom=[2, 15], nodata=[0, 0, 0], convert=True,
        move=False, quiet=True
    ):
        """
        Creates tiles for image using tilers-tools

        Arguments:
            * image_path: path for image
            * base_link: http url for xml file. E.g.: http://localhost
            * output_folder: folder for image and pyramid files
                default is '~/tms/'
            * zoom: list of zoom levels ([start, end])
            * nodata: nodata info, must be same number as source bands
            * convert: convert image to byte scale? Default is True
            * move: create files on temp, and move when process finish
        Returns:
            * pyramid data and xml data on output folder for zoom levels
        """
        input_image = Image(image_path)
        output_folder_name = Utils.check_creation_folder(output_folder)

        if move:
            output_folder_name = Utils.create_tempdir()

        if convert:
            converted_image = Tiler._convert_to_byte_scale(
                input_image=input_image,
                output_folder=output_folder_name,
                quiet=quiet
            )
        else:
            converted_image = input_image

        tms = Tiler._generate_tms(
            image_path=converted_image.image_path,
            output_folder=output_folder_name,
            nodata=nodata,
            zoom=zoom,
            quiet=quiet
        )

        if not base_link.endswith('/'):
            base_link = os.path.join(base_link, "")

        xml = Tiler._generate_xml(
            image_path=converted_image.image_path,
            naming_image=input_image,
            base_link=base_link,
            output_folder=output_folder_name,
            quiet=quiet
        )

        # Removing converted image file on output path
        if convert:
            converted_image.remove_file()

        tms_path = os.path.join(tms, converted_image.image_name + '.tms')
        xml_path = os.path.join(output_folder_name, xml)

        if move:
            try:
                output_final_path = Utils.check_creation_folder(output_folder)
                log = 'Trying to move files from {} and {} to {}'.format(
                    tms_path, xml_path, output_final_path)
                Utils._print(log, quiet=quiet)
                Utils.move_path_files(tms_path, output_final_path)
                Utils.move_path_files(xml_path, output_final_path)
                Utils._print('Move process finished', quiet=quiet)
                xml_path = os.path.join(output_final_path, xml)
                tms_path = os.path.join(output_final_path,
                                        converted_image.image_name + '.tms')
            except Exception as exc:
                print('Move process with error: {}'.format(exc))
                raise exc

        log = 'Tiles path: {}\nXML File: {}'.format(tms_path, xml)
        Utils._print(log, quiet=quiet)

        return (tms_path, xml_path)
