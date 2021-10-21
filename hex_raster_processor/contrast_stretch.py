import os
import tempfile
import subprocess
import logging

logger = logging.getLogger()


class GdalContrastStretch:
    """Support class to generate contrasted image.

    Use dans-gdal-scripts (https://github.com/gina-alaska/dans-gdal-scripts/).
    """

    @classmethod
    def _get_contrast_command(cls):
        """Returns contrast stretch shell command.

        Returns:
            str: gdal_constrast_stretch shell command.
        """
        return 'gdal_contrast_stretch -ndv {nodata} ' + \
            '-percentile-range {constrast_range} {input_file} {output_path}'

    @classmethod
    def _run_process(cls, command: str):
        """Returns subprocess.run execution.

        Args:
            command (str): string command.

        Returns:
            subprocess.Run: subprocess.run process.
        """
        return subprocess.run(command, shell=True, check=True)

    @staticmethod
    def get_image(
        input_file: str,
        output_path: str = None,
        constrast_range: list = [0.02, 0.98],
        nodata: int = 0
    ):
        """Gets constrasted image from input_file.

        Uses constrast_range and nodatavalue and returns a 8 bit image
        with cutted histogram.

        Args:
            input_file (str): path to input file.
            output_path (str, optional): output path.
                Creates tempfile if output_path is None. Defaults to None.
            constrast_range (list, optional): Contrast range to cut.
                Defaults to [0.02, 0.98].
            nodata (int, optional): notadata value. Defaults to 0.

        Returns:
            str: contrasted image output path.
        """
        if not output_path:
            output_path = os.path.join(
                tempfile.gettempdir(),
                next(tempfile._get_candidate_names()) + '.TIF'
            )

        command = GdalContrastStretch._get_contrast_command()
        command = command.format(
            nodata=nodata,
            constrast_range=' '.join(map(str, constrast_range)),
            input_file=input_file,
            output_path=output_path,
        )

        try:
            GdalContrastStretch._run_process(command)
        except subprocess.CalledProcessError as exc:
            logger.error(
                f'Error while executing gdal_constrast_stretch process.'
                f'Input file: {input_file}. Exception: {exc}.'
            )
            raise

        return output_path
