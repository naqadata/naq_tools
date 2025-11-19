load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")

def naq_py_binary(name, deps, **kwargs):
    """A thin wrapper around py_binary to include common dependencies."""

    deps = (deps or []) + [
        requirement("zipapp"),
    ]

    # standard py_binary target
    py_binary(
        name = name,
        **kwargs
    )

    # zipapp target
    native.genrule(
        name = name + ".zipapp",
        srcs = [":" + name],
        outs = [name + ".pyz"],
        toolchains = ["@rules_python//python:current_py_toolchain"],
        cmd = "$(PYTHON3) -m zipapp --output $(OUTS) --python '/usr/bin/env python' $(SRCS)",
    )

def naq_release(name, app_target):
    """Creates filegroup and genrule targets for packaging a Python application and installing it

    Args:
      name: The base name for the generated targets.
      app_target: The Bazel target of the Python application to package.
    """
    install_name = name + ".install"

    py_binary(
        name = install_name,
        srcs = [":install.py"],
        main = "install.py",
        data = [app_target],
        deps = [requirement("bazel-runfiles")],
        args = ["$(location " + app_target + ")"],
        tags = ["manual"],
    )
