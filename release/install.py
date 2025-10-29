#!/usr/bin/env python3
import argparse
import shutil
from runfiles import runfiles
from pathlib import Path
import subprocess

INSTALL_DIR = Path("/usr/local/bin/")

parser = argparse.ArgumentParser(description="Install given target and runfiles")
parser.add_argument("target", help="The target to install")
args = parser.parse_args()

target_path = Path(args.target).resolve()
print(args.target)
print(target_path)

r = runfiles.Create()
target_exec_path = Path(r.Rlocation(target_path.as_posix()))
target_runfiles_path = Path(f"{target_exec_path}.runfiles")

assert target_exec_path.exists(), f"Target executable not found: {target_exec_path}"
assert target_runfiles_path.exists(), f"Target runfiles not found: {target_runfiles_path}"

print(f"Installing target:")
print(f"  Executable: {target_exec_path}")
print(f"  Runfiles:   {target_runfiles_path}")

install_exec_path = INSTALL_DIR / target_exec_path.name
install_runfiles_path = INSTALL_DIR / target_runfiles_path.name

# if install_exec_path.exists():
#     print(f"Removing existing installation at {install_exec_path}")
#     subprocess.run(["sudo", "rm", "-rf", str(install_exec_path)], check=True)
#     if install_runfiles_path.exists():
#         subprocess.run(["sudo", "rm", "-rf", str(install_runfiles_path)], check=True)

subprocess.run(["sudo", "cp", str(target_exec_path), str(install_exec_path)], check=True)
subprocess.run(["sudo", "rsync", "-rLptD", str(target_runfiles_path), str(install_runfiles_path)], check=True)

print(f"Installed {target_path.name} to {install_exec_path}")