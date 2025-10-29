# file: pytest_wrapper.bzl
load("@rules_python//python:defs.bzl", "py_test")
load("@pypi//:requirements.bzl", "requirement")

def pytest_test(
        name,
        test,                 # Label to a .py file to run with pytest (e.g. ":test_example.py")
        args = None,          # Extra args to pass to pytest (list of strings)
        deps = None,          # Extra python deps your test needs
        data = None,          # Extra runtime data files
        srcs = None,          # Extra source files for the test (rarely needed)
        **kwargs):
    """
    Wrap a single Python file and run it via pytest.

    Example usage (in BUILD):
        load("//:pytest_wrapper.bzl", "pytest_file_test")
        load("@rules_python//python:pip.bzl", "requirement")

        pytest_file_test(
            name = "my_pytest",
            test = ":test_example.py",
            args = ["-q"],  # optional
        )

    Notes:
    - `pytest_dep` should be a label that provides pytest on PYTHONPATH, e.g. requirement("pytest").
    - Your test file should be a py module that pytest can collect.
    """
    args = args or []
    deps = deps or []
    data = data or []
    srcs = srcs or []

    runner = name + "_runner.py"

    native.genrule(
        name = name + "_runner_gen",
        outs = [runner],
        # Minimal runner: forwards all argv to pytest.main(...)
        cmd = """cat > $@ <<'PY'
import sys
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:]))
PY
""",
    )

    # Ensure the test file is available at runtime and resolvable via $(location ...)
    full_args = list(args) + ["$(location %s)" % test]

    py_test(
        name = name,
        srcs = [runner] + srcs,
        main = runner,
        deps = deps + [
            requirement("pytest")
        ],
        args = full_args,
        data = [test] + data,
        **kwargs
    )
