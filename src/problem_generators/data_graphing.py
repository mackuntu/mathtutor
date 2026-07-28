"""Strategy for data/graphing problems (grade 3): read a tiny bar chart.

Each bar carries its value as a printed label (3.MD.3 style): the answer is
always read off the labels, never off the physical bar height, so the chart
stays answerable when printed at any scale.
"""

import random
from typing import Dict, Tuple

from src.problem_strategy import ProblemStrategy, make_visual

_LABELS = ["A", "B", "C"]
_COLORS = ["#4a7fb5", "#7bb573", "#d49a4a"]


def _bar_chart_svg(values) -> str:
    max_v = max(values)
    bar_w = 12
    gap = 6
    base_y = 40
    top = 10  # room for the value label above the tallest bar
    scale = (base_y - top) / max_v
    bars = []
    for i, v in enumerate(values):
        x = 6 + i * (bar_w + gap)
        h = v * scale
        y = base_y - h
        bars.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" '
            f'fill="{_COLORS[i]}"/>'
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 2:.1f}" font-size="9" '
            f'text-anchor="middle">{v}</text>'
            f'<text x="{x + bar_w / 2:.1f}" y="48" font-size="9" '
            f'text-anchor="middle">{_LABELS[i]}</text>'
        )
    return (
        '<svg width="60" height="52" viewBox="0 0 60 52" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<line x1="4" y1="40" x2="58" y2="40" stroke="black" stroke-width="1"/>'
        f'{"".join(bars)}'
        "</svg>"
    )


class DataGraphingStrategy(ProblemStrategy):
    """One/two-step questions over a small value-labeled 3-bar chart."""

    def generate(
        self, min_val: int, max_val: int, difficulty: float, age: int
    ) -> Tuple[Dict[str, str], str]:
        values = [random.randint(1, 10) for _ in range(3)]
        # Distinct max/min keep "more"/"most"/"least" unambiguous.
        while len(set(values)) < 3:
            values = [random.randint(1, 10) for _ in range(3)]

        kind = random.choice(["more", "total", "most", "least"])
        svg = _bar_chart_svg(values)

        if kind == "total":
            return make_visual(svg, prompt="Total of all bars?"), str(sum(values))

        if kind == "most":
            hi = max(range(3), key=lambda j: values[j])
            return make_visual(svg, prompt="Which bar is most?"), _LABELS[hi]

        if kind == "least":
            lo = min(range(3), key=lambda j: values[j])
            return make_visual(svg, prompt="Which bar is least?"), _LABELS[lo]

        # how many more (max vs min)
        hi = max(range(3), key=lambda j: values[j])
        lo = min(range(3), key=lambda j: values[j])
        prompt = f"How many more {_LABELS[hi]} than {_LABELS[lo]}?"
        return make_visual(svg, prompt=prompt), str(values[hi] - values[lo])
