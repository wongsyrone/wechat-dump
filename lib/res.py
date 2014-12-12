#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: res.py
# Date: Fri Dec 12 23:12:06 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import glob
import os
import Image
import cStringIO
import base64
import logging
logger = logging.getLogger(__name__)

from lib.avatar import AvatarReader

VOICE_DIRNAME = 'voice2'
JPEG_QUALITY = 50

class Resource(object):
    """ multimedia resources in chat"""
    def __init__(self, res_dir):
        assert os.path.isdir(res_dir), "No such directory: {}".format(res_dir)
        self.res_dir = res_dir
        self.img_dir = os.path.join(res_dir, 'image2')
        assert os.path.isdir(self.img_dir), \
                     "No such directory: {}".format(self.img_dir)
        self.avt_reader = AvatarReader(self.res_dir)
        self.init()

    def init(self):
        """ load some index in memory"""
        self.speak_data = {}
        for root, subdirs, files in os.walk(
            os.path.join(self.res_dir, VOICE_DIRNAME)):
            if subdirs:
                continue
            for f in files:
                if not f.endswith('amr'):
                    continue
                full_path = os.path.join(root, f)
                key = f[4:-4]  # msg_xxxxx.amr
                assert len(key) == 26, \
                    "Error interpreting the protocol, this is a bug!"
                self.speak_data[key] = full_path

    @staticmethod
    def get_file_b64(fname):
        data = open(fname, 'rb').read()
        return base64.b64encode(data)

    def get_avatar(self, username):
        """ return base64 string"""
        ret = self.avt_reader.get_avatar(username)
        if ret is None:
            return ""
        im = Image.fromarray(ret)
        buf = cStringIO.StringIO()
        im.save(buf, 'JPEG', quality=JPEG_QUALITY)
        jpeg_str = buf.getvalue()
        return base64.b64encode(jpeg_str)

    def get_img_file(self, fnames):
        """ fnames: a list of filename to search for
            return (filename, filename) of (big, small) image.
            could be empty string.
        """
        cands = []
        for fname in fnames:
            dir1, dir2 = fname[:2], fname[2:4]
            dirname = os.path.join(self.img_dir, dir1, dir2)
            if not os.path.isdir(dirname):
                logger.warn("Directory not found: {}".format(dirname))
                continue
            for f in os.listdir(dirname):
                if fname in f:
                    full_name = os.path.join(dirname, f)
                    size = os.path.getsize(full_name)
                    if size > 0:
                        cands.append((full_name, size))
        if not cands:
            return ("", "")
        cands = sorted(cands, key=lambda x: x[1])

        def name_is_thumbnail(name):
            return os.path.basename(name).startswith('th_') \
                    and not name.endswith('hd')
        if len(cands) == 1:
            name = cands[0][0]
            if name_is_thumbnail(name):
                # thumbnail
                return ("", name)
            else:
                logger.warn("Found big image but not thumbnail: {}".format(fname))
                return (name, "")
        big, small = cands[-1], cands[0]
        if not name_is_thumbnail(small[0]):
            return (big[0], "")
        return (big[0], small[0])

    def get_img(self, fnames):
        """ return two base64 jpg string"""
        big_file, small_file = self.get_img_file(fnames)

        def get_jpg_b64(img_file):
            if not big_file:
                return None
            if not img_file.endswith('jpg'):
                # possibly not jpg
                im = Image.open(open(img_file, 'rb'))
                buf = cStringIO.StringIO()
                im.save(buf, 'JPEG', quality=JPEG_QUALITY)
                return base64.b64encode(buf.getvalue())
            return Resource.get_file_b64(img_file)
        big_file = get_jpg_b64(big_file)
        small_file = get_jpg_b64(small_file)

        if big_file and not small_file:
            # TODO resize big to a thumbnail
            pass
        return (big_file, small_file)
