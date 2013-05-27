# Copyright (C) 2012 Tim Radvan
#
# This file is part of Kurt.
#
# Kurt is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Kurt is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Kurt. If not, see <http://www.gnu.org/licenses/>.

"""A Kurt plugin for Scratch 2.0."""

import zipfile
import json
import time
import os
import hashlib

import kurt
from kurt.plugin import Kurt, KurtPlugin

IMAGE_EXTENSIONS = ["PNG", "JPG"]


path = "/Users/tim/Dropbox/Code/kurt2/convert2.sb2"


class _ZipBuilder(object):
    def __init__(self, path, kurt_project):
        self.zip_file = zipfile.ZipFile(path, "w")

        project_dict = {
            "penLayerMD5": "279467d0d49e152706ed66539b577c00.png",
            "info": {},
            "tempoBPM": kurt_project.tempo,
            "children": [],

            "info": {
                "flashVersion": "MAC 11,7,700,203",
                "projectID": "10442014",
                "scriptCount": 0,
                "spriteCount": 0,
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.20 Safari/537.36",
                "videoOn": False,
            },
            "videoAlpha": 0.5,
        }

        self.image_dicts = {}
        self.highest_image_id = 0

        stage_dict = self.save_scriptable(kurt_project.stage)
        project_dict.update(stage_dict)

        for kurt_sprite in kurt_project.sprites:
            sprite_dict = self.save_scriptable(kurt_sprite)
            project_dict["children"].append(sprite_dict)

        self.write_file("project.json", json.dumps(project_dict))

        self.zip_file.close()

    def write_file(self, name, contents):
        """Write file contents string into archive."""
        # TODO: find a way to make ZipFile accept a file object.
        zi = zipfile.ZipInfo(name)
        zi.date_time = time.localtime(time.time())[:6]
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0777 << 16L
        self.zip_file.writestr(zi, contents)

    def write_image(self, image):
        if image in self.image_dicts:
            image_dict = self.image_dicts[image]
        else:
            image_id = self.highest_image_id
            self.highest_image_id += 1

            image = image.convert("SVG", "JPEG", "PNG")
            filename = str(image_id) + (image.extension or ".png")
            self.write_file(filename, image.contents)

            image_dict = {
                "baseLayerID": image_id, #-1 for download
                "bitmapResolution": 1,
                #"baseLayerMD5": hashlib.md5(contents).hexdigest(),
            }
            self.image_dicts[image] = image_dict
        return image_dict


    def save_scriptable(self, kurt_scriptable):
        is_stage = isinstance(kurt_scriptable, kurt.Stage)

        scriptable_dict = {
            "objName": kurt_scriptable.name,
            "currentCostumeIndex": kurt_scriptable.costume_index or 0,
            "costumes": [],
            "sounds": [],
        }

        for kurt_costume in kurt_scriptable.costumes:
            costume_dict = self.save_costume(kurt_costume)
            scriptable_dict["costumes"].append(costume_dict)

        if isinstance(kurt_scriptable, kurt.Sprite):
            scriptable_dict.update({
                "scratchX": 0,
                "scratchY": 0,
                "scale": 1,
                "direction": 90,
                "indexInLibrary": 1,
                "isDraggable": False,
                "rotationStyle": "normal",
                "spriteInfo": {},
                "visible": True,
            })

        return scriptable_dict

    def save_costume(self, kurt_costume):
        costume_dict = self.write_image(kurt_costume.image)
        (rx, ry) = kurt_costume.rotation_center
        costume_dict.update({
            "costumeName": kurt_costume.name,
            "rotationCenterX": rx,
            "rotationCenterY": ry,
        })
        return costume_dict


class Scratch20Plugin(KurtPlugin):
    name = "scratch20"
    display_name = "Scratch 2.0"
    extension = ".sb2"

    def load(self, path):
        project_zip = zipfile.ZipFile(path)

        project_dict = json.load(project_zip.open("project.json"))

        kurt_project = kurt.Project()

        kurt_project._original = project_dict

        return kurt_project

    def save(self, path, kurt_project):
        _ZipBuilder(path, kurt_project)




Kurt.register(Scratch20Plugin())
