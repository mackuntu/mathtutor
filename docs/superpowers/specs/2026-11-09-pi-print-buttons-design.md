# Pi Print Buttons — Design

**Date:** 2026-11-09
**Status:** Draft for approval

## Intent

Two kids, Philip and Sudo, each get their own physical button. When a kid is
ready for more practice, they press their button and a fresh worksheet at their
level comes out of the home printer. No screen, no parent, no login. The point
is independence: the kid decides when they're ready, and the paper just appears.

## Goals

- One press → one new worksheet for that kid, printed on the home printer.
- Each kid's button is theirs; it always prints for them.
- The button light tells the kid what is happening.
- Runs unattended on the Pi; survives reboots and transient network/printer
  problems.
- Cheap, DIY hardware bought on Amazon (~$15–25).

## Non-goals

- No choosing problem type, count, or difficulty at the button. The worksheet
  is exactly what the site's existing "Generate" makes for that child today.
- No grading on the Pi (the separate photo-grader project handles grading).
- No screen, display, sound, or app on the Pi.
- No support for more than the two configured buttons in v1 (config should not
  hard-code two, but no UI to add more).

## Anti-goals (failure even if it "works")

- A held or mashed button printing a pile of sheets (wasted paper).
- One kid's press blocking or delaying the other kid's.
- The Pi silently stuck — light dark or blinking forever with no way to tell why.
- Device credential readable by anyone on the network, or broader than `/api`.
- Breaking or slowing Plex Media Server, which shares this Pi.
- Changing the printed layout of `src/templates/problem_grid.html` (project
  constraint: never modify its layout).

## Environment (facts)

| Thing | Value |
|---|---|
| Pi | Raspberry Pi 5, 8 GB, in an Argon NEO 5 case |
| OS | Raspberry Pi OS Lite 64-bit (Debian 13 trixie), freshly flashed 2026-11-09 |
| Host | `homepi.local` (10.0.0.237, DHCP), wired Ethernet, no Wi-Fi |
| Login | user `martin`, SSH key only, passwordless sudo |
| Also running | Plex Media Server (apt repo `repo.plex.tv`), Samba share `media` at `/mnt/media` (2 TB USB HDD) |
| Printer | Brother HL-L2340DW, on Wi-Fi, same LAN. AirPrint-capable. |
| Site | `https://mathtutor.mackuntu.com` (Flask on Vercel, Postgres/Neon) |
| Site auth for devices | Device tokens (`mt_…`), created at `/settings/devices`, sent as `Authorization: Bearer` on `/api/*` only; act as the owner (first `ALLOWED_EMAILS` entry). `/api/ping` exists. |

## Hardware (decided)

- Two 30 mm momentary arcade buttons with **built-in 5 V LEDs** (60 mm dome
  optional). 5 V LEDs, not 12 V — driven directly from 3.3 V GPIO (dimmer but
  fine; resistor is built in).
- Female–female Dupont jumpers + pre-wired 2.8 mm spade connectors. No solder,
  no breadboard, no external resistors.
- Each button: switch between a GPIO input and GND, using the Pi's internal
  pull-up. LED between a GPIO output and GND.
- Optional project box or shoebox. Wires reach the 40-pin header through the
  NEO 5's top opening (or lid off).
- Exact pin assignment is the builder's call; it must live in config, not code,
  and the wiring guide must show it.

## Behavior (decided with the user)

| State | Light |
|---|---|
| Ready | Steady on (also shows the Pi is alive) — *builder's call, approved as a guess* |
| Working (fetching + sending to printer) | Blinking |
| Done (printer accepted the job) | Back to steady on |
| Failure (site unreachable, printer off/out of paper, any error) | Fast flash for a few seconds, then back to ready |

- **Extra presses while that kid's light is blinking are ignored** (user
  decision). After it returns to ready, a new press prints a new sheet.
- The two buttons are independent: both kids can press at once; each job runs
  on its own.
- "Done" means the printer **accepted** the job (CUPS job completed/sent), not
  that paper physically came out — network printers don't report that
  reliably.
- Every press and every failure reason is logged (journald) so the owner can see
  why something failed.
- Debounce the switch so a single physical press is one press.

## How it works (decided)

### Site side (new, in this repo)

A new authenticated JSON endpoint under `/api` that, for a given child, does
exactly what `GET /worksheets/generate` does today (age from the child,
`count=30`, difficulty from `get_school_year_progress()`, saves the worksheet
with its correct answers) and returns what the Pi needs to print it.

- Auth: existing `require_api_auth` device-token bearer auth; must only act on
  children belonging to the token's owner.
- The Pi identifies kids by a stable child id stored in its config. The owner
  needs a way to find each child's id (e.g. a `GET /api/children` list
  endpoint, or showing ids on the settings page) — builder's choice.
- The worksheet must print identically to printing from the browser today
  (same `worksheet.html` / `problem_grid.html` rendering, same serial number on
  the sheet). Reuse the existing generation code; do not duplicate it.

### Pi side (new, in this repo, e.g. `pi/`)

- Python program run as a systemd service (starts at boot, restarts on crash),
  as an unprivileged user with GPIO and printer access.
- GPIO via **`gpiozero`** (the Pi 5 does not work with `RPi.GPIO`).
- **Rendering (my call):** the Pi fetches the worksheet's printable HTML with
  its device token and renders it to PDF locally with headless Chromium, so the
  output matches the browser print exactly and the server stays free of PDF
  libraries. (Builder may pick another approach only if it prints identically
  and keeps the token out of URLs/logs.)
- **Printing:** CUPS with the printer added driverless via AirPrint/IPP
  (`ipp://…` / `everywhere`). Brother's own Linux driver is x86-only — don't
  use it. Fallback if driverless misbehaves: `printer-driver-brlaser`.
- Printer found via mDNS; config may pin its IP if discovery is flaky.
- Config file on the Pi (not in git): site URL, device token, printer name, and
  per-button `{kid name, child id, button pin, LED pin}`. Token file readable
  only by the service user (`0600`).
- Network/site/printer failures are expected states, not crashes: time out,
  fast-flash, log, return to ready.

### Setup and docs

- A repeatable setup path (script or documented steps) that installs packages,
  adds the printer, installs the service, and writes the config skeleton —
  runnable over SSH on `homepi.local`.
- A one-page wiring guide (which wire goes on which pin) and owner setup steps:
  create device token at `/settings/devices`, put it on the Pi, map kids to
  buttons, press to test.

## Constraints

- Never modify the layout of `src/templates/problem_grid.html`.
- Child ages use the existing end-of-school-year calculation; the Pi never
  computes ages.
- Device tokens are secrets: never committed, never logged, never in URLs.
- Existing tests run against real Postgres (`pytest tests/ -W error`); new site
  code follows that, TDD.
- Must coexist with Plex and Samba on the same Pi (small memory/CPU footprint
  when idle; Chromium only runs per print).
- Branch note: the `raspberry-pi` worktree branched from `a1f332d`; the hosting
  branch has later commits (e.g. `49c3cce`, Neon `DATABASE_URL` fallback). The
  builder should base the work on the latest hosting branch / `main` once
  merged.

## Settled after builder review (my calls)

1. **Serial number is printed.** Today's `GET /worksheets/generate` page omits
   it; the button sheet includes it (`serial_number`, as `view_worksheet`
   renders it) so the photo grader can match a photo to its worksheet. This
   is the one intended difference from today's Generate output.
2. **Printable HTML comes from `/api`.** Existing worksheet pages use session
   auth, so the new `/api` endpoint renders the same `worksheet.html` (with
   base layout and print CSS) via a helper shared with the existing routes.
   Static assets it references must load without login.
3. **One render at a time.** A global lock serializes Chromium renders (memory,
   Plex). A press never waits to *start*: the kid's light blinks immediately
   while their job queues behind the other kid's.
4. **Orphan worksheets are tolerated.** The worksheet is saved when generated;
   if printing fails, it stays in the history (same as an unprinted Generate
   today). No idempotency keys; the next press makes a new sheet.
5. **"Done" = CUPS reports the job completed** (sent to the printer). If not
   completed within ~120 s (printer asleep/off), cancel the job and treat as
   failure (fast flash).
6. **No answers in the printable output.** The endpoint never renders the
   answer-key mode and never returns answers.
7. **Unknown or other-owner child id → 404.**
8. **Base branch:** build on `mackuntu/host-on-vercel` (latest), not the older
   `a1f332d` the `raspberry-pi` branch started from; drop the stale
   `vercel.json` there accordingly.

## Left to the builder

- Endpoint names and response shape.
- GPIO pin numbers, blink rates, fast-flash duration, timeouts.
- How the Pi gets the printable HTML to Chromium with the bearer header
  (e.g. Playwright `extra_http_headers`, or fetch-then-render-local-file).
- Package layout under `pi/`, how the Pi code is tested off-device (GPIO and
  printing behind small interfaces with fakes).
- Setup script vs. documented steps.
