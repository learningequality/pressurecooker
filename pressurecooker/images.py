import math
from PIL import Image, ImageOps

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

    max_dimension = min(max(widths), max(heights))
    offset = max_dimension / int(root)

    new_im = Image.new('RGB', (max_dimension, max_dimension))

    y_offset = 0
    index = 0
    while y_offset < max_dimension and index < len(images):
        x_offset = 0
        while x_offset < max_dimension:
            im = ImageOps.fit(images[index], (int(offset), int(offset)), Image.ANTIALIAS)
            new_im.paste(im, (int(x_offset), int(y_offset)))
            x_offset += offset
            index += 1
        y_offset += offset
    new_im.save(fpath_out)