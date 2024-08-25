import os, tempfile, textwrap
import pytest
from pythonrunscript.pythonrunscript import parse_dependencies


tests: list[tuple[str, tuple[str, str, str]]] = [
    (
    """
    # ```requirements.txt
    # requests==2.26.0
    # ```
    """,
        (
        """
        requests==2.26.0
        """,
        "",
        "")
     ),
]
f = lambda s:(textwrap.dedent(s)).strip()
tests = [(f(a),(f(b),f(c),f(d))) for (a,(b,c,d)) in tests]
del f

def test_parse_dependencies_basic():
    for (input,(expected_pip_val,expected_conda_env,expected_conda_specs)) in tests:
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
