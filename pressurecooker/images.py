import math
import tempfile
import numpy as np
import os
import wave
import subprocess
import sys

# On OS X, the default backend will fail if you are not using a Framework build of Python,
# e.g. in a virtualenv. To avoid having to set MPLBACKEND each time we use Pressure Cooker,
# automatically set the backend.
if sys.platform.startswith("darwin"):
    import matplotlib
    if matplotlib.get_backend().lower() == "macosx":
        matplotlib.use('PS')

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageOps
from wand.image import Image as pdfImage # Must also have imagemagick and ghostscript installed

def create_tiled_image(source_images, fpath_out):
    """
    Create a tiled image from list of image paths provided in source_images and
    write result to fpath_out.
    """
    root = math.sqrt(len(source_images))
    assert len(source_images) > 0, "Must provide at least one image to tile"
    assert int(root + 0.5) ** 2 == len(source_images), "Number of images must be a perfect square"

    images = list(map(Image.open, source_images))
    widths, heights = zip(*(i.size for i in images))

    max_dimension = int(min(max(widths), max(heights)))
    offset = int(max_dimension / int(root))

    new_im = Image.new('RGB', (max_dimension, max_dimension))

    index = x_index = y_index = 0
    root = int(root)
    while y_index < root and index < len(images):
        x_index = 0
        while x_index < root and index < len(images):
            im = ImageOps.fit(images[index], (int(offset), int(offset)), Image.ANTIALIAS)
            new_im.paste(im, (int(offset * x_index), int(offset * y_index)))
            x_index += 1
            index += 1
        y_index += 1
    new_im.save(fpath_out)

def create_image_from_pdf_page(fpath_in, fpath_out, page_number=0, position='north'):
    """
    Create an image from the pdf at fpath_in and write result to fpath_out.
    position options: 'forget', 'north_west', 'north', 'north_east', 'west', 'center', 'east', 'south_west', 'south', 'south_east', 'static'
    """
    assert fpath_in.endswith('pdf'), "File must be in pdf format"
    with pdfImage(filename="{}[{}]".format(fpath_in, page_number)) as img:
        size = min(img.width, img.height)
        img.crop(width=size, height=size, gravity=position)
        img.save(filename=fpath_out)


def create_waveform_image(fpath_in, fpath_out, max_num_of_points=None, colormap_options=None):
    """
    Create a waveform image from audio or video file at fpath_in and write to fpath_out
    Colormaps can be found at http://matplotlib.org/examples/color/colormaps_reference.html
    """

    colormap_options = colormap_options or {}
    cmap_name = colormap_options.get('name') or 'cool'
    vmin = colormap_options.get('vmin') or 0
    vmax = colormap_options.get('vmax') or 1
    color = colormap_options.get('color') or 'w'

    tempwav_fh, tempwav_name = tempfile.mkstemp(suffix=".wav")
    os.close(tempwav_fh)  # close the file handle so ffmpeg can write to the file
    try:
        ffmpeg_cmd = ['ffmpeg', '-y', '-loglevel', 'panic', '-i', fpath_in]
        # The below settings apply to the WebM encoder, which doesn't seem to be built by Homebrew on Mac,
        # so we apply them conditionally.
        if not sys.platform.startswith('darwin'):
            ffmpeg_cmd.extend(['-cpu-used', '-16'])
        ffmpeg_cmd += [tempwav_name]
        subprocess.call(ffmpeg_cmd)

        spf = wave.open(tempwav_name, 'r')

        #Extract Raw Audio from Wav File
        signal = spf.readframes(-1)
        signal = np.fromstring(signal, 'Int16')

        # Get subarray from middle
        length = len(signal)
        count = max_num_of_points or length
        subsignals = signal[int((length-count)/2):int((length+count)/2)]

        # Set up max and min values for axes
        X = [[.6, .6], [.7, .7]]
        xmin, xmax = xlim = 0, count
        max_y_axis = max(-min(subsignals), max(subsignals))
        ymin, ymax = ylim = -max_y_axis, max_y_axis

        # Set up canvas according to user settings
        figure = Figure()
        canvas = FigureCanvasAgg(figure)
        ax = figure.add_subplot(111, xlim=xlim, ylim=ylim, autoscale_on=False, frameon=False)
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.set_xticks([])
        ax.set_yticks([])
        cmap = plt.get_cmap(cmap_name)
        cmap = LinearSegmentedColormap.from_list(
            'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=vmin, b=vmax),
            cmap(np.linspace(vmin, vmax, 100))
        )
        ax.imshow(X, interpolation='bicubic', cmap=cmap, extent=(xmin, xmax, ymin, ymax), alpha=1)

        # Plot points
        ax.plot(np.arange(count), subsignals, color)
        ax.set_aspect('auto')

        canvas.print_figure(fpath_out)
    finally:
        os.remove(tempwav_name)
