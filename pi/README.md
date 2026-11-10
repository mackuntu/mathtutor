# MathTutor print buttons (Raspberry Pi)

Two arcade buttons on a Raspberry Pi 5. Press a kid's button and the Pi asks
the MathTutor site for a fresh worksheet, renders it to PDF with headless
Chromium, and prints it on the Brother HL-L2340DW via CUPS (AirPrint,
driverless; do not install Brother's driver).

Button light: **steady** = ready, **slow blink** = working, **fast flash** = failed
(then back to steady after a few seconds).

## Parts

- 2 x 30 mm momentary arcade buttons with built-in 5 V LEDs
- Female-female Dupont jumper wires (2 per button for the switch, 2 for the LED)
- Pre-wired 2.8 mm spade connectors (to fit the button and LED tabs)
- Optional: project box

## Wiring

Pins are BCM GPIO numbers; physical header pin in parentheses. Buttons use the
internal pull-up, so a button connects its GPIO to GND when pressed.

| Kid    | Part         | Connect to              |
|--------|--------------|-------------------------|
| Philip | Button       | GPIO17 (pin 11) and GND (pin 9)  |
| Philip | LED + / -    | GPIO27 (pin 13) / GND (pin 14)   |
| Sudo   | Button       | GPIO22 (pin 15) and GND (pin 20) |
| Sudo   | LED + / -    | GPIO23 (pin 16) / GND (pin 25)   |

- The switch has no polarity: either tab to the GPIO, the other to GND.
- The LED does: **+ goes to the GPIO, - goes to GND**. The Pi's 3.3 V output is
  below the LED's 5 V rating, so it will be dimmer than rated; that is expected.
- Do not connect the LED + to the Pi's 5 V pin without a transistor and
  resistor; GPIOs cannot source the current.

Pins are set in `/etc/mathtutor-pi/config.toml` (`button_pin`, `led_pin`).

## Install

Copy the `pi/` directory to the Pi (rsync or git checkout), then:

```bash
cd pi
sudo ./setup.sh
```

It installs packages, creates the `mathtutor-pi` service user, copies the code
to `/opt/mathtutor-pi`, creates `/etc/mathtutor-pi/`, adds the printer queue
`Brother_HL_L2340DW` if missing, and enables the systemd service. It is safe to
re-run. If the printer is not discovered, re-run with
`sudo PRINTER_URI=ipp://<address>/ipp/print ./setup.sh`. It does not touch Plex
or Samba.

## Owner steps (once)

1. On the site, open `/settings/devices` and create a device token.
2. Put it in the token file (mode 0600, owned by `mathtutor-pi`):
   `sudoedit /etc/mathtutor-pi/token` (contents: just `mt_...`). If sudoedit
   loosens the mode, run
   `sudo chown mathtutor-pi:mathtutor-pi /etc/mathtutor-pi/token && sudo chmod 600 /etc/mathtutor-pi/token`.
3. List the children and copy their ids into `/etc/mathtutor-pi/config.toml`:

   ```bash
   sudo -u mathtutor-pi PYTHONPATH=/opt/mathtutor-pi python3 -m mathtutor_pi children --config /etc/mathtutor-pi/config.toml
   ```

4. Test a print without the buttons:

   ```bash
   sudo -u mathtutor-pi PYTHONPATH=/opt/mathtutor-pi python3 -m mathtutor_pi print Philip --config /etc/mathtutor-pi/config.toml
   ```

5. Start the service and watch it:

   ```bash
   sudo systemctl restart mathtutor-pi
   journalctl -u mathtutor-pi -f
   ```

## Development

```bash
pytest pi/tests -W error   # run separately from the site's tests/
```

`gpiozero` is imported only by the `run` command, so tests and the `print` /
`children` commands work on any machine.
