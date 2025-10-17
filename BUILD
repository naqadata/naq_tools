# Make requirements.txt addressable as //:requirements.txt
exports_files(["requirements.txt", "setup.py"])
load("@python_versions//3.12:defs.bzl", compile_pip_requirements_3_12 = "compile_pip_requirements")

compile_pip_requirements_3_12(
    name = "requirements_3_12",
    timeout = "moderate",
    src = "requirements.txt",
    requirements_txt = "requirements_lock_3_12.txt",
)