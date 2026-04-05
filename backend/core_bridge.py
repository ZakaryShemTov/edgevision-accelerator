"""
Core bridge — resolves the project's Python core packages into sys.path.

All backend modules import core_bridge first.  This is the single place
where the backend knows about the project layout; nothing else needs to
hard-code path logic.
"""
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_BACKEND_DIR, "..")

_CORE_PATHS = [
    os.path.join(_PROJECT_ROOT, "python", "common"),
    os.path.join(_PROJECT_ROOT, "python", "golden"),
    os.path.join(_PROJECT_ROOT, "python", "preview"),
    os.path.join(_PROJECT_ROOT, "python", "codegen"),
    os.path.join(_PROJECT_ROOT, "python", "verify"),
]

for _p in _CORE_PATHS:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Verify the core is importable at startup — fail fast if the tree is broken.
from kernels import KERNELS, KERNEL_NAMES          # noqa: F401, E402
from conv_reference import conv2d_int8             # noqa: F401, E402
from conversions import uint8_to_int8              # noqa: F401, E402
