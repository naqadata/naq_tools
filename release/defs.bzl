"""Module for defining release rules for Python zip applications."""

load("@rules_python//python:defs.bzl", "py_binary")
load("@pypi//:requirements.bzl", "requirement")


def naq_release(name, app_target):
    """Creates filegroup and genrule targets for packaging a Python application as a zip executable.

    Args:
      name: The base name for the generated targets.
      app_target: The Bazel target of the Python application to package.
    """

    filegroup_name = name + "-src"
    release_name = name + "-pyzip"
    install_name = name + ".install"

    native.filegroup(
        name = filegroup_name,
        srcs = [app_target],
        output_group = "python_zip_file",
    )

    native.genrule(
        name = release_name,
        srcs = [":" + filegroup_name],
        outs = [name],
        cmd = "echo '#!/usr/bin/env python3' > $@ && cat $(location :" + filegroup_name + ") >> $@ && chmod +x $@",
    )
    
    py_binary(
        name = install_name,
        srcs = [":install.py"],
        main = "install.py",
        data = [app_target],
        deps = [requirement("bazel-runfiles")],
        args = ["$(location " + app_target + ")"],
    )