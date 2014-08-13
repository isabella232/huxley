# Copyright (c) 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import os

from PIL import Image
from PIL import ImageChops

from huxley.errors import TestError

def rmsdiff_2011(im1, im2):
    "Calculate the root-mean-square difference between two images"
    diff = ImageChops.difference(im1, im2)
    h = diff.histogram()
    sq = (value * (idx ** 2) for idx, value in enumerate(h))
    sum_of_squares = sum(sq)
    rms = math.sqrt(sum_of_squares / float(im1.size[0] * im1.size[1]))
    return rms


def images_identical(path1, path2, mask_path):
    if not os.path.exists(path1):
        return False
    im1 = Image.open(path1)
    im2 = Image.open(path2)
    if im1.size != im2.size:
        return False
    if mask_path != None:
        mask = Image.open(mask_path)
        im1 = Image.alpha_composite(im1, mask)
        im2 = Image.alpha_composite(im2, mask)
    return ImageChops.difference(im1, im2).getbbox() is None


def image_diff(path1, path2, outpath, diffcolor, mask_path):
    if not os.path.exists(path1):
        im2 = Image.open(path2)
        return (1000, im2.size[0], im2.size[1])

    im1 = Image.open(path1)
    im2 = Image.open(path2)

    if im1.size != im2.size:
        return (1000, im2.size[0], im2.size[1])

    if mask_path != None:
        mask = Image.open(mask_path)
        im1 = Image.alpha_composite(im1, mask)
        im2 = Image.alpha_composite(im2, mask)

    rmsdiff = rmsdiff_2011(im1, im2)

    pix1 = im1.load()
    pix2 = im2.load()

    if im1.mode != im2.mode:
        raise TestError('Different pixel modes between %r and %r' % (path1, path2))
    if im1.size != im2.size:
        raise TestError('Different dimensions between %r (%r) and %r (%r)' % (path1, im1.size, path2, im2.size))

    mode = im1.mode

    if mode == '1':
        value = 255
    elif mode == 'L':
        value = 255
    elif mode == 'RGB':
        value = diffcolor
    elif mode == 'RGBA':
        value = diffcolor + (255,)
    elif mode == 'P':
        raise NotImplementedError('TODO: look up nearest palette color')
    else:
        raise NotImplementedError('Unexpected PNG mode')

    width, height = im1.size

    for y in xrange(height):
        for x in xrange(width):
            if pix1[x, y] != pix2[x, y]:
                pix2[x, y] = value
    im2.save(outpath)

    return (rmsdiff, width, height)
