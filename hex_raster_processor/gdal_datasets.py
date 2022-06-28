#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile


class GdalDatasets:
    """Default datasets for GdalDem process.

    Contains default datasets for gdal processes including color text files.
    """

    @classmethod
    def get_color_text_file(cls, image_type="NDVI"):
        """Creates tempfile with color_text file data.

        Check http://www.gdal.org/gdaldem.html for more details.

        Args:
            img_type (str, optional): type of image to get text file.
                Must be in ['NDVI', 'NDWI', 'NBR', 'NDMI', 'NDSI', 'NPCRI'].

        Returns:
            str: path to temporary file
        """

        if image_type.lower() == 'ndvi':
            filetext = \
                '-0.2 4, 157, 222 \n' \
                '-0.1 115, 164, 166 \n' \
                '0.0 225, 172, 111 \n' \
                '0.1 254, 201, 129 \n' \
                '0.2 255, 237, 171 \n' \
                '0.3 235, 247, 173 \n' \
                '0.4 196, 230, 135 \n' \
                '0.5 150, 210, 101 \n' \
                '0.6 88, 180, 83 \n' \
                '0.7 26, 150, 65 \n' \
                'nv 0 0 0 0\n'

        if image_type.lower() == 'ndwi':
            filetext = \
                '-1 0, 0, 0\n' \
                '-0.68 234, 48, 51\n' \
                '-0.65 215, 96, 98\n' \
                '-0.45 246, 144, 83\n' \
                '-0.35 254, 190, 116\n' \
                '-0.25 255, 223, 154\n' \
                '0.00 255, 255, 191\n' \
                '0.02 222, 242, 180\n' \
                '0.05 188, 228, 170\n' \
                '0.09 145, 203, 169\n' \
                '0.17 94, 167, 177\n' \
                '0.23 43, 131, 186\n' \
                '0.30 43, 76, 222\n' \
                '0.4 22, 0, 221\n' \
                'nv 0 0 0\n'

        if image_type.lower() == 'nbr':
            filetext = \
                '-0.05 166, 81, 11\n' \
                '0 195, 95, 13\n' \
                '0.05 224, 110, 15\n' \
                '0.10 253, 124, 17\n' \
                '0.15 252, 171, 15\n' \
                '0.20 248, 222, 12\n' \
                '0.25 224, 243, 13\n' \
                '0.30 166, 216, 23\n' \
                '0.35 109, 188, 34\n' \
                '0.40 51, 160, 44\n' \
                'nv 0 0 0\n'

        if image_type.lower() == 'ndmi':
            filetext = \
                '-0.055 222, 0, 0\n' \
                '-0.015 237, 68, 7\n' \
                '0.024 252, 137, 15\n' \
                '0.063 255, 194, 16\n' \
                '0.102 255, 247, 15\n' \
                '0.142 205, 229, 12\n' \
                '0.181 154, 211, 9\n' \
                '0.221 102, 193, 6\n' \
                '0.26 51, 174, 3\n' \
                '0.3 0, 156, 0\n' \
                'nv 0 0 0\n'

        if image_type.lower() == 'ndsi':
            filetext = \
                '-1 220, 0, 11\n' \
                '0 230, 66, 75 \n' \
                '0.1 239, 133, 139 \n' \
                '0.2 248, 200, 203 \n' \
                '0.3 242, 242, 255 \n' \
                '0.4 161, 161, 255 \n' \
                '0.5 80, 80, 255 \n' \
                '0.6 0, 0, 255\n' \
                'nv 0 0 0\n'

        if image_type.lower() == 'npcri':
            filetext = \
                '-0.1081 79, 155, 40\n' \
                '-0.0963 107, 150, 36\n' \
                '-0.0845 136, 146, 33\n' \
                '-0.0727 164, 141, 29\n' \
                '-0.0609 192, 136, 26\n' \
                '-0.0491 220, 131, 22\n' \
                '-0.0372 249, 126, 18\n' \
                '-0.0254 251, 183, 14\n' \
                '-0.0136 243, 247, 10\n' \
                '-0.0018 204, 164, 10\n' \
                '0.01 166, 81, 11\n' \
                'nv 0 0 0\n'

        filename = os.path.join(
            tempfile._get_default_tempdir(),
            next(tempfile._get_candidate_names())
        )

        with open(filename, 'w') as outputfile:
            outputfile.write(filetext)

        return filename
