"""Tests for the problem generator."""

import pytest

from src.problem_generator import ProblemGenerator
from src.problem_generators.order_of_operations import OrderOfOperationsStrategy
from src.problem_generators.roman_numerals import RomanNumeralStrategy, int_to_roman
from src.problem_generators.rounding import RoundingStrategy
from src.problem_generators.measurement import MeasurementStrategy


def test_age_5_problem_ranges():
    """Test that age 5 problems use appropriate ranges based on difficulty."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Test low difficulty (should use numbers 1-10)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.2
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem["text"].split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 10
        ), f"Number {num1} in problem {problem} is outside expected range for low difficulty"
        assert (
            1 <= num2 <= 10
        ), f"Number {num2} in problem {problem} is outside expected range for low difficulty"

    # Test medium difficulty (should use numbers 1-15)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.5
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem["text"].split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 15
        ), f"Number {num1} in problem {problem} is outside expected range for medium difficulty"
        assert (
            1 <= num2 <= 15
        ), f"Number {num2} in problem {problem} is outside expected range for medium difficulty"

    # Test high difficulty (should use numbers 1-20)
    problems, answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.8
    )
    for problem in problems:
        # Extract numbers from the problem
        parts = problem["text"].split()
        num1 = int(parts[0])
        num2 = int(parts[2])

        # Check that numbers are within expected range
        assert (
            1 <= num1 <= 20
        ), f"Number {num1} in problem {problem} is outside expected range for high difficulty"
        assert (
            1 <= num2 <= 20
        ), f"Number {num2} in problem {problem} is outside expected range for high difficulty"


def test_age_5_vs_age_6():
    """Test that age 5 and age 6 problems are appropriately differentiated."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Generate problems for age 5 and age 6 at the same difficulty
    age5_problems, age5_answers = generator.generate_math_problems(
        age=5, count=20, difficulty=0.8
    )
    age6_problems, age6_answers = generator.generate_math_problems(
        age=6, count=20, difficulty=0.8
    )

    # Check that age 5 problems use numbers up to 20
    for problem in age5_problems:
        parts = problem["text"].split()
        num1 = int(parts[0])
        num2 = int(parts[2])
        assert (
            1 <= num1 <= 20
        ), f"Number {num1} in age 5 problem {problem} is outside expected range"
        assert (
            1 <= num2 <= 20
        ), f"Number {num2} in age 5 problem {problem} is outside expected range"

    # Check that age 6 problems can use numbers beyond 20 at high difficulty
    has_larger_numbers = False
    for problem in age6_problems:
        parts = problem["text"].split()
        num1 = int(parts[0])
        num2 = int(parts[2])
        if num1 > 20 or num2 > 20:
            has_larger_numbers = True
            break

    # At high difficulty, age 6 should have at least some problems with numbers > 20
    assert (
        has_larger_numbers
    ), "Age 6 problems at high difficulty should include some numbers > 20"


def test_age_5_problem_distribution():
    """Test that age 5 problems have an appropriate distribution of addition and subtraction."""
    generator = ProblemGenerator(seed=42)  # Use a fixed seed for reproducibility

    # Generate problems at different difficulty levels
    # Use smaller counts since age 5 with low difficulty has limited unique problems
    low_problems, _ = generator.generate_math_problems(age=5, count=30, difficulty=0.2)
    med_problems, _ = generator.generate_math_problems(age=5, count=30, difficulty=0.5)
    high_problems, _ = generator.generate_math_problems(age=5, count=30, difficulty=0.8)

    # Count addition and subtraction problems
    low_add = sum(1 for p in low_problems if "+" in p["text"])
    low_sub = sum(1 for p in low_problems if "-" in p["text"])

    med_add = sum(1 for p in med_problems if "+" in p["text"])
    med_sub = sum(1 for p in med_problems if "-" in p["text"])

    high_add = sum(1 for p in high_problems if "+" in p["text"])
    high_sub = sum(1 for p in high_problems if "-" in p["text"])

    # At low difficulty, should have more addition than subtraction
    # Note: Due to limited unique problems (only 35 total with numbers 1-5),
    # we expect more addition but not necessarily 80% due to constraint
    assert low_add >= low_sub, (
        f"Expected at least as many addition as subtraction at low difficulty, "
        f"got {low_add} addition and {low_sub} subtraction"
    )

    # At medium difficulty, should be more balanced
    assert (
        0.3 <= med_add / len(med_problems) <= 0.7
    ), f"Expected balanced distribution at medium difficulty, got {med_add / len(med_problems):.1%} addition"
    assert (
        0.3 <= med_sub / len(med_problems) <= 0.7
    ), f"Expected balanced distribution at medium difficulty, got {med_sub / len(med_problems):.1%} subtraction"

    # At high difficulty, should be roughly equal
    assert (
        0.3 <= high_add / len(high_problems) <= 0.7
    ), f"Expected balanced distribution at high difficulty, got {high_add / len(high_problems):.1%} addition"
    assert (
        0.3 <= high_sub / len(high_problems) <= 0.7
    ), f"Expected balanced distribution at high difficulty, got {high_sub / len(high_problems):.1%} subtraction"


# --- Grade-3 schema + new topic coverage ---------------------------------


def test_all_problems_are_well_formed_dicts():
    """Every generated problem is a dict with text + a valid kind."""
    generator = ProblemGenerator(seed=11)
    for age in range(5, 13):
        problems, answers = generator.generate_math_problems(
            age=age, count=30, difficulty=0.6
        )
        assert len(problems) == len(answers)
        for p in problems:
            assert isinstance(p, dict)
            assert "text" in p and "kind" in p
            assert p["kind"] in ("operands", "expression", "visual")
            if p["kind"] == "visual":
                assert p["svg"].startswith("<svg")


def test_problems_are_unique_by_text():
    """Dedup is on display text; a full age-8 sheet has no repeats."""
    generator = ProblemGenerator(seed=3)
    problems, _ = generator.generate_math_problems(age=8, count=40, difficulty=0.5)
    assert len(problems) == 40
    texts = [p["text"] for p in problems]
    assert len(set(texts)) == len(texts)


def test_age_8_covers_many_topics():
    """A large grade-3 draw spans well beyond the four arithmetic ops."""
    generator = ProblemGenerator(seed=99)
    problems, _ = generator.generate_math_problems(age=8, count=200, difficulty=0.6)
    kinds = {p["kind"] for p in problems}
    assert kinds == {"operands", "expression", "visual"}
    # At least some visual (geometry/graphing/clock/fraction-identify) appears.
    assert any(p["kind"] == "visual" for p in problems)


def _safe_eval(expr: str) -> int:
    expr = (
        expr.replace("×", "*").replace("÷", "/").replace("−", "-").replace(" ", "")
    )
    return int(eval(expr, {"__builtins__": {}}, {}))


def test_order_of_operations_answers_correct():
    strat = OrderOfOperationsStrategy()
    for diff in (0.2, 0.8):
        for _ in range(200):
            problem, answer = strat.generate(1, 12, diff, 8)
            assert problem["kind"] == "expression"
            assert _safe_eval(problem["text"]) == int(answer)


def test_roman_numeral_answers_correct():
    strat = RomanNumeralStrategy()
    for _ in range(200):
        problem, answer = strat.generate(1, 100, 0.8, 8)
        text = problem["text"]
        if problem.get("prompt") == "Roman numeral":
            # number -> roman
            assert int_to_roman(int(text)) == answer
        else:
            # roman -> number
            assert int_to_roman(int(answer)) == text


def test_rounding_answers_correct():
    strat = RoundingStrategy()
    for _ in range(200):
        problem, answer = strat.generate(1, 999, 0.8, 8)
        base = int(problem["prompt"].split()[-1])
        num = int(problem["text"].replace(",", ""))
        ans = int(answer)
        assert ans % base == 0
        assert abs(ans - num) <= base // 2


def test_measurement_answers_positive_integers():
    strat = MeasurementStrategy()
    for _ in range(100):
        problem, answer = strat.generate(1, 100, 0.6, 8)
        assert problem["kind"] == "expression"
        assert "= ?" in problem["text"]
        assert int(answer) > 0


def test_generated_sheet_renders_one_answer_box_per_cell():
    """Template renders a mixed age-8 sheet with exactly one answer box each."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("src/templates"))
    tpl = env.get_template("problem_grid.html")
    generator = ProblemGenerator(seed=5)
    problems, answers = generator.generate_math_problems(
        age=8, count=40, difficulty=0.6
    )
    html = tpl.render(problems=problems, answers=answers, is_answer_key=True)
    assert html.count('<div class="answer-space">') == 40
    assert html.count('<div class="problem">') == 40


def test_visual_svgs_have_explicit_dimensions():
    """Inline SVGs must carry width+height attrs or browsers drop them in print."""
    import re
    from src.problem_generators.geometry import GeometryStrategy
    from src.problem_generators.data_graphing import DataGraphingStrategy
    from src.problem_generators.time_problems import TimeStrategy
    from src.problem_generators.fractions import FractionStrategy

    svgs = []
    geo, dg = GeometryStrategy(), DataGraphingStrategy()
    for _ in range(30):
        svgs.append(geo.generate(1, 100, 0.6, 8)[0].get("svg", ""))
        svgs.append(dg.generate(1, 10, 0.6, 8)[0].get("svg", ""))
    # clock + fraction-identify only appear sometimes
    tm, fr = TimeStrategy(), FractionStrategy()
    for _ in range(200):
        p = tm.generate(1, 100, 0.6, 8)[0]
        if p.get("svg"):
            svgs.append(p["svg"])
        p = fr.generate(1, 8, 0.6, 8)[0]
        if p.get("svg"):
            svgs.append(p["svg"])

    assert svgs, "expected some visual SVGs"
    for svg in svgs:
        open_tag = svg[: svg.index(">") + 1]
        assert re.search(r'\bwidth="\d', open_tag), f"no width attr: {open_tag}"
        assert re.search(r'\bheight="\d', open_tag), f"no height attr: {open_tag}"
