# PySack

Encrypt Python projects with **Nuitka** and package with **PyInstaller** — one-command source code protection for your Python applications.

## Features

- **Nuitka Encryption** — Compile `.py` to `.pyd` (Windows) / `.so` (Linux/macOS) for strong source code protection
- **Auto Dependency Detection** — Scan `.pyi` files and known transitive dependency maps to resolve imports automatically
- **PyInstaller Integration** — Package encrypted `.pyd` files into a standalone executable
- **Full Workflow** — Encrypt + Pack in a single command
- **Config File Support** — Use `.pysack.cfg` for repeatable builds

## Installation

```bash
pip install pysack
```

## Usage

### Encrypt only

```bash
pysack encrypt -i /path/to/project -o /path/to/output
```

### Package encrypted project

```bash
pysack pack -i /path/to/encrypted_project -m main.py -n MyApp
```

### Full workflow (encrypt + pack)

```bash
pysack full -i /path/to/project -m main.py -n MyApp
```

### Build from config file

Create `.pysack.cfg` in your project directory:

```ini
[pysack]
paths = src/
build_dir = encrypted_output
main_py = main.py
dist_name = MyApp
force_encrypt_files = client.py, tool.py

[pyinstaller]
main_entry = main.py
dist_name = MyApp
```

Then run:

```bash
pysack build
```

## How It Works

```

┌─────────────────────────────────────────────────────┐
│  pysack full -i project/ -m main.py                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Nuitka compiles all .py files → .pyd/.so         │
│  2. Generates .pyi files (import info)               │
│  3. Auto-detects dependencies from .pyi              │
│  4. PyInstaller packages everything into dist/       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Options

| Flag | Description |
|------|-------------|
| `-i, --input` | File or directory to encrypt |
| `-o, --output` | Output directory (default: `<input>/dist`) |
| `-I, --ignore` | Files/directories to skip, comma-separated |
| `-e, --except-main` | Skip files containing `__main__` (default: 1) |
| `-c, --config` | Config file path |
| `-m, --main` | Main entry file (required for pack/full) |
| `-n, --name` | Output dist directory name |
| `--force-encrypt` | Force encrypt files containing `__main__` |
| `--hidden-imports` | Extra modules for PyInstaller `--hidden-import` |
| `--collect-submodules` | Extra packages for `--collect-submodules` |

## License

MIT