import pytest
import os, tempfile
from pythonrunscript.pythonrunscript import parse_dependencies

def test_parse_dependencies_basic():
    # Create a temporary file with some test content
    test_content = """
    # ```requirements.txt
    # requests==2.26.0
    # ```
    
    print("Hello, world!")
    """
    p = os.path.join( tempfile.gettempdir(), "test_script.py" )    
    with open(p, 'w') as f:
        f.write(test_content)
    
    try:
        # Call the function
        result = parse_dependencies(p)
        
        # Assert the expected results
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert result[1] == "requests==2.26.0\n".strip()  # pip requirements
        assert result[2] == ""  # conda env
        assert result[3] == ""  # conda specs
    finally:
        # Clean up the temporary file
        os.remove(p)
