import pytest, os, tempfile, textwrap, tomlkit  # noqa: E401
from pythonrunscript.pythonrunscript import parse_dependencies, parse_script_toml, tomlconfig_to_pip_conda

from typing import NamedTuple

class Expected(NamedTuple):
    reqs: str
    cis: str
    envyml: str

tests: list[tuple[str, Expected]] = [
    ## requirements, 1-line
    (
    """
    # ```requirements.txt
    # requests==2.26.0
    # ```
    """,
        Expected(
        reqs="""
        requests==2.26.0
        """,
        cis="",
        envyml="")
     ),
    ## conda_install_sepcs, 1-line
    (
    """
    # ```conda_install_specs.txt
    # requests==2.27.0
    # ```
    """,
        Expected(
        reqs="""
        """,
        cis="""
        requests==2.27.0
        """,
        envyml="")
     ),
    ## one-line requirements
    (
    """
    # ```requirements.txt
    # requests==2.26.0
    # ```
    # 
    # ```conda_install_specs.txt
    # python=<3.11
    # ```
    """,
        Expected(
        reqs="""
        requests==2.26.0
        """,
        cis="python=<3.11\n",
        envyml="")
     ),
    ## 2-line conda
    (
    """
    # ```conda_install_specs.txt
    # python=3.11
    # nbclassic
    # ```
    """,
        Expected(
        reqs="",
        cis="""
        python=3.11
        nbclassic
        """,
        envyml="")
     ),
]
def f(s):
    return textwrap.dedent(s).lstrip()
tests = [(f(a),(f(b),f(c),f(d))) for (a,(b,c,d)) in tests] # type: ignore
del f

@pytest.mark.parametrize("test_index", list(range(len(tests))))
def test_parse_dependencies_basic(test_index:int):
    to_run = tests[test_index:test_index+1]
    print(f"{to_run=}")
    for (input,(expected_pip_val,expected_conda_specs,expected_conda_env)) in to_run:
        (_, out_pip, out_conda_env, out_conda_specs) = (None,None,None,None)
        p = os.path.join( tempfile.gettempdir(), "test_script.py" )    
        with open(p, 'w') as f:
            f.write(input)
        try:
            # Call the function
            result = parse_dependencies(p)
            
            # Assert the expected results
            assert isinstance(result, tuple)
            assert len(result) == 4
            (_, out_pip, out_conda_env, out_conda_specs) = result
            assert out_pip == expected_pip_val
            assert out_conda_env == expected_conda_env
            assert out_conda_specs == expected_conda_specs
        finally:
            # Clean up the temporary file
            os.remove(p)

toml_inputs:list[str] = [
"""
requires-python = ">=3.11"
dependencies = ["requests<3", "rich", ]
""",
"""
requires-python = ">=3.11"
dependencies = [
  "requests<3",
  "rich",
]
""",
"""
requires-python = ">=3.11"
dependencies = [
  "requests<3", #comment
  # comment
"rich",
]
""",
]

@pytest.mark.parametrize("toml_test_index", list(range(len(toml_inputs))))
def test_parse_toml(toml_test_index):
    s = toml_inputs[toml_test_index]
    (out_pip,out_conda) = parse_script_toml(s)

    # test if we're parsing like tomlkit
    config = tomlkit.parse(s)
    (kit_pip_deps,kit_conda_python_spec) = tomlconfig_to_pip_conda(config)
    assert kit_pip_deps == out_pip
    assert kit_conda_python_spec == out_conda

    exp_conda_specs = "python>=3.11"
    exp_pip = """requests<3
rich
"""
    assert exp_pip == out_pip, "unexpected requirements generated from script TOML"
    assert exp_conda_specs == out_conda, "unexpected conda install specs generated from script TOML"
