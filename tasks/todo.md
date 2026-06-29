# Todo: Grade-3 difficulty + full k5 topic coverage

## Core schema plumbing
- [ ] `problem_strategy.py`: `generate -> (dict,str)`; add `make_operands/make_expression/make_visual`
- [ ] `problem_generator.py`: dedup on `problem["text"]`; register new strategies; return `(List[dict],List[str])`
- [ ] `worksheets.py`: drop `[{"text":p}]` wraps (lines 59,171,266,341); pass dicts through
- [ ] `problem_grid.html`: keep operands branch verbatim; add expression + visual branches; shared answer-space

## Harder core arithmetic (age 8)
- [ ] `problem_types.py`: raise age-8 ranges
- [ ] `basic_operations.py`: 3-4 digit regroup/borrow; missing-operand variant
- [ ] `multiplication.py`: tables→12, 2dig×1dig, ×10/×100; div facts→12, remainders, ÷10/÷100; missing-operand

## New text/expression strategies
- [ ] place_value.py
- [ ] rounding.py
- [ ] order_of_operations.py
- [ ] roman_numerals.py
- [ ] measurement.py
- [ ] money.py
- [ ] time.py (conversions/elapsed + visual clock)

## Fractions reshaped (grade 3)
- [ ] fractions.py: compare/equivalent/like-denom add-sub/identify (visual); keep age 9+ decimal

## Visual topics (inline SVG)
- [ ] geometry.py
- [ ] data_graphing.py

## Wire age 8 + age 7
- [ ] problem_types.py: full topic set age 8; lighter set age 7

## Verification
- [ ] pytest -k generator (each strategy: dict w/ text+kind, correct answer)
- [ ] dedup/count age=8 count=40 → 40 unique, topic spread
- [ ] render: 40 fit one page, operands byte-identical, one answer-space/cell
- [ ] regression ages 5-12 operands path
- [ ] app smoke

## Review
Done. Schema = problem dicts (`text`/`kind` + optional `prompt`/`svg`) via
`make_operands/make_expression/make_visual`. Generator dedups on `text`, registers
9 new strategies. Template: operands branch rendered output unchanged; added
`expression` + `visual` branches; shared single `.answer-space` per cell.

Harder grade-3 arithmetic: add/sub 3-4 digit (1,9999) w/ regroup; ×tables→12 +
2dig×1dig + ×10/×100; ÷facts→12 + remainders + ÷10/÷100; missing-operand variants
(add/sub/mult, age≥8). Fractions reshaped for grade 3 (compare/equivalent/like-denom/
identify-visual); ages 9+ decimal path untouched. Age 7 = lighter same set.

New topics: place_value, rounding, order_of_operations, roman_numerals, measurement,
money, time (convert/elapsed/clock-visual), geometry (sides/perimeter/name-visual),
data_graphing (bar chart).

Verification:
- 96/96 non-UI tests pass (incl. new per-strategy answer-correctness + render tests).
- All ages 5-12 generate dicts w/ valid kind; age-8 count=40 → 40 unique, all 3 kinds.
- Layout: 40 cells / 40 answer-boxes (one per cell). Visual cells fit 30/page in
  weasyprint == operands baseline (which the browser fits at 40); expression fits 40.
  => no height regression; visuals no taller than legacy operands.
- App factory + worksheets blueprint import clean. SVGs parse (svg2rlg).
- Browser preview: scratchpad/grade3_preview.html (print-preview to eyeball fit).

Pending (needs user env): app smoke w/ DynamoDB Local + browser print-preview (plan §5).
Out of scope: grading ROI rework (follow-up).
