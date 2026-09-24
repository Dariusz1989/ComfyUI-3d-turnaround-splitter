"""
Stage Guard - Geekatplay 3D Multiview

Passes the pipeline's stage on/off switches through unchanged, but refuses a
combination where a stage is ON while a stage it needs is OFF. The check runs in
VALIDATE_INPUTS, so a bad combination is reported when the prompt is queued,
before any model loads, with a message that names both stages and the fix.

Order (each needs the one before it):
    shape -> remesh -> clean_mesh -> textures -> normal_map, ambient_occlusion
"""

try:
    from .branding import CATEGORY
except ImportError:  # pragma: no cover
    from branding import CATEGORY


STAGES = ("shape", "remesh", "clean_mesh", "textures", "normal_map", "ambient_occlusion")

# stage -> the stage it cannot run without
NEEDS = {
    "remesh": "shape",
    "clean_mesh": "remesh",
    "textures": "clean_mesh",
    "normal_map": "textures",
    "ambient_occlusion": "textures",
}

LABELS = {
    "shape": "2 SHAPE",
    "remesh": "3 REMESH",
    "clean_mesh": "4 CLEAN MESH",
    "textures": "TEXTURES",
    "normal_map": "NORMAL MAP",
    "ambient_occlusion": "AMBIENT OCCLUSION",
}


def stage_problems(values):
    """Every broken dependency, as readable sentences (empty list = fine)."""
    problems = []
    for stage, needed in NEEDS.items():
        if values.get(stage) and not values.get(needed):
            problems.append(
                "{} is ON but {} is OFF: {} needs the {} stage. Turn {} on, or {} off.".format(
                    LABELS[stage], LABELS[needed], LABELS[stage], LABELS[needed], LABELS[needed], LABELS[stage]))
    return problems


class GeekatplayStageGuard:
    """Checks the stage switches of the 3D pipeline and passes them through."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {name: ("BOOLEAN", {"default": True}) for name in STAGES}}

    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Stage on/off switches for the 3D pipeline. Queueing fails with a clear message when a stage is on "
        "while a stage it needs is off (shape -> remesh -> clean mesh -> textures -> normal / AO)."
    )
    RETURN_TYPES = ("BOOLEAN",) * len(STAGES)
    RETURN_NAMES = STAGES
    FUNCTION = "check"

    @classmethod
    def VALIDATE_INPUTS(cls, **values):
        problems = stage_problems(values)
        if problems:
            return "Stage order: " + " | ".join(problems)
        return True

    def check(self, **values):
        problems = stage_problems(values)
        if problems:
            raise ValueError("Stage order: " + " | ".join(problems))
        return tuple(bool(values[name]) for name in STAGES)
