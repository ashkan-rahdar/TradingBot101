from Cython.Build import cythonize
from setuptools import Extension
import shutil
import subprocess
from pathlib import Path

# === PATH CONFIG ===
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR
MAIN_SCRIPT = SRC_DIR / "main_backend.py"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# === STEP 1: Cythonize all .py files ===
def cythonize_all():
    print("[*] Cythonizing all modules via setuptools...")

    py_files = list(SRC_DIR.rglob("*.py"))
    modules = []

    for path in py_files:
        if path.name == "build.py":
            continue

        # Build proper module name: from "D:/Trade/Bot/TradingBot101/classes/DP_Parameteres.py"
        # to "classes.DP_Parameteres"
        relative = path.relative_to(SRC_DIR)
        module_name = ".".join(relative.with_suffix("").parts)

        modules.append(Extension(module_name, [str(path)]))

    cythonize(
        modules,
        compiler_directives={'language_level': 3},
        build_dir="build",
        annotate=False
    )


# === STEP 2: Obfuscate (optional) ===
def obfuscate_main():
    print("[*] Obfuscating entry point with PyArmor...")
    subprocess.run([
        "pyarmor", "obfuscate", str(MAIN_SCRIPT)
    ], check=True)

# === STEP 3: Build executable ===
def build_executable():
    print("[*] Building .exe with PyInstaller...")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    subprocess.run([
        "pyinstaller",
        "--onefile",
        # "--noconsole",
        "--name=TradingBotSecure",
        str(MAIN_SCRIPT)
    ], check=True)

# === BUILD PIPELINE ===
if __name__ == "__main__":
    cythonize_all()
    obfuscate_main()
    build_executable()
    print("\n[+] Build complete. Check dist/TradingBotSecure.exe")
