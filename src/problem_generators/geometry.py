"""Strategy for geometry problems (grade 3): sides, perimeter, naming."""

import math
import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_visual

_SHAPES = {3: "triangle", 4: "square", 5: "pentagon", 6: "hexagon"}


def _polygon_points(n: int, cx: float, cy: float, r: float) -> str:
    pts = []
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        pts.append(f"{cx + r * math.cos(ang):.1f},{cy + r * math.sin(ang):.1f}")
    return " ".join(pts)


def _shape_svg(sides: int) -> str:
    if sides == 4:
        # Axis-aligned square (clearer than a rotated diamond).
        body = '<rect x="14" y="8" width="32" height="32" fill="#dce8f5" stroke="black" stroke-width="1.5"/>'
    else:
        pts = _polygon_points(sides, 30, 26, 20)
        body = (
            f'<polygon points="{pts}" fill="#dce8f5" stroke="black" stroke-width="1.5"/>'
        )
    return f'<svg viewBox="0 0 60 52" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def _rect_svg(width: int, length: int) -> str:
    return (
        '<svg viewBox="0 0 64 48" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="10" y="12" width="40" height="24" fill="#dce8f5" '
        'stroke="black" stroke-width="1.5"/>'
        f'<text x="30" y="46" font-size="9" text-anchor="middle">{length}</text>'
        f'<text x="6" y="26" font-size="9" text-anchor="end">{width}</text>'
        "</svg>"
    )


class GeometryStrategy(ProblemStrategy):
    """Count sides, compute rectangle perimeter, or name a shape."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        kind = random.choice(["sides", "perimeter", "name"])

        if kind == "perimeter":
            width = random.randint(2, 12)
            length = random.randint(2, 12)
            answer = 2 * (width + length)
            return make_visual(_rect_svg(width, length), prompt="Perimeter"), str(answer)

        sides = random.choice(list(_SHAPES.keys()))
        if kind == "sides":
            return make_visual(_shape_svg(sides), prompt="How many sides?"), str(sides)

        # name the shape
        return make_visual(_shape_svg(sides), prompt="Name the shape"), _SHAPES[sides]
