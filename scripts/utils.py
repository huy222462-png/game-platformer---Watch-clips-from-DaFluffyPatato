import os

import pygame

BASE_IMG_PATH = 'data/images/'

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]


def bottom_nontransparent_row(surf):
    """Return the y index (0-based) of the lowest non-transparent pixel row in surf.

    Uses the surface colorkey when present; otherwise falls back to alpha channel
    or non-black pixels. Returns -1 if the surface is fully transparent/empty.
    """
    try:
        w, h = surf.get_width(), surf.get_height()
    except Exception:
        return -1

    colorkey = None
    try:
        colorkey = surf.get_colorkey()
    except Exception:
        colorkey = None

    for y in range(h - 1, -1, -1):
        for x in range(w):
            try:
                c = surf.get_at((x, y))
            except Exception:
                continue
            # c may be (r,g,b) or (r,g,b,a)
            if colorkey is not None:
                if c[:3] != colorkey:
                    return y
            else:
                if len(c) == 4:
                    if c[3] != 0:
                        return y
                else:
                    # no alpha channel - treat pure black as transparent (consistent with set_colorkey usage)
                    if c[:3] != (0, 0, 0):
                        return y
    return -1


def baseline_from_bottom(surf):
    """Return number of transparent pixels at bottom of the surface.

    This is (height - 1 - bottom_nontransparent_row). If the surface is fully
    empty returns 0.
    """
    br = bottom_nontransparent_row(surf)
    if br == -1:
        return 0
    try:
        return surf.get_height() - 1 - br
    except Exception:
        return 0