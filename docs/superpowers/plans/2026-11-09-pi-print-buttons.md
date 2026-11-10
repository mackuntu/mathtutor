# Pi Print Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each kid presses their own button on the Pi and a fresh worksheet at their level prints on the home printer.

**Architecture:** The Flask site gains two device-token `/api` endpoints: list children, and create-a-worksheet-and-return-its-printable-HTML (shared generation/render helper, no duplication). A small stdlib-only Python program on the Pi (`pi/mathtutor_pi/`) watches two GPIO buttons, calls the site, renders the HTML to PDF with headless Chromium (one render at a time), prints through CUPS, and drives each button's LED (steady / blink / fast flash).

**Tech Stack:** Flask, psycopg3, pytest (site); Python 3.13 stdlib (`urllib`, `tomllib`, `subprocess`, `threading`), `gpiozero` (apt), `chromium-headless-shell` (apt), CUPS `lp`/`lpstat`/`cancel` (Pi).

**Spec:** `docs/superpowers/specs/2026-11-09-pi-print-buttons-design.md`

## Global Constraints

- Never modify the layout of `src/templates/problem_grid.html`.
- Child ages come from the existing model (`Child.age`, end-of-school-year); the Pi never computes ages.
- Worksheet generation = today's `/worksheets/generate`: `age=child.age`, `count=30`, `difficulty=generator.get_school_year_progress()`, saved with correct answers.
- Button sheets print the serial (`serial_number=worksheet.serial_number`, e.g. `WS-1a2b3c4d`); never answer-key mode, never answers in any response.
- Device tokens: never committed, never logged, never in URLs. Token file mode `0600`.
- Unknown or other-owner child id → 404 JSON `{"error": "not found"}`.
- State-changing `/api` endpoints are `POST` (see `require_api_auth` docstring).
- Site tests: real Postgres, `pytest tests/ -W error`, TDD. Pi tests: `pytest pi/tests -W error`, no GPIO/Chromium/CUPS needed (fakes).
- Pi code: stdlib + `gpiozero` only; `gpiozero` imported only in `pi/mathtutor_pi/main.py`. No `RPi.GPIO`.
- Pi: one Chromium render at a time (global lock); a press still starts blinking immediately.
- Extra presses while that kid's job runs are ignored. The two buttons are independent.
- "Done" = CUPS job completed. Not completed within `print_timeout_s` (default 120) → cancel job, failure.
- Failure → fast flash for `error_flash_s` (default 5) then steady. Every press and failure reason logged (stdout → journald).
- Pi host `homepi.local`, user `martin`; Plex and Samba also run there — don't touch their config.

## Review Focus

1. Printer asleep/off/unreachable: job never completes → cancelled at timeout, light flashes, button usable again (Task 4 `test_wait_done_timeout_cancels_job`, Task 5 `test_print_failure_flashes_then_ready`).
2. Token revoked or wrong → 401 → failure flash; log says "unauthorized", never the token (Task 3 `test_unauthorized_raises_without_token_in_message`).
3. Switch bounce / mashing / held button → one sheet (Task 5 `test_presses_while_busy_are_ignored`; Task 6 `bounce_time`).
4. Vercel cold start or slow network → client timeout, failure flash, not a hang (Task 3 `test_timeout_raises_site_error`).
5. Chromium missing, crashing, or hanging → `RenderError`, temp files removed, lock released so the other kid can still print (Task 4 `test_render_timeout_raises_and_cleans_up`, Task 5 `test_render_lock_released_after_failure`).

---

### Task 1: Shared worksheet generation and printable render

**Files:**
- Create: `src/worksheet_service.py`
- Modify: `src/routes/worksheets.py` (`generate_worksheet_route`, ~lines 190-225)
- Test: `tests/test_worksheet_service.py`

**Interfaces:**
- Produces:
  - `generate_for_child(child: Child) -> Worksheet` — generates with the Global Constraints values, persists via `PostgresRepository().create_worksheet`, returns the saved worksheet (with `correct_answers`).
  - `render_printable(worksheet: Worksheet, child: Child) -> str` — `render_template("worksheet.html", ...)` with problems normalized exactly as `view_worksheet` does, `serial_number=worksheet.serial_number`, `answers=None`, `is_answer_key=False`, `worksheet_id=worksheet.id`, plus whatever else the template needs (pass `user=None` if the template tolerates it; check).
- `generate_worksheet_route` calls `generate_for_child`; its rendered output stays as today (no serial) — do not change that page.

- [ ] **Step 1: Write failing tests** (use `app`, `repository`, `test_child` fixtures; run inside `app.test_request_context()`)

```python
def test_generate_for_child_persists_30_problems_with_answers(repository, test_child):
    ws = generate_for_child(test_child)
    saved = repository.get_worksheet(ws.id)
    assert saved is not None and saved.child_id == test_child.id
    assert len(json.loads(saved.problems) if isinstance(saved.problems, str) else saved.problems) == 30
    assert saved.correct_answers

def test_render_printable_has_serial_and_no_answer_key(app, repository, test_child):
    ws = generate_for_child(test_child)
    html = render_printable(ws, test_child)
    assert f"Serial: {ws.serial_number}" in html
    assert "Answer Key" not in html
    assert "MathTutor Worksheet" in html

def test_generate_route_still_works(...)  # existing route test(s) keep passing; add one if none covers /worksheets/generate
```

- [ ] **Step 2:** `pytest tests/test_worksheet_service.py -W error -v` → FAIL (module missing).
- [ ] **Step 3:** Implement `src/worksheet_service.py`; refactor `generate_worksheet_route` to use `generate_for_child`.
- [ ] **Step 4:** `pytest tests/ -W error` → all pass.
- [ ] **Step 5:** Commit `feat: shared worksheet generation and printable render`.

### Task 2: Device API — list children, print a new worksheet

**Files:**
- Modify: `src/routes/api.py`
- Test: `tests/test_api_worksheets.py` (reuse the `owner_env`/`owner`/`bearer` patterns from `tests/test_device_tokens.py`; move shared ones to `conftest.py` if needed)

**Interfaces:**
- Consumes: Task 1 `generate_for_child`, `render_printable`; `require_api_auth` (sets `g.user`).
- Produces (Pi relies on these exact shapes):
  - `GET /api/children` → `200 {"children": [{"id": str, "name": str, "age": int, "grade": int}]}` — only `g.user.email`'s children.
  - `POST /api/children/<child_id>/worksheets` → `201 {"worksheet_id": str, "serial": str, "html": str}`; unknown/other-owner → `404 {"error": "not found"}`; no auth → `401`.

- [ ] **Step 1: Write failing tests**

```python
def test_list_children_returns_owner_children_only(client, repository, owner, ...): ...
def test_new_worksheet_returns_html_with_serial(client, owner_child, token):
    r = client.post(f"/api/children/{owner_child.id}/worksheets", headers=bearer(token))
    assert r.status_code == 201
    body = r.get_json()
    assert body["serial"].startswith("WS-")
    assert f"Serial: {body['serial']}" in body["html"]
    assert "answers" not in body and "Answer Key" not in body["html"]
def test_new_worksheet_unknown_child_404(...): assert r.status_code == 404 and r.get_json() == {"error": "not found"}
def test_new_worksheet_other_parents_child_404(...)
def test_new_worksheet_requires_auth_401(...)
def test_new_worksheet_get_not_allowed_405(...)
```

- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** `pytest tests/ -W error` → pass.
- [ ] **Step 5:** Commit `feat: device API to list children and print a new worksheet`.

### Task 3: Pi config and site client

**Files:**
- Create: `pi/mathtutor_pi/__init__.py`, `pi/mathtutor_pi/config.py`, `pi/mathtutor_pi/site_client.py`, `pi/config.example.toml`
- Create: `pi/tests/__init__.py`, `pi/tests/test_config.py`, `pi/tests/test_site_client.py`, `pi/pytest.ini` (or conftest adding `pi/` to `sys.path`)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) ButtonConfig(kid: str, child_id: str, button_pin: int, led_pin: int)`
  - `@dataclass(frozen=True) Config(site_url: str, token: str, printer: str, buttons: tuple[ButtonConfig, ...], print_timeout_s: float = 120, error_flash_s: float = 5, site_timeout_s: float = 30)`
  - `load_config(path: Path) -> Config` — TOML; `token_file` key points at a file whose stripped contents are the token; raises `ConfigError` on missing keys, empty buttons, duplicate pins (across all button/led pins), duplicate kid names, token not starting with `mt_`, or token file mode looser than `0600`.
  - `class SiteError(Exception)`; `@dataclass(frozen=True) PrintableWorksheet(serial: str, html: str)`
  - `class SiteClient(base_url: str, token: str, timeout_s: float)` with `new_worksheet(child_id: str) -> PrintableWorksheet` (POST, `Authorization: Bearer`) and `children() -> list[dict]`. HTTP errors, timeouts, bad JSON → `SiteError` with a short reason (`"unauthorized"`, `"child not found"`, `"timeout"`, `"http 500"`…); the token never appears in messages or `repr`.
- `config.example.toml`: `site_url = "https://mathtutor.mackuntu.com"`, `token_file = "/etc/mathtutor-pi/token"`, `printer = "Brother_HL_L2340DW"`, two `[[buttons]]` for `Philip` and `Sudo` with placeholder child ids and the pins chosen in Task 6's wiring guide.

- [ ] **Step 1: Failing tests** — config: valid example loads; each `ConfigError` case above; client (stub server via `http.server` on a thread, or monkeypatched `urllib.request.urlopen`):

```python
def test_new_worksheet_posts_bearer_and_parses(...): assert ws == PrintableWorksheet("WS-abc", "<html>")
def test_unauthorized_raises_without_token_in_message(...):
    with pytest.raises(SiteError) as e: client.new_worksheet("c1")
    assert "unauthorized" in str(e.value) and TOKEN not in str(e.value) and TOKEN not in repr(client)
def test_404_raises_child_not_found(...)
def test_timeout_raises_site_error(...)   # server sleeps > timeout_s
def test_bad_json_raises_site_error(...)
```

- [ ] **Step 2:** `pytest pi/tests -W error` → FAIL. **Step 3:** implement. **Step 4:** → pass.
- [ ] **Step 5:** Commit `feat(pi): config loader and site client`.

### Task 4: Pi renderer and printer

**Files:**
- Create: `pi/mathtutor_pi/render.py`, `pi/mathtutor_pi/printer.py`
- Test: `pi/tests/test_render.py`, `pi/tests/test_printer.py`

**Interfaces:**
- Both take an injectable `run: Callable[..., subprocess.CompletedProcess] = subprocess.run` so tests use fakes.
- Produces:
  - `class RenderError(Exception)`; `render_pdf(html: str, out_pdf: Path, *, timeout_s: float = 60, run=subprocess.run, chromium: str = "chromium-headless-shell") -> None` — writes HTML to a temp file next to `out_pdf`, runs Chromium `--headless --no-pdf-header-footer --print-to-pdf=<out_pdf> file://<tmp>` (confirm flags against the installed binary in Task 7), deletes the temp HTML always; non-zero exit, `TimeoutExpired`, `FileNotFoundError`, or empty/missing PDF → `RenderError`.
  - `class PrintError(Exception)`; `class CupsPrinter(name: str, run=subprocess.run, sleep=time.sleep, clock=time.monotonic)` with `submit(pdf: Path, title: str) -> str` (`lp -d <name> -t <title> <pdf>`, parse job id from `request id is <name>-<n> ...`) and `wait_done(job_id: str, timeout_s: float, poll_s: float = 2) -> None` (poll `lpstat -W completed -o <name>` / `lpstat -o`; completed → return; timeout → `cancel <job_id>` then `PrintError("printer timeout")`).

- [ ] **Step 1: Failing tests**

```python
def test_render_invokes_chromium_and_removes_temp_html(tmp_path): ...
def test_render_nonzero_exit_raises(tmp_path): ...
def test_render_timeout_raises_and_cleans_up(tmp_path):  # fake run raises TimeoutExpired; no temp html left
def test_render_missing_binary_raises(tmp_path): ...
def test_submit_parses_job_id(): assert printer.submit(pdf, "Philip WS-1") == "Brother_HL_L2340DW-17"
def test_submit_failure_raises_print_error(): ...
def test_wait_done_returns_when_completed(): ...
def test_wait_done_timeout_cancels_job():  # fake clock advances; asserts ["cancel", "Brother_HL_L2340DW-17"] was run
```

- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** `pytest pi/tests -W error` → pass.
- [ ] **Step 5:** Commit `feat(pi): chromium PDF render and CUPS printing`.

### Task 5: Pi button controller

**Files:**
- Create: `pi/mathtutor_pi/light.py`, `pi/mathtutor_pi/controller.py`
- Test: `pi/tests/test_controller.py`

**Interfaces:**
- Consumes: Task 3 `SiteClient`/`SiteError`/`ButtonConfig`, Task 4 `render_pdf`/`RenderError`/`CupsPrinter`/`PrintError`.
- Produces:
  - `class Light(Protocol)`: `steady() -> None`, `blink() -> None`, `flash() -> None`.
  - `class KidButton(kid: str, child_id: str, light: Light, *, site, render, printer, render_lock: threading.Lock, print_timeout_s: float, error_flash_s: float, workdir: Path, sleep=time.sleep)` with `on_press() -> bool` (returns False and logs `"<kid>: busy, press ignored"` if a job is running; otherwise starts a daemon thread, returns True) and `join(timeout: float | None = None)` for tests. Light `steady()` on construction.
  - Job: `blink()` → `site.new_worksheet` → under `render_lock`: `render(html, pdf)` → `printer.submit(pdf, f"{kid} {serial}")` → `printer.wait_done(job, print_timeout_s)` → `steady()`. Any `SiteError | RenderError | PrintError | Exception` → log `"<kid>: failed: <reason>"`, `flash()`, `sleep(error_flash_s)`, `steady()`. PDF removed after the job either way. Busy cleared last.
- Logging via `logging.getLogger("mathtutor_pi")`; log `"<kid>: pressed"`, `"<kid>: printed <serial>"`.

- [ ] **Step 1: Failing tests** (fake site/render/printer/light recording calls; fake `sleep`)

```python
def test_press_prints_and_returns_to_steady(): assert light.calls == ["steady", "blink", "steady"]
def test_presses_while_busy_are_ignored():  # site blocks on an Event; second on_press() is False; one worksheet requested
def test_two_kids_run_independently():  # Philip blocked in site call; Sudo's press still completes
def test_renders_are_serialized():  # two kids; fake render records overlap → never concurrent
def test_print_failure_flashes_then_ready(): assert light.calls == ["steady", "blink", "flash", "steady"]
def test_site_error_flashes_and_logs_reason(caplog): ...
def test_render_lock_released_after_failure():  # render raises for Philip; Sudo then prints fine
def test_press_after_failure_works_again(): ...
```

- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** `pytest pi/tests -W error` → pass.
- [ ] **Step 5:** Commit `feat(pi): per-kid button controller`.

### Task 6: Pi entrypoint, service, setup, wiring guide, CI

**Files:**
- Create: `pi/mathtutor_pi/main.py`, `pi/mathtutor_pi/__main__.py`, `pi/systemd/mathtutor-pi.service`, `pi/setup.sh`, `pi/README.md`
- Modify: `.github/workflows/tests.yml` (add a `pytest pi/tests -W error` step), `CLAUDE.md` (one line under Architecture for `pi/`)
- Test: `pi/tests/test_main.py`

**Interfaces:**
- Consumes: Tasks 3–5.
- Produces:
  - `python3 -m mathtutor_pi run --config /etc/mathtutor-pi/config.toml` — loads config, builds one `KidButton` per button with a `gpiozero.LED`-backed `Light` (steady=`on()`, blink=`blink(0.4, 0.4)`, flash=`blink(0.1, 0.1)`) and `gpiozero.Button(pin, pull_up=True, bounce_time=0.05)` whose `when_pressed` calls `on_press`; blocks on `signal.pause()`.
  - `python3 -m mathtutor_pi print <kid> --config …` — runs one job for that kid synchronously without GPIO (console `Light` that logs), exit 0 on success / 1 on failure. Used for testing before buttons arrive.
  - `python3 -m mathtutor_pi children --config …` — prints `name  id` per child from `/api/children` (owner uses it to fill config).
- Service: `User=mathtutor-pi`, `SupplementaryGroups=gpio lp`, `ExecStart=/usr/bin/python3 -m mathtutor_pi run --config /etc/mathtutor-pi/config.toml`, `WorkingDirectory=/opt/mathtutor-pi`, `Environment=PYTHONPATH=/opt/mathtutor-pi`, `Restart=always`, `RestartSec=5`, `PrivateTmp=yes`, `MemoryMax=600M`, `Nice=10`.
- `setup.sh` (idempotent, run as root on the Pi from a checkout or rsync of `pi/`): apt install `python3-gpiozero python3-lgpio cups chromium-headless-shell`; system user `mathtutor-pi` (no login, groups `gpio,lp`); copy package to `/opt/mathtutor-pi`; create `/etc/mathtutor-pi/` (`0750 root:mathtutor-pi`) with `config.toml` from example if absent and an empty `token` (`0600 mathtutor-pi`) if absent; add printer if missing: `lpadmin -p Brother_HL_L2340DW -E -v "$PRINTER_URI" -m everywhere` where `PRINTER_URI` defaults to the first `ipp://` from `lpinfo --include-schemes dnssd -v` matching `HL-L2340D` (override via env); install + enable the service. Never prints the token.
- `README.md`: parts list (spec), wiring table with chosen pins (e.g. Philip button GPIO17 + GND, LED GPIO27 + GND; Sudo button GPIO22 + GND, LED GPIO23 + GND — physical pin numbers too), owner steps (create token at `/settings/devices`, write it to `/etc/mathtutor-pi/token`, `children` command → fill child ids, `print Philip` test, `journalctl -u mathtutor-pi -f`).

- [ ] **Step 1: Failing tests** — `main` arg parsing and `print` subcommand with fakes (patch the builders), exit codes 0/1; `gpiozero` not imported when running `print`/`children`.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement all files. `bash -n pi/setup.sh` passes.
- [ ] **Step 4:** `pytest pi/tests -W error` and `pytest tests/ -W error` → pass.
- [ ] **Step 5:** Commit `feat(pi): service entrypoint, setup script, wiring guide`.

### Task 7: Deploy and verify on homepi (controller-run, not a subagent code task)

- [ ] **Step 1:** Ask the user before deploying the site (production deploy). Deploy the branch to production (`vercel deploy --prod`) once approved; smoke `GET /api/children` with a token → 200.
- [ ] **Step 2:** `rsync -a pi/ martin@homepi.local:~/mathtutor-pi-src/` then `ssh martin@homepi.local sudo bash ~/mathtutor-pi-src/setup.sh`. Confirm Chromium flags work: render a sample HTML to PDF on the Pi.
- [ ] **Step 3:** User creates a device token at `/settings/devices` and writes it to `/etc/mathtutor-pi/token` (user runs the command; token never passes through chat). Run `children`, fill child ids into config.
- [ ] **Step 4:** `sudo -u mathtutor-pi python3 -m mathtutor_pi print Philip --config /etc/mathtutor-pi/config.toml` → a sheet with a serial prints; same for Sudo. Printer off → exit 1 after timeout, job cancelled.
- [ ] **Step 5:** `systemctl status mathtutor-pi` active; Plex still `active`; `free -h` sane. Button test waits for hardware arrival (user).
