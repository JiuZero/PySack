import os
import sys
import getopt
import configparser

from pysack.pysack import start_encrypt, start_pyinstaller_pack, start_full_workflow


def usage():
    """
Usage:
    pysack encrypt [options]          Encrypt Python source code (default)
    pysack pack -i <dir> -m <file>    Pack encrypted project with PyInstaller
    pysack full [options]             Encrypt + Pack in one workflow
    pysack build                      Use .pysack.cfg config file in current directory

Options:
    -i, --input <path>        File or directory to encrypt (required)
    -o, --output <path>       Output directory (default: <input>/dist)
    -I, --ignore <list>       Files/directories to skip, comma-separated
    -e, --except-main <0|1>   Skip files containing __main__ (default: 1)
    -c, --config <path>       Config file path, overrides other arguments

    -m, --main <file>         Main entry file (required for pack/full)
    -n, --name <name>         Output dist directory name (default: project name)
    --force-encrypt <list>    Force encrypt files containing __main__, comma-separated
    --hidden-imports <list>   Extra modules for PyInstaller --hidden-import, comma-separated
    --collect-submodules <list>  Extra packages for --collect-submodules, comma-separated

    -h, --help                Show this help message
    """
    sys.exit()


def load_config(config_path):
    """Load parameters from config file"""
    config = configparser.ConfigParser()
    config.read(config_path)
    # .pysack.cfg
    # [pysack]
    # paths = package_a
    # ignores = setup.py
    # build_dir = build
    # main_py = main.py
    # dist_name = MyApp
    # force_encrypt_files = llm_client.py, tool_manager.py
    # except_main_file = 1
    #
    # [pyinstaller]
    # hidden_imports = httptools, watchfiles, psutil, requests
    # collect_submodules = uvicorn, fastapi, sqlalchemy, numpy
    # main_entry = main.py
    # dist_name = MyApp
    params = {}
    if 'pysack' in config:
        params['input_file_path'] = config['pysack'].get('paths', '')
        params['output_file_path'] = config['pysack'].get('build_dir', '')
        params['ignore_files'] = config['pysack'].get('ignores', '').split(',')
        params['except_main_file'] = config['pysack'].getint('except_main_file', 1)
        force_encrypt = config['pysack'].get('force_encrypt_files', '')
        if force_encrypt:
            params['force_encrypt_files'] = [f.strip() for f in force_encrypt.split(',') if f.strip()]
        params['dist_name'] = config['pysack'].get('dist_name', '')

    if 'pyinstaller' in config:
        hi = config['pyinstaller'].get('hidden_imports', '')
        if hi:
            params['hidden_imports'] = [m.strip() for m in hi.split(',') if m.strip()]
        cs = config['pyinstaller'].get('collect_submodules', '')
        if cs:
            params['collect_submodules'] = [p.strip() for p in cs.split(',') if p.strip()]
        params['main_entry'] = config['pyinstaller'].get('main_entry', '')
        if not params.get('dist_name'):
            params['dist_name'] = config['pyinstaller'].get('dist_name', '')

    return params


def execute():
    try:
        # Detect subcommand
        subcommand = "encrypt"  # default
        args_start = 1
        if len(sys.argv) > 1:
            if sys.argv[1] in ("encrypt", "pack", "full", "build"):
                subcommand = sys.argv[1]
                args_start = 2

        if subcommand == "build":
            # Auto-use .pysack.cfg in current directory
            current_dir = os.getcwd()
            config_path = os.path.join(current_dir, ".pysack.cfg")
            if not os.path.exists(config_path):
                print(f"Config file not found: {config_path}")
                sys.exit(1)

            config_params = load_config(config_path)
            input_file_path = config_params.get('input_file_path', '')
            output_file_path = config_params.get('output_file_path', '')
            ignore_files = config_params.get('ignore_files', [])
            except_main_file = config_params.get('except_main_file', 1)
            force_encrypt_files = config_params.get('force_encrypt_files', None)
            hidden_imports = config_params.get('hidden_imports', None)
            collect_submodules = config_params.get('collect_submodules', None)
            main_entry = config_params.get('main_entry', None)
            dist_name = config_params.get('dist_name', None)

            start_full_workflow(
                input_file_path=input_file_path,
                output_file_path=output_file_path,
                ignore_files=ignore_files,
                except_main_file=except_main_file,
                force_encrypt_files=force_encrypt_files,
                main_entry=main_entry,
                hidden_imports=hidden_imports,
                collect_submodules=collect_submodules,
                dist_name=dist_name,
            )
            sys.exit(0)

        if subcommand == "pack":
            # pack: PyInstaller packaging for an already encrypted project
            # Usage: pysack pack -i <encrypted_dir> -m <main_entry> [options]
            options, args = getopt.getopt(
                sys.argv[args_start:],
                "hi:m:n:",
                [
                    "help",
                    "input=",
                    "main=",
                    "hidden-imports=",
                    "collect-submodules=",
                    "name=",
                ],
            )
            encrypted_dir = ""
            main_entry = ""
            hidden_imports = None
            collect_submodules = None
            dist_name = ""

            for name, value in options:
                if name in ("-h", "--help"):
                    print(usage.__doc__)
                    sys.exit()
                elif name in ("-i", "--input"):
                    encrypted_dir = value
                elif name in ("-m", "--main"):
                    main_entry = value
                elif name == "--hidden-imports":
                    hidden_imports = [m.strip() for m in value.split(",") if m.strip()]
                elif name == "--collect-submodules":
                    collect_submodules = [p.strip() for p in value.split(",") if p.strip()]
                elif name in ("-n", "--name"):
                    dist_name = value

            if not encrypted_dir:
                print("pack requires -i or --input (encrypted project directory)")
                sys.exit(1)
            if not main_entry:
                print("pack requires -m or --main (main entry file, e.g. main.py)")
                sys.exit(1)

            start_pyinstaller_pack(
                encrypted_dir=encrypted_dir,
                main_entry=main_entry,
                hidden_imports=hidden_imports,
                collect_submodules=collect_submodules,
                dist_name=dist_name or None,
            )
            sys.exit(0)

        if subcommand == "full":
            # full: Encrypt + Pack complete workflow
            options, args = getopt.getopt(
                sys.argv[args_start:],
                "hi:o:I:e:c:m:n:",
                [
                    "help",
                    "input=",
                    "output=",
                    "ignore=",
                    "except-main=",
                    "config=",
                    "main=",
                    "hidden-imports=",
                    "collect-submodules=",
                    "name=",
                    "force-encrypt=",
                ],
            )
            input_file_path = output_file_path = ignore_files = ""
            except_main_file = 1
            config_path = ""
            main_entry = ""
            hidden_imports = None
            collect_submodules = None
            dist_name = ""
            force_encrypt_files = []

            # Check for config file first
            for name, value in options:
                if name in ("-c", "--config"):
                    config_path = value
                    break

            if config_path:
                config_params = load_config(config_path)
                input_file_path = config_params.get('input_file_path', '')
                output_file_path = config_params.get('output_file_path', '')
                ignore_files = config_params.get('ignore_files', [])
                except_main_file = config_params.get('except_main_file', 1)
                force_encrypt_files = config_params.get('force_encrypt_files', [])
                hidden_imports = config_params.get('hidden_imports', None)
                collect_submodules = config_params.get('collect_submodules', None)
                main_entry = config_params.get('main_entry', '')
                dist_name = config_params.get('dist_name', '')
            else:
                for name, value in options:
                    if name in ("-h", "--help"):
                        print(usage.__doc__)
                        sys.exit()
                    elif name in ("-i", "--input"):
                        input_file_path = value
                    elif name in ("-o", "--output"):
                        output_file_path = value
                    elif name in ("-I", "--ignore"):
                        ignore_files = value.split(",")
                    elif name in ("-e", "--except-main"):
                        except_main_file = int(value)
                    elif name in ("-m", "--main"):
                        main_entry = value
                    elif name == "--hidden-imports":
                        hidden_imports = [m.strip() for m in value.split(",") if m.strip()]
                    elif name == "--collect-submodules":
                        collect_submodules = [p.strip() for p in value.split(",") if p.strip()]
                    elif name in ("-n", "--name"):
                        dist_name = value
                    elif name == "--force-encrypt":
                        force_encrypt_files = [f.strip() for f in value.split(",") if f.strip()]

                if not input_file_path:
                    print("full requires -i or --input")
                    sys.exit(1)

            start_full_workflow(
                input_file_path=input_file_path,
                output_file_path=output_file_path or None,
                ignore_files=ignore_files or None,
                except_main_file=except_main_file,
                force_encrypt_files=force_encrypt_files or None,
                main_entry=main_entry or None,
                hidden_imports=hidden_imports or None,
                collect_submodules=collect_submodules or None,
                dist_name=dist_name or None,
            )
            sys.exit(0)

        # Default encrypt subcommand (original logic)
        options, args = getopt.getopt(
            sys.argv[args_start:],
            "hi:o:I:e:c:",
            [
                "help",
                "input=",
                "output=",
                "ignore=",
                "except-main=",
                "config=",
            ],
        )
        input_file_path = output_file_path = ignore_files = ""
        except_main_file = 1
        config_path = ""

        # Check for config file first
        for name, value in options:
            if name in ("-c", "--config"):
                config_path = value
                break

        if config_path:
            config_params = load_config(config_path)
            input_file_path = config_params.get('input_file_path', '')
            output_file_path = config_params.get('output_file_path', '')
            ignore_files = config_params.get('ignore_files', [])
            except_main_file = config_params.get('except_main_file', 1)
            force_encrypt_files = config_params.get('force_encrypt_files', None)
        else:
            force_encrypt_files = None
            for name, value in options:
                if name in ("-h", "--help"):
                    print(usage.__doc__)
                    sys.exit()

                elif name in ("-i", "--input"):
                    input_file_path = value

                elif name in ("-o", "--output"):
                    output_file_path = value

                elif name in ("-I", "--ignore"):
                    ignore_files = value.split(",")

                elif name in ("-e", "--except-main"):
                    except_main_file = int(value)

            if not input_file_path:
                print("Requires -i or --input, or use -c/--config to pass a config file")
                print(usage.__doc__)
                sys.exit()

        start_encrypt(input_file_path, output_file_path, ignore_files, except_main_file, force_encrypt_files)

    except getopt.GetoptError:
        print(usage.__doc__)
        sys.exit()


if __name__ == "__main__":
    execute()