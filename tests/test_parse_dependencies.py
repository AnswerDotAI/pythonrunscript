import os, tempfile, textwrap  # noqa: E401
from pythonrunscript.pythonrunscript import parse_dependencies

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
        cis="python=<3.11",
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
    return textwrap.dedent(s).strip()
tests = [(f(a),(f(b),f(c),f(d))) for (a,(b,c,d)) in tests] # type: ignore
del f

def test_parse_dependencies_basic():
    for (input,(expected_pip_val,expected_conda_specs,expected_conda_env)) in tests:
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
