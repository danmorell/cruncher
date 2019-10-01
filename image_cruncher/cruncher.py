"""
:Project: Image Cruncher
:Contents: cruncher.py
:copyright: © 2019 Daniel Morell
:license: GPL-3.0, see LICENSE for more details.
:Author: DanielCMorell
:Added v0.0.1.dev -- 9/30/2019
"""
# Standard Library Imports
import os

# Package Imports
from PIL import Image
import click

# Local Imports


class CruncherBase:

    def __init__(self, mode, path, output, image_path, version):
        self.mode = mode
        self.path = path
        self.output = output
        self.image_path = image_path
        self.version = version
        self.filename = self.generate_filename(os.path.split(image_path)[1], version)
        self.new_path = self.image_output_path(image_path)
        self.exif = b''

        self.crunch_image()

    def image_output_path(self, image_path):
        """
        Calculate the output path for the image.

        :param image_path: Image input path.
        :return: Image output path.
        """
        if self.mode == 'img':
            image_name = os.path.split(image_path)[1]
            return os.path.join(self.output, image_name)
        relative_path = os.path.relpath(image_path, self.path)
        return os.path.join(self.output, relative_path)

    def crunch_image(self):
        pass

    @staticmethod
    def generate_filename(filename, version):
        return f"{filename}{version['append']}.{version['file_format']}"

    @staticmethod
    def resize(image, size=None, version=None):
        """
        The `resize()` function changes the size of an image without squashing or stretching
        as the PIL.Image.resize() function does. The `size` argument should be a tuple formatted
        as (width, height).

        :param image: PIL image object
        :param size: Tuple with 2 values (width, height)
        :param version: The image version dictionary.
        :return: PIL image object
        """

        if not size:
            return image

        old_aspect = image.width / image.height
        new_aspect = size[0] / size[1]

        if version['orientation'] and (old_aspect < 0 <= new_aspect or old_aspect >= 0 > new_aspect):
            # if one is horizontal and the other vertical flip the orientation
            size = (size[1], size[0])
            new_aspect = size[0] / size[1]

        if size == (image.width, image.height):
            return image

        if new_aspect < old_aspect:
            image.thumbnail([size[1] * old_aspect, size[1]], Image.LANCZOS)
        else:
            image.thumbnail([size[0], size[0] * old_aspect], Image.LANCZOS)

        left = (image.width - size[0]) / 2
        top = (image.height - size[1]) / 2
        right = image.width - left
        bottom = image.height - top

        box = (left, top, right, bottom)

        cropped = image.crop(box)

        return cropped

    def calculate_sampling(self, options, base):
        divisor = (100 - base) / len(options)
        raw_sampling = ((self.version['quality'] - base) / divisor) - 1
        if raw_sampling < 0:
            return 0
        return round(raw_sampling)


class GIFCruncher(CruncherBase):

    def __init__(self, mode, path, output, image_path, version):
        super().__init__(mode, path, output, image_path, version)

    def crunch_image(self):
        image = Image.open(self.path)
        if self.version['metadata'] and image.info.get('exif'):
            self.exif = image.info.get('exif')
        transparency = None
        if image.info.get('transparency'):
            transparency = image.info.get('transparency')
        image = self.resize(image, (self.version['width'], self.version['height']), self.version)
        image.save(
            self.new_path,
            "GIF",
            optimize=True,
            transparency=transparency
        )


class JPEGCruncher(CruncherBase):
    """
    Quality Based Sampling
        0 - 70: 4:2:0
        71 - 89: 4:2:2
        90 - 100: 4:4:4
    """

    def __init__(self, mode, path, output, image_path, version):
        super().__init__(mode, path, output, image_path, version)

    def crunch_image(self):
        image = Image.open(self.path)
        if self.version['metadata'] and image.info.get('exif'):
            self.exif = image.info.get('exif')
        image = self.resize(image, (self.version['width'], self.version['height']), self.version)
        sampling = self.calculate_sampling([0, 1, 2], 40)
        click.echo(sampling)
        image.save(
            self.new_path,
            "JPEG",
            quality=self.version['quality'],
            sampling=sampling,
            optimize=True,
            progressive=True,
            exif=self.exif
        )


class JPEG2000Cruncher(CruncherBase):

    def __init__(self, mode, path, output, image_path, version):
        super().__init__(mode, path, output, image_path, version)

    def crunch_image(self):
        image = Image.open(self.path)
        image = self.resize(image, (self.version['width'], self.version['height']), self.version)
        image.save(
            self.new_path,
            "JPEG",
            quality_mode='dB',
            quality_layers=self.version['quality'],
            progressive=True
        )


class PNGCruncher(CruncherBase):

    def __init__(self, mode, path, output, image_path, version):
        super().__init__(mode, path, output, image_path, version)

    def crunch_image(self):
        image = Image.open(self.path)
        if self.version['metadata'] and image.info.get('exif'):
            self.exif = image.info.get('exif')
        transparency = None
        if image.info.get('transparency'):
            transparency = image.info.get('transparency')
        image = self.resize(image, (self.version['width'], self.version['height']), self.version)
        image.save(
            self.new_path,
            "PNG",
            optimize=True,
            exif=self.exif,
            transparency=transparency
        )


class WebPCruncher(CruncherBase):

    def __init__(self, mode, path, output, image_path, version):
        super().__init__(mode, path, output, image_path, version)

    def crunch_image(self):
        image = Image.open(self.path)
        if self.version['metadata'] and image.info.get('exif'):
            self.exif = image.info.get('exif')
        image = self.resize(image, (self.version['width'], self.version['height']), self.version)
        image.save(
            self.new_path,
            "WebP",
            quality=(100 - self.version['quality']),
            method=0,
            exif=self.exif
        )
