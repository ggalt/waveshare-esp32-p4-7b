#!/usr/bin/env python3
"""Generate moon phase images at multiple resolutions.

Output is grayscale + alpha (LA mode) PNG.  ESPHome's GRAYSCALE image type
with transparency: alpha_channel renders these correctly on RGB565 displays
without the green-tint artefact that photographic RGB565 images can exhibit.
"""

import os
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SCRIPT_DIR, "PIA00405~large.jpg")
BASE = SCRIPT_DIR
SIZES = [100, 200, 400]

# Moon phases defined by illumination fraction and which side is lit.
# Convention (Northern Hemisphere view):
#   - "right" means the right side is illuminated (waxing)
#   - "left"  means the left side is illuminated (waning)
#   - fraction: 0.0 = new moon, 0.5 = quarter, 1.0 = full
PHASES = {
    "new_moon":         (0.00, "right"),
    "waxing_crescent":  (0.25, "right"),
    "first_quarter":    (0.50, "right"),
    "waxing_gibbous":   (0.75, "right"),
    "full_moon":        (1.00, "right"),
    "waning_gibbous":   (0.75, "left"),
    "last_quarter":     (0.50, "left"),
    "waning_crescent":  (0.25, "left"),
}


def make_phase_mask(size, fraction, lit_side):
    """Create a float mask (0..1) for the illuminated portion of the moon.

    The moon disk is a circle of diameter `size` centred in a size×size image.
    The terminator is modelled as an ellipse whose semi-major axis equals the
    moon radius and whose semi-minor axis varies with the illumination fraction.

    Args:
        size: pixel dimension (width == height)
        fraction: 0.0 (new) to 1.0 (full)
        lit_side: "right" or "left"

    Returns:
        numpy float32 array, shape (size, size), values in [0, 1].
    """
    r = size / 2.0
    # Coordinate grids centred on the disk
    y, x = np.ogrid[:size, :size]
    cx = x - (size - 1) / 2.0
    cy = y - (size - 1) / 2.0

    # Circular disk mask
    dist = np.sqrt(cx ** 2 + cy ** 2)
    disk = (dist <= r).astype(np.float32)

    if fraction >= 1.0:
        return disk  # full moon – entire disk lit
    if fraction <= 0.0:
        return np.zeros((size, size), dtype=np.float32)  # new moon – nothing lit

    # The terminator is the edge between light and dark.  We model it as:
    #   x_term = k * sqrt(r^2 - cy^2)
    # where k ranges from +1 (full) through 0 (quarter) to -1 (new).
    # k = 1 - 2*fraction  maps  fraction 0→+1, 0.5→0, 1→-1.
    # At each row, lit fraction = (1-k)/2 = fraction.
    k = 1.0 - 2.0 * fraction

    # For each row, compute the terminator x position
    # (only meaningful where |cy| < r)
    half_chord = np.sqrt(np.maximum(r ** 2 - cy ** 2, 0))  # shape (size,1)
    x_term = k * half_chord  # terminator x coordinate

    # Illuminated region: for lit_side == "right", pixels with cx >= x_term
    if lit_side == "right":
        lit = (cx >= x_term).astype(np.float32)
    else:
        lit = (cx <= -x_term).astype(np.float32)

    return disk * lit


def generate_all():
    # Convert source to grayscale first, then to RGB so R=G=B=luminance.
    # This avoids the green-tint artefact on RGB565 displays: because all three
    # channels are identical, the unequal 5-6-5 quantisation cannot produce a
    # colour shift.  (The original JPEG had warm tones where R>G>B, and the
    # extra green precision in RGB565 made that look greenish.)
    src_gray = Image.open(SRC).convert("L")

    for size in SIZES:
        moon = src_gray.resize((size, size), Image.LANCZOS)
        moon_arr = np.array(moon, dtype=np.float32)

        for phase_name, (frac, side) in PHASES.items():
            mask = make_phase_mask(size, frac, side)

            # Circular disk mask (for alpha channel – everything outside is transparent)
            r = size / 2.0
            y, x = np.ogrid[:size, :size]
            cx = x - (size - 1) / 2.0
            cy = y - (size - 1) / 2.0
            disk = (np.sqrt(cx ** 2 + cy ** 2) <= r).astype(np.float32)

            # Build RGBA output with R=G=B=luminance
            lum = (mask * moon_arr).astype(np.uint8)
            alpha = (disk * 255).astype(np.uint8)
            out = np.zeros((size, size, 4), dtype=np.uint8)
            out[:, :, 0] = lum
            out[:, :, 1] = lum
            out[:, :, 2] = lum
            out[:, :, 3] = alpha

            outpath = f"{BASE}/{size}/{phase_name}.png"
            Image.fromarray(out, "RGBA").save(outpath)
            print(f"  wrote {outpath}")


if __name__ == "__main__":
    generate_all()
