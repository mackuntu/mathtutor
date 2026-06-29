"""Strategy for time problems (grade 3): conversions, elapsed, clock reading."""

import math
import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_expression, make_visual

# (from_unit, to_unit, factor)
# Abbreviated units keep the inline expression inside one grid column.
_CONVERSIONS = [
    ("h", "min", 60),
    ("min", "s", 60),
    ("day", "h", 24),
    ("wk", "days", 7),
    ("yr", "mo", 12),
]


def _clock_svg(hour: int, minute: int) -> str:
    """Analog clock face with hour/minute hands at the given time."""
    cx = cy = 30
    r = 27
    # Angles measured clockwise from 12 o'clock.
    min_ang = math.radians(minute * 6)
    hour_ang = math.radians((hour % 12) * 30 + minute * 0.5)
    mx = cx + 20 * math.sin(min_ang)
    my = cy - 20 * math.cos(min_ang)
    hx = cx + 13 * math.sin(hour_ang)
    hy = cy - 13 * math.cos(hour_ang)
    ticks = []
    for i in range(12):
        a = math.radians(i * 30)
        x1 = cx + (r - 3) * math.sin(a)
        y1 = cy - (r - 3) * math.cos(a)
        x2 = cx + r * math.sin(a)
        y2 = cy - r * math.cos(a)
        ticks.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="black" stroke-width="1"/>'
        )
    return (
        '<svg width="60" height="60" viewBox="0 0 60 60" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" stroke="black" '
        'stroke-width="1.5"/>'
        f'{"".join(ticks)}'
        f'<line x1="{cx}" y1="{cy}" x2="{hx:.1f}" y2="{hy:.1f}" stroke="black" '
        'stroke-width="2.5"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{mx:.1f}" y2="{my:.1f}" stroke="black" '
        'stroke-width="1.5"/>'
        f'<circle cx="{cx}" cy="{cy}" r="1.5" fill="black"/>'
        "</svg>"
    )


class TimeStrategy(ProblemStrategy):
    """Time conversions, elapsed time, and reading an analog clock."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        kind = random.choice(["convert", "elapsed", "clock"])

        if kind == "convert":
            from_unit, to_unit, factor = random.choice(_CONVERSIONS)
            count = random.randint(2, 9)
            text = f"{count} {from_unit} = ? {to_unit}"
            return make_expression(text), str(count * factor)

        if kind == "elapsed":
            hour = random.randint(1, 11)
            start_min = random.choice([0, 15, 30, 45])
            add = random.choice([15, 30, 45, 60])
            total = hour * 60 + start_min + add
            end_hour = (total // 60 - 1) % 12 + 1
            end_min = total % 60
            text = f"{hour}:{start_min:02d} + {add} min"
            return make_expression(text), f"{end_hour}:{end_min:02d}"

        # clock reading
        hour = random.randint(1, 12)
        minute = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
        return (
            make_visual(_clock_svg(hour, minute), prompt="Read the time"),
            f"{hour}:{minute:02d}",
        )
