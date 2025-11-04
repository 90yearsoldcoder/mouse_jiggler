# 🖱️ Mouse Jiggler

A minimal, cross‑platform mouse jiggler controllable from the terminal.  
Designed for reliability, zero dependencies beyond Python itself, and clean start/stop control.

## ✨ Features

- CLI: `start` / `stop` / `status` / `run`
- Human‑readable timing: `--interval 30s`, `--duration 2h`, `--amplitude 1`
- Cross‑platform: Windows, macOS, Linux
- Graceful stop via STOP flag (no force‑kill)
- Single instance with PID file
- Packable binary with PyInstaller

## 📦 Installation (Conda recommended)

```powershell
# 1) Create and activate environment
conda create -n jiggler python=3.11 -y
conda activate jiggler

# 2) Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt`:
```text
pynput>=1.7
```

## ▶️ Usage (from source)

Run directly in the environment:

```powershell
# Start background jiggler (30 s interval × 1 px step × 10 minutes)
python -m mouse_jiggler.cli start --interval 30s --amplitude 1 --duration 10m

# Check status
python -m mouse_jiggler.cli status

# Stop
python -m mouse_jiggler.cli stop
```

Debug/visible test (runs in foreground so you can watch the cursor move):
```powershell
python -m mouse_jiggler.cli run --interval 1s --amplitude 50 --duration 10s
```

Tips:
- Use `--force` with `start` to replace an existing instance.
- Use humanized specs: `500ms`, `30s`, `10m`, `2h`.

## ⚙️ Build a standalone binary

```powershell
python -m pip install pyinstaller
pyinstaller --onefile --name mousejiggler -p src --collect-submodules pynput src/mouse_jiggler/cli.py
```

Result:
- Windows: `dist\mousejiggler.exe`
- macOS/Linux: `./dist/mousejiggler`

Examples:
```powershell
./dist/mousejiggler start --interval 30s --amplitude 1 --duration 1h
./dist/mousejiggler status
./dist/mousejiggler stop
```

## 🗂️ State directory

Where runtime state is stored:

- Windows: `%LOCALAPPDATA%\MouseJiggler`
- macOS/Linux: `~/.mousejiggler`

Contents:
- `jiggler.pid` — active process ID
- `STOP` — flag for graceful termination
- `run.log` — stdout/stderr of background run (for debugging)

## 🪟 Windows notes

- Uses native APIs (or `pynput`) for cursor movement; no special privileges required.
- Large interval + small amplitude may be imperceptible. Verify with `--interval 1s --amplitude 50`.

## 🍎 macOS / 🐧 Linux notes

- macOS: grant Accessibility permissions to your terminal or the built binary.
- Wayland sessions may block synthetic input; use X11 or adjust security policy.
- Ensure `~/.mousejiggler` is writable.

## 🧠 Design highlights

- Clean OOP: core logic, adapters (OS bindings), CLI entry point.
- Abstract ports for Mouse, Time, State, Process, Daemon → easy testing and replacement.
- Default pattern: square loop (+x → +y → −x → −y) to avoid cursor drift.
- Configurable intervals; quick stop responsiveness.

## 🔧 Troubleshooting

- “Launched, but PID not confirmed”:
  - Run foreground to see errors:  
    `python -m mouse_jiggler.cli run --interval 5s --amplitude 5 --duration 30s`
  - Check `run.log` in the state directory.
  - Ensure the state directory is writable.
  - On macOS/Wayland, confirm input permissions.

- “Not running” after `start`:
  - Verify Python path and that `pynput` is installed in the same environment.
  - Try a visible test (`run` with larger amplitude) to confirm movement.

## 📜 License

MIT (see LICENSE)
