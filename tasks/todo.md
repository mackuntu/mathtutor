# Todo: Print-answerable grade-3 visual questions

Problem: `data_graphing.py` bar chart has no scale/gridlines/value labels.
"Value of B?" answerable only by measuring bar height — impossible on print.

Research (3.MD + K5/Education.com/SuperTeacher formats): scaled bar/picture
graphs valid grade-3, but every needed number must be printed as a label;
correctness must never depend on drawing size. Labeled-rectangle area (3.MD.7)
also standard and print-safe.

Layout: visual cell ~60px wide, 3.5rem tall (problem_grid.html immutable).
No room for readable y-axis → label value above each bar instead.

## Plan
- [x] `data_graphing.py`: value printed above each bar; kinds:
      total / how-many-more / which-most / which-least (drop trivial "read")
- [x] `geometry.py`: add "area" kind reusing labeled `_rect_svg` (3.MD.7)
- [x] `problem_generator.py`: dedup key text+prompt+svg (visuals all share
      text="" → today max 1 visual per sheet)
- [x] Tests: update uniqueness test key; assert bar values labeled; area answers
- [x] Verify: pytest, render sample sheet, eyeball SVG fit

## Review
- Bar chart now prints each bar's value above the bar (font 9) + letter below;
  all four question kinds answerable purely from labels. Values forced distinct
  so most/least/how-many-more unambiguous. SVG 60x52 fits 3.5rem cell cap.
- Geometry gained "Area" on the existing labeled rectangle (3.MD.7).
- Dedup key now (text, prompt, svg): sample age-8 35-problem sheet went from
  1 visual to 7 (fractions/clock/shape/bar chart mix).
- Verified: tests/test_generator.py 18 passed (incl. new
  test_bar_chart_answers_read_from_labels, test_geometry_area_answers_correct);
  test_document_renderer.py 3 passed. Headless-Chrome screenshots of rendered
  grid + 5 chart samples: labels legible, answers match labels.
- test_worksheet/test_auth botocore errors = DynamoDB Local not running
  (pre-existing env, unrelated).

# Todo: 35-problem worksheet overflows one printed page

Problem: default count 35 → 7 grid rows. Row height = tallest cell
(visual + 2-line prompt ≈ 127px; plain operands ≈ 104px). Measured body
1130px vs 970px printable (letter − 0.45in margins). Two causes:
1. problem_grid.html spacing is fixed (comment claims count-adaptive, isn't);
   sized for ≤6 rows — even 7 all-plain rows = 1059px.
2. `_arrange_for_layout` spread visuals one per row → every row tall.

Constraint: problem_grid.html layout immutable → override CSS vars from
worksheet.html (higher specificity / element-scoped custom props).

## Plan
- [x] TDD: failing tests — clustering unit test + end-to-end tall-rows-minimal
- [x] `_arrange_for_layout`: pack tall problems (visual or prompt) into
      earliest rows, keep right-column-short + pair invariants
- [x] worksheet.html: >30 problems → gap 1rem, answer box 1.25rem, SVG 3rem;
      >35 → gap 0.6rem, font 14pt, SVG 2.5rem
- [x] Verify: headless-Chrome print-to-PDF page counts across seeds/ages/counts

## Review
- `_is_tall` + 4-bucket fill (tall-long / tall-short / plain-long /
  plain-short); last column still prefers shorts, talls consumed first so
  tall rows = ceil(talls/5).
- Verified 1 page: count 35 ages 5-10 (30+ sheets, worksheet + answer key),
  count 40 ages 5-10 incl. 19-tall sheets. Before fix: 2 pages.
- pytest: 105 passed (2 new tests). problem_grid.html untouched.

# Todo: dependency update (82 Dependabot alerts)

## Plan
- [x] Pull open alerts via `gh api .../dependabot/alerts`, map to min patched
      versions across requirements.txt + tests/ui/requirements.txt
- [x] Bump: Flask 3.1.3, Werkzeug 3.1.8, Pillow 12.3.0, requests 2.34.2,
      python-dotenv 1.2.2, markdown 3.10.2, pytest 9.1.1, pytest-cov 7.1.0,
      black 26.5.1, gunicorn 26.0.0, types-requests; UI: pypdf 6.14.2,
      pillow 12.3.0
- [x] Fix fallout, verify: unit suite, app boot, gunicorn config check

## Review
- pytest 9 broke pytest-selenium 4.0.2 (removed `startdir` hook arg) →
  4.1.0.
- Resolver dragged numpy to 2.2.1; cv2 4.9 / torch wheels are numpy-1.x
  builds (`_ARRAY_API not found`) → pinned `numpy<2` +
  `tifffile==2024.8.30` (scikit-image chain needs numpy>=2 from 2025+
  lines).
- Known benign: pyppeteer 2.0.0 (unused, via pytest-failed-screenshot)
  wants urllib3<2.
- Verified: 105 unit tests pass; `create_app()` + GET / → 302; gunicorn 26
  `--check-config wsgi:app` exit 0; pypdf usage is modern PdfReader only.
- Every alerted package now at/above its patched version.
