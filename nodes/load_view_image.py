"""
Load View Image - Geekatplay 3D Multiview

Loads one image from ComfyUI's input folder OR from anywhere under the output
folder, subfolders included, so a view saved by another workflow (for example
output/turntable/charsheet_v2/left/left_00005_.png) can be picked straight from
the dropdown. The core "Load Image (from Outputs)" only lists the top level of
output/.

Like the core Load Image it also returns the painted mask: open the node in the
Mask Editor, paint over the area to change, and the MASK output is 1 there.
"""

import hashlib
import os

import numpy as np
import torch
from PIL import Image, ImageOps

import folder_paths

try:
    import node_helpers
except ImportError:  # pragma: no cover - stand-alone import for tests
    node_helpers = None

try:
    from .branding import CATEGORY
    from .turnaround_splitter import _output_sheet_choices
except ImportError:  # pragma: no cover
    from branding import CATEGORY
    from turnaround_splitter import _output_sheet_choices


def _pillow(function, *args, **kwargs):
    if node_helpers is not None:
        return node_helpers.pillow(function, *args, **kwargs)
    return function(*args, **kwargs)


def load_image_and_mask(path):
    """(1, H, W, 3) image in 0..1 and (1, H, W) mask, 1 where the alpha was cleared (painted)."""
    image = _pillow(Image.open, path)
    image = _pillow(ImageOps.exif_transpose, image)
    rgb = np.array(image.convert("RGB")).astype(np.float32) / 255.0
    if "A" in image.getbands():
        alpha = np.array(image.getchannel("A")).astype(np.float32) / 255.0
        mask = 1.0 - alpha
    else:
        mask = np.zeros(rgb.shape[:2], dtype=np.float32)
    return torch.from_numpy(rgb)[None,], torch.from_numpy(mask)[None,]


class GeekatplayLoadViewImage:
    """Loads one image from input/ or from any output/ subfolder, with its mask."""

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [
            name for name in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, name))
        ]
        if hasattr(folder_paths, "filter_files_content_types"):
            files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (_output_sheet_choices() + sorted(files), {"image_upload": True}),
            }
        }

    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Loads an image from the input folder or from any output subfolder (newest outputs first, "
        "marked [output]). Paint in the Mask Editor to get a MASK of the area to change."
    )
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load"

    def load(self, image):
        return load_image_and_mask(folder_paths.get_annotated_filepath(image))

    @classmethod
    def IS_CHANGED(cls, image):
        digest = hashlib.sha256()
        with open(folder_paths.get_annotated_filepath(image), "rb") as handle:
            digest.update(handle.read())
        return digest.hexdigest()

    @classmethod
    def VALIDATE_INPUTS(cls, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True
