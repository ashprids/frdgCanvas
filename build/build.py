print("""
# frdgCanvas Cross-Platform build script
# Made by fridge (https://fridg3.org)
# Created on 12/07/2024, currently supports any Windows and Unix (MacOS/Linux) systems.
      
# This script should be in the 'build' directory, and the main script should be in the parent directory.

Please make sure you have all the necessary dependencies installed before installing!
If you're using a virtual environment, place it in the directory above where this script is.\n""")

import os, fnmatch, sys

# Find an OS-appropriate solution for immediate input
def get_key():
    try:
        # Windows
        import msvcrt
        return msvcrt.getch().decode().lower()
    except ImportError:
        # Unix
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# build.spec requires a pathex to be specified if a virtual environment is in use.
# This function checks for the presence of a virtual environment, and finds where site-packages should be based on OS.
def get_pathex():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dirs = [d for d in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, d))]
    env_dirs = fnmatch.filter(dirs, '*env*')
    
    if env_dirs:
        venv = env_dirs[0]
        print(f"Found a virtual environment in '{venv}'")
    else:
        print("No 'env' directories found, defaulting to system-wide environment.")
        return "."

    # Check the OS and return the appropriate pathex directory
    if os.name == 'nt':
        return os.path.join("..", venv, "Lib", "site-packages")
    else:
        return os.path.join("..", venv, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")


if __name__ == "__main__":
    build_dir = os.path.join('build')
    if os.getcwd() != build_dir:
        print(f"Changing the current working directory to /{build_dir}")
        os.chdir(build_dir)

    pathex = get_pathex()
    print(f"Pathex directory decided: {pathex}")
    with open("build.spec", "w") as f:
        f.write(f"# -*- mode: python ; coding: utf-8 -*-\n\n")
        f.write(f"\n")
        f.write(f"a = Analysis(\n")
        f.write(f"    ['../main.py'],\n")
        f.write(f"    pathex=['{pathex}'],\n")
        f.write(f"    binaries=[],\n")
        f.write(f"    datas=[('../gtk/*', 'gtk'),('../assets/*', 'assets')],\n")
        f.write(f"    hiddenimports=[],\n")
        f.write(f"    hookspath=[],\n")
        f.write(f"    hooksconfig={{}},\n")
        f.write(f"    runtime_hooks=[],\n")
        f.write(f"    excludes=[],\n")
        f.write(f"    noarchive=False,\n")
        f.write(f"    optimize=0,\n")
        f.write(f")\n\n")
        f.write(f"pyz = PYZ(a.pure)\n")
        f.write(f"\n")
        f.write(f"exe = EXE(\n")
        f.write(f"    pyz,\n")
        f.write(f"    a.scripts,\n")
        f.write(f"    a.binaries,\n")
        f.write(f"    a.datas,\n")
        f.write(f"    [],\n")
        f.write(f"    name='frdgCanvas',\n")
        f.write(f"    debug=False,\n")
        f.write(f"    bootloader_ignore_signals=False,\n")
        f.write(f"    strip=False,\n")
        f.write(f"    upx=True,\n")
        f.write(f"    upx_exclude=[],\n")
        f.write(f"    runtime_tmpdir=None,\n")
        f.write(f"    console=False,\n")
        f.write(f"    disable_windowed_traceback=False,\n")
        f.write(f"    argv_emulation=False,\n")
        f.write(f"    target_arch=None,\n")
        f.write(f"    codesign_identity=None,\n")
        f.write(f"    entitlements_file=None,\n")
        f.write(f"    icon=['../assets/icon.ico'],\n")
        f.write(f")\n")
    print("build.spec written successfully.")
    print("\nWould you like to build the executable now? (y/n): ", end='', flush=True)

    choice = get_key()
    if choice == "y":
        print("Building...")
        os.system("pyinstaller build.spec")
        print("\nProcess finished.\nExecutable in 'dist' directory.")
        exit(0)
    else:
        print("Process finished.\nYou can rerun this script or run 'pyinstaller build.spec' to build the executable at any time.")
        exit(0)
