load("@pypi//:requirements.bzl", "requirement")

def naq_py_binary(name, deps, **kwargs):
    """A thin wrapper around py_binary to include common dependencies."""
    
    deps = (deps or []) + [
        requirement("zipapp"),
    ]

    # standard py_binary target
    native.py_binary(
        name = name,
        **kwargs,
    )

    # zipapp target
    native.genrule(
        name = name + ".zipapp",
        srcs = [":" + name],
        outs = [name + ".pyz"],
        toolchains=["@rules_python//python:current_py_toolchain"],
        cmd = "$(PYTHON3) -m zipapp --output $(OUTS) --python '/usr/bin/env python' $(SRCS)",
    )

