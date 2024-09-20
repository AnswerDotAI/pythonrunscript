#!/Users/alexis/workspace/answerai/pythonrunscript/pythonrunscript/pythonrunscript.py
# ```conda_install_specs.txt
# python=3.10
# ffmpeg
# ```

# if pythonrunscript works properly,
# then ffmpeg should be run properly

import os, logging, sys
from typing import NoReturn

print("top-line")

if __name__ == "__main__":
    print("main: ENTRY")
    cmd = ["ffmpeg","-version"]
    print(f"{cmd=}")
    os.execvp(cmd[0],cmd)

    
