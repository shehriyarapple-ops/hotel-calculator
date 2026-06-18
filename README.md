# Hotel Calculator (Android)

A custom calculator for hotel billing with fixed-value buttons, editable values,
a `÷2` (share between 2 plates) mode, and daily saved calculations.

## Features

- **Custom item buttons** with fixed values:

  | Button   | Value |
  |----------|-------|
  | 1F       | 1950  |
  | 1H       | 1050  |
  | 1Q       | 600   |
  | 1FWR     | 1650  |
  | 1HWR     | 850   |
  | 1QWR     | 450   |
  | 1Raita   | 70    |
  | 1G       | 10    |
  | 1S       | 90    |
  | 1L       | 180   |
  | 1.5L     | 230   |
  | 2L       | 260   |

  > The 1650 button is named **1FWR** and the 850 button is **1HWR**. You can
  > rename any button or change its value from the Settings screen at any time.

- **÷2 mode**: Tap **"÷2 mode"** to turn it ON, then tap an item — its value is
  halved (e.g. one plate shared between 2 people). It auto-turns off after one use.
- **Add custom amount**: type any number and press **Add**.
- **Undo / Clear** the running total.
- **Edit values later**: open **Settings** to change any name/value, add new
  buttons, or delete buttons. Changes are saved permanently to disk.
- **Save Today**: stores the current bill under today's date. Every calculation
  made in a day is grouped by that date.
- **History**: view all saved calculations grouped by date with daily totals,
  and delete a day if needed.

## Where data is stored

- `hotel_calc_data/buttons.json` — your editable button definitions.
- `hotel_calc_data/history.json` — all saved daily calculations.

On Android these live in the app's private storage; on desktop they sit next to
`main.py`.

---

## Run on your PC (to test first)

```powershell
pip install kivy==2.3.0
python main.py
```

---

## Build the Android APK

Buildozer (the tool that makes the APK) only runs on **Linux**. On Windows use
**WSL** (Windows Subsystem for Linux) or a Linux machine / GitHub Actions.

### Option A — WSL (Ubuntu) on Windows

1. Install WSL (run in PowerShell as admin, then reboot):
   ```powershell
   wsl --install
   ```
2. Open Ubuntu, then install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip git zip unzip openjdk-17-jdk \
       autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
       libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   pip3 install --user buildozer cython==0.29.36
   ```
3. Copy this project folder into WSL (or `cd` into it), then build:
   ```bash
   buildozer -v android debug
   ```
4. The APK appears in the `bin/` folder. Copy it to your phone and install
   (enable "Install unknown apps").

### Option B — GitHub Actions (no Linux needed)

Push this folder to a GitHub repo and add a workflow using
`ArtemSBulgakov/buildozer-action`. The APK is produced as a build artifact you
can download. Ask me and I'll generate the workflow file for you.

---

## Editing values later

You don't need code changes — just open the app, tap **Settings**, edit any
value, and tap **Save Changes**. If you'd rather I change the defaults in code,
tell me the new values and I'll update `main.py`.
