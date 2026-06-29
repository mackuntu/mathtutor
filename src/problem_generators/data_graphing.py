"""Strategy for data/graphing problems (grade 3): read a tiny bar chart."""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_visual

_LABELS = ["A", "B", "C"]
_COLORS = ["#4a7fb5", "#7bb573", "#d49a4a"]


def _bar_chart_svg(values) -> str:
    max_v = max(values)
    bar_w = 12
    gap = 6
    base_y = 38
    scale = 28 / max_v
    bars = []
    for i, v in enumerate(values):
        x = 6 + i * (bar_w + gap)
        h = v * scale
        y = base_y - h
        bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" '
            f'fill="{_COLORS[i]}"/>'
            f'<text x="{x + bar_w / 2:.1f}" y="46" font-size="8" '
            f'text-anchor="middle">{_LABELS[i]}</text>'
        )
    return (
        '<svg width="60" height="50" viewBox="0 0 60 50" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<line x1="4" y1="38" x2="58" y2="38" stroke="black" stroke-width="1"/>'
        f'{"".join(bars)}'
        "</svg>"
    )


class DataGraphingStrategy(ProblemStrategy):
    """Read values off a small 3-bar chart."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        values = [random.randint(1, 10) for _ in range(3)]
        # Avoid an all-equal chart for the "how many more" questions.
        while len(set(values)) == 1:
            values = [random.randint(1, 10) for _ in range(3)]

        kind = random.choice(["more", "total", "read"])

        if kind == "total":
            return (
                make_visual(_bar_chart_svg(values), prompt="Total of all bars?"),
                str(sum(values)),
            )

        if kind == "read":
            i = random.randrange(3)
            return (
                make_visual(_bar_chart_svg(values), prompt=f"Value of {_LABELS[i]}?"),
                str(values[i]),
            )

        # how many more (max vs min)
        hi = max(range(3), key=lambda j: values[j])
        lo = min(range(3), key=lambda j: values[j])
        prompt = f"How many more {_LABELS[hi]} than {_LABELS[lo]}?"
        return make_visual(_bar_chart_svg(values), prompt=prompt), str(
            values[hi] - values[lo]
        )
