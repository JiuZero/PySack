import os
import re
import shutil
import subprocess
import sys
import ast
import importlib.util
from typing import Union, List

from pysack.log import logger, C


def search(content, regexs):
    if isinstance(regexs, str):
        return re.search(regexs, content)

    for regex in regexs:
        if re.search(regex, content):
            return True


def walk_file(file_path):
    if os.path.isdir(file_path):
        for current_path, sub_folders, files_name in os.walk(file_path):
            for file in files_name:
                file_path = os.path.join(current_path, file)
                yield file_path

    else:
        yield file_path


def copy_files(src_path, dst_path):
    if os.path.isdir(src_path):
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)

        def callable(src, names: list):
            if dst_path in src:
                return names
            return ["dist", ".git", "venv", ".idea", "__pycache__"]

        shutil.copytree(src_path, dst_path, ignore=callable)
    else:
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        shutil.copyfile(src_path, os.path.join(dst_path, os.path.basename(src_path)))


def get_py_files(files, ignore_files: Union[List, str, None] = None):
    """
    @summary:
    ---------
    @param files: file list
    @param ignore_files: files to ignore, supports regex
    ---------
    @result:
    """
    for file in files:
        if file.endswith(".py"):
            if ignore_files and search(file, regexs=ignore_files):  # this file is in the ignore list
                pass
            else:
                yield file


def filter_cannot_encrypted_py(files, except_main_file, force_encrypt_files=None):
    """
    Filter out files that cannot be encrypted, such as log.py, __main__.py,
    and files containing if __name__ == "__main__":
    Args:
        files: file list (absolute paths)
        except_main_file: whether to filter out files containing __main__
        force_encrypt_files: list of filenames (basename match) to force encrypt even if they contain __main__

    Returns:

    """
    _files = []
    force_encrypt_basenames = set()
    if force_encrypt_files:
        for f in force_encrypt_files:
            force_encrypt_basenames.add(os.path.basename(f))

    for file in files:
        if search(file, regexs="__.*?.py"):
            continue

        if except_main_file and os.path.basename(file) not in force_encrypt_basenames:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                if search(content, regexs="__main__"):
                    continue

        _files.append(file)

    return _files


def encrypt_py(py_files: list):
    encrypted_py = []
    original_cwd = os.getcwd()

    total_count = len(py_files)
    for i, py_file in enumerate(py_files):
        try:
            dir_name = os.path.dirname(py_file)
            file_name = os.path.basename(py_file)

            os.chdir(dir_name)

            logger.info("Encrypting {}/{}, {}".format(i + 1, total_count, file_name))
            result = subprocess.run(
                ["python", "-m", "nuitka", "--module", file_name],
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode != 0:
                raise Exception(
                    result.stderr[-1000:] if result.stderr else result.stdout[-1000:]
                )

            encrypted_py.append(py_file)
            logger.info(f"{C.GREEN}  Encryption successful: {file_name}{C.RESET}")

        except Exception as e:
            logger.exception("Encryption failed: {}, error {}".format(py_file, e))
        finally:
            os.chdir(original_cwd)

    return encrypted_py


def delete_files(files_path):
    """
    @summary: delete files
    ---------
    @param files_path: file paths (py files)
    ---------
    @result:
    """
    for file in files_path:
        try:
            if os.path.exists(file):
                os.remove(file)  # py file
        except Exception:
            pass


def rename_excrypted_file(output_file_path):
    """
    Nuitka generates .pyd filenames with platform tags (e.g. module.cp314-win_amd64.pyd),
    rename them to module.pyd for proper import.
    """
    files = walk_file(output_file_path)
    for file in files:
        if file.endswith(".pyd") or file.endswith(".so"):
            new_filename = re.sub(r"(.*)\..*\.(.*)", r"\1.\2", file)
            if new_filename != file:
                os.rename(file, new_filename)


def start_encrypt(
    input_file_path,
    output_file_path: str = None,
    ignore_files: Union[List, str, None] = None,
    except_main_file: int = 1,
    force_encrypt_files: Union[List, None] = None,
):
    assert input_file_path, "input_file_path cannot be null"

    assert (
        input_file_path != output_file_path
    ), "output_file_path must be diffent with input_file_path"

    if output_file_path and os.path.isfile(output_file_path):
        raise ValueError("output_file_path need a dir path")

    input_file_path = os.path.abspath(input_file_path)
    if not output_file_path:  # no output path specified
        if os.path.isdir(
            input_file_path
        ):  # if input is a directory, output defaults to input_file_path/dist/project_name
            output_file_path = os.path.join(
                input_file_path, "dist", os.path.basename(input_file_path)
            )
        else:
            output_file_path = os.path.join(os.path.dirname(input_file_path), "dist")
    else:
        if os.path.isdir(input_file_path):
            output_file_path = os.path.join(os.path.abspath(output_file_path),os.path.basename(input_file_path))
        else:
            output_file_path = os.path.abspath(output_file_path)

    # copy source files to target directory
    copy_files(input_file_path, output_file_path)

    files = walk_file(output_file_path)
    py_files = get_py_files(files, ignore_files)

    # filter out files that should not be encrypted
    need_encrypted_py = filter_cannot_encrypted_py(py_files, except_main_file, force_encrypt_files)

    encrypted_py = encrypt_py(need_encrypted_py)

    delete_files(encrypted_py)
    rename_excrypted_file(output_file_path)

    # clean up Nuitka compilation artifacts
    for item in need_encrypted_py:
        dir_name = os.path.dirname(item)

        # Nuitka generated <module>.build directory
        nuitka_build_dir = os.path.join(dir_name, os.path.splitext(os.path.basename(item))[0] + ".build")
        if os.path.exists(nuitka_build_dir):
            try:
                shutil.rmtree(nuitka_build_dir, onerror=lambda fn, p, e: None)
            except Exception:
                pass

    logger.info(f"{C.CYAN}Encryption completed: total={len(need_encrypted_py)}, success={len(encrypted_py)}, output: {output_file_path}{C.RESET}")

    return output_file_path


def auto_detect_dependencies(encrypted_dir):
    """
    Auto-detect third-party dependencies from Nuitka-generated .pyi files.

    Args:
        encrypted_dir: encrypted project directory

    Returns:
        (hidden_imports, collect_submodules) tuple
        - hidden_imports: list of modules needing --hidden-import
        - collect_submodules: list of packages recommended for --collect-submodules
    """
    # Python standard library module names (3.10+)
    try:
        stdlib_modules = sys.stdlib_module_names
    except AttributeError:
        stdlib_modules = set()

    # project internal modules (identified via .pyi, .pyd file paths and __init__.py directories)
    internal_modules = set()
    internal_packages = set()
    for root, dirs, files in os.walk(encrypted_dir):
        rel = os.path.relpath(root, encrypted_dir)
        if rel == ".":
            pass  # do not skip root directory
        elif rel.startswith("dist") or rel.startswith("build") or rel.startswith("."):
            continue
        for f in files:
            if f.endswith(".pyi") or f.endswith(".pyd"):
                name = os.path.splitext(f)[0]
                if rel == ".":
                    internal_modules.add(name)
                else:
                    internal_modules.add(rel.replace(os.sep, ".") + "." + name)
            if f == "__init__.py":
                # register directory package name (e.g. core, core.database, web.engines, etc.)
                pkg_name = rel.replace(os.sep, ".")
                internal_packages.add(pkg_name)

    all_third_party = set()
    pyi_files = []
    for root, dirs, files in os.walk(encrypted_dir):
        rel = os.path.relpath(root, encrypted_dir)
        if rel == ".":
            pass  # do not skip root directory
        elif rel.startswith("dist") or rel.startswith("build") or rel.startswith("."):
            continue
        for f in files:
            if f.endswith(".pyi"):
                pyi_files.append(os.path.join(root, f))

    logger.info(f"{C.CYAN}Extracting dependency info from {len(pyi_files)} .pyi files{C.RESET}")

    for pyi_file in pyi_files:
        try:
            with open(pyi_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        for line in content.splitlines():
            line = line.strip()
            # match import X and from X import Y
            m = re.match(r"^(?:from\s+(\S+)\s+import|\s*import\s+(\S+))", line)
            if not m:
                continue
            module_name = m.group(1) or m.group(2)
            # get top-level package name (e.g. typing_extensions.TypeAlias -> typing_extensions)
            top_module = module_name.split(".")[0]

            # filter standard library — skip top-level modules, keep submodules (e.g. xml.dom)
            if top_module in stdlib_modules:
                if module_name == top_module:
                    # top-level stdlib module (e.g. os, sys), skip
                    continue
                # stdlib submodule (e.g. xml.dom, collections.abc) — add full name
                all_third_party.add(module_name)
                continue
            # filter __future__
            if top_module == "__future__":
                continue
            # filter project internal modules
            # Top-level internal modules (e.g. "conf", "core") are discovered by
            # PyInstaller's modulegraph. Submodules of internal packages (e.g.
            # "conf.i18n") may NOT be discovered because the importing module is
            # compiled to .pyd/.so, so we add them with their full dotted name.
            if module_name in internal_modules:
                if "." not in module_name:
                    continue  # top-level internal module, skip
                # internal submodule (e.g. conf.i18n) — add full name
                all_third_party.add(module_name)
                continue
            if top_module in internal_modules and "." not in module_name:
                continue  # top-level import of internal module, skip
            if module_name in internal_packages:
                continue  # exact internal package (e.g. "import conf"), skip
            if top_module in internal_packages:
                # importing from internal package (e.g. "from conf.i18n import t")
                if module_name == top_module:
                    continue  # top-level internal package import, skip
                # submodule of internal package (e.g. "conf.i18n") — add full name
                all_third_party.add(module_name)
                continue
            # filter names starting with _ (usually internal modules)
            if top_module.startswith("_"):
                continue

            all_third_party.add(module_name)

    # Known transitive dependency mapping: when a package is detected, automatically supplement
    # its commonly used transitive dependencies. These dependencies are not captured by .pyi files
    # (since they are imported internally by third-party libraries), but are required at runtime.
    # Only supplement transitive dependencies for already-detected packages to avoid blind imports.
    TRANSITIVE_DEPS = {
        "sqlalchemy": ["aiosqlite", "greenlet"],
        "fastapi": ["python_multipart"],
        "uvicorn": ["httptools", "watchfiles"],
        "cryptography": ["cffi"],
        "pydantic": ["pydantic_core", "typing_extensions"],
        "sentence_transformers": ["transformers", "torch", "tokenizers"],
        "httpx": ["httpcore", "h11", "certifi", "sniffio"],
        "requests": ["urllib3", "idna", "charset_normalizer", "certifi"],
        "rich": ["markdown_it", "pygments"],
        "numpy": ["numpy._core._multiarray_umath"],
    }

    # supplement transitive dependencies from known mappings (only for detected packages)
    for pkg, deps in TRANSITIVE_DEPS.items():
        if pkg in all_third_party:
            for dep in deps:
                if dep not in all_third_party and dep not in stdlib_modules:
                    try:
                        spec = importlib.util.find_spec(dep)
                    except (ModuleNotFoundError, ImportError):
                        spec = None
                    if spec is not None:
                        all_third_party.add(dep)
                        logger.info(f"{C.CYAN}Added transitive dependency ({pkg} -> {dep}){C.RESET}")

    # verify modules exist, filter out non-existent modules (avoid false positives from .pyi path simplification)
    # Note: internal submodules (e.g. conf.i18n, core.executor) are project-internal and won't
    # be found by find_spec() from the pysack environment, so we keep them unconditionally.
    verified_hidden = []
    for mod in sorted(all_third_party):
        # internal submodule — keep it, PyInstaller needs it even if find_spec fails
        top = mod.split(".")[0]
        if "." in mod and (top in internal_packages or top in internal_modules):
            verified_hidden.append(mod)
            continue
        try:
            spec = importlib.util.find_spec(mod)
        except (ModuleNotFoundError, ImportError):
            spec = None
        if spec is not None:
            verified_hidden.append(mod)
        else:
            logger.info(f"{C.CYAN}Module {mod} not found, skipped{C.RESET}")

    # All modules are added as precise --hidden-import (no --collect-submodules).
    # Using individual submodule paths (e.g. "sqlalchemy.orm" instead of "sqlalchemy")
    # avoids importing entire packages wholesale, keeping the build lean.
    hidden = verified_hidden
    collect = []

    logger.info(f"{C.YELLOW}Auto-detected {len(hidden)} hidden-import modules: {hidden}{C.RESET}")

    return hidden, collect


def start_pyinstaller_pack(
    encrypted_dir,
    main_entry,
    hidden_imports=None,
    collect_submodules=None,
    dist_name=None,
):
    """
    Package the Nuitka-encrypted project with PyInstaller

    Args:
        encrypted_dir: encrypted project directory
        main_entry: main entry file (relative to encrypted_dir, e.g. "main.py")
        hidden_imports: list of third-party modules for --hidden-import
        collect_submodules: list of packages for --collect-submodules
        dist_name: output directory name (defaults to project name)

    Returns:
        dist_dir: PyInstaller output directory
    """
    encrypted_dir = os.path.abspath(encrypted_dir)
    if not os.path.isdir(encrypted_dir):
        raise ValueError(f"encrypted_dir must be a directory: {encrypted_dir}")

    main_entry_path = os.path.join(encrypted_dir, main_entry)
    if not os.path.exists(main_entry_path):
        raise ValueError(f"main_entry not found: {main_entry_path}")

    if dist_name is None:
        dist_name = os.path.basename(encrypted_dir)
    else:
        dist_name = os.path.basename(dist_name.strip("/\\"))

    # auto-detect dependencies (if not explicitly provided by user)
    if hidden_imports is None or collect_submodules is None:
        auto_hidden, auto_collect = auto_detect_dependencies(encrypted_dir)
        if hidden_imports is None:
            hidden_imports = auto_hidden
        if collect_submodules is None:
            collect_submodules = auto_collect

    hidden_imports = hidden_imports or []
    collect_submodules = collect_submodules or []

    # find all compiled module files (.pyd on Windows, .so on Linux/macOS),
    # excluding dist/build directories
    pyd_files = []
    for root, dirs, files in os.walk(encrypted_dir):
        rel = os.path.relpath(root, encrypted_dir)
        if rel == ".":
            pass  # do not skip root directory
        elif rel.startswith("dist") or rel.startswith("build") or rel.startswith("."):
            continue
        for f in files:
            if f.endswith(".pyd") or f.endswith(".so"):
                pyd_files.append(os.path.join(root, f))

    logger.info(f"{C.CYAN}Found {len(pyd_files)} .pyd/.so files{C.RESET}")

    # find all __init__.py files
    init_files = []
    for root, dirs, files in os.walk(encrypted_dir):
        rel = os.path.relpath(root, encrypted_dir)
        if rel == ".":
            pass  # do not skip root directory
        elif rel.startswith("dist") or rel.startswith("build") or rel.startswith("."):
            continue
        for f in files:
            if f == "__init__.py":
                init_files.append(os.path.join(root, f))

    logger.info(f"{C.CYAN}Found {len(init_files)} __init__.py files{C.RESET}")

    # clean up old build artifacts
    for d in ["dist", "build"]:
        p = os.path.join(encrypted_dir, d)
        if os.path.exists(p):
            shutil.rmtree(p, onerror=lambda fn, p, e: None)

    spec_file = os.path.join(encrypted_dir, f"{dist_name}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Build PyInstaller command
    # Use sys.executable to ensure PyInstaller runs on the SAME Python as Nuitka.
    # Mixing interpreters (e.g. .pyd built with 3.11, pyinstaller from 3.14 in PATH)
    # causes "Module use of pythonXXX.dll conflicts with this version of Python".
    cmd = [sys.executable, "-m", "PyInstaller", "--onedir", "--name", dist_name]

    # Note: --add-binary for .pyd/.so files and --add-data for __init__.py files are
    # intentionally omitted. PyInstaller's modulegraph analysis automatically discovers
    # these files through the main entry's import chain. Adding them explicitly bloats
    # the command line beyond Windows' 8191-character limit (gitee.com issue #1).

    # add hidden imports
    for hi in hidden_imports:
        cmd.append(f"--hidden-import={hi}")

    # add collect submodules (only when manually specified via CLI/config;
    # auto-detection uses precise --hidden-import with submodule paths instead)
    for pkg in collect_submodules:
        cmd.append(f"--collect-submodules={pkg}")

    # add main entry file
    cmd.append(main_entry)

    logger.info("PyInstaller command: %s", " ".join(cmd))

    original_cwd = os.getcwd()
    os.chdir(encrypted_dir)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            error_msg = result.stderr[-2000:] if result.stderr else result.stdout[-2000:]
            raise Exception(f"PyInstaller packaging failed:\n{error_msg}")
        logger.info(f"{C.GREEN}PyInstaller packaging succeeded, output: {os.path.join(encrypted_dir, 'dist', dist_name)}{C.RESET}")
    finally:
        os.chdir(original_cwd)

    return os.path.join(encrypted_dir, "dist", dist_name)


def start_full_workflow(
    input_file_path,
    output_file_path=None,
    ignore_files=None,
    except_main_file=1,
    force_encrypt_files=None,
    main_entry=None,
    hidden_imports=None,
    collect_submodules=None,
    dist_name=None,
):
    """
    Full workflow: Nuitka Encryption + PyInstaller Packaging

    Args:
        input_file_path: path to the project to encrypt
        output_file_path: encryption output path (also PyInstaller input path)
        ignore_files: list of files to ignore
        except_main_file: whether to filter out files containing __main__
        force_encrypt_files: list of filenames to force encrypt even if they contain __main__
        main_entry: PyInstaller main entry file (relative to encrypted output dir)
        hidden_imports: list of PyInstaller --hidden-import modules
        collect_submodules: list of PyInstaller --collect-submodules packages
        dist_name: PyInstaller output directory name

    Returns:
        dist_dir: PyInstaller output directory
    """
    # Step 1: Nuitka Encryption
    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")
    logger.info(f"{C.CYAN}Step 1: Nuitka Encryption{C.RESET}")
    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")
    encrypted_dir = start_encrypt(
        input_file_path=input_file_path,
        output_file_path=output_file_path,
        ignore_files=ignore_files,
        except_main_file=except_main_file,
        force_encrypt_files=force_encrypt_files,
    )

    # if main_entry not specified, try common main entry filenames
    if main_entry is None:
        candidates = ["main.py", "app.py", "run.py", "aether.py", "cli.py", "server.py"]
        for candidate in candidates:
            candidate_path = os.path.join(encrypted_dir, candidate)
            if os.path.exists(candidate_path):
                main_entry = candidate
                break

    if main_entry is None:
        logger.warning("Main entry file not found, skipping PyInstaller packaging")
        logger.warning("Please specify main_entry parameter, or place a main entry file in the encrypted output directory")
        return encrypted_dir

    # Step 2: PyInstaller Packaging
    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")
    logger.info(f"{C.CYAN}Step 2: PyInstaller Packaging{C.RESET}")
    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")
    dist_dir = start_pyinstaller_pack(
        encrypted_dir=encrypted_dir,
        main_entry=main_entry,
        hidden_imports=hidden_imports,
        collect_submodules=collect_submodules,
        dist_name=dist_name,
    )

    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")
    logger.info(f"{C.ORANGE}Full workflow completed!{C.RESET}")
    logger.info(f"{C.CYAN}Encrypted output: {encrypted_dir}{C.RESET}")
    logger.info(f"{C.CYAN}Packaged output: {dist_dir}{C.RESET}")
    logger.info(f"{C.GRAY}{'=' * 60}{C.RESET}")

    return dist_dir