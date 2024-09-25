#!/usr/bin/env pythonrunscript
# ```conda_install_specs.txt
# python=3.10
# ffmpeg
# ```

# if pythonrunscript works properly,
# then it should be possible to run
# an interactive executable such
# as python itself, from a script,
# as usual

import os, logging, sys
from typing import NoReturn

print("top-line")
sys.stdout.flush()

if __name__ == "__main__":
    print("main: ENTRY")
    print(f"{sys.argv=}")
    cmd = sys.argv
    cmd[0] = "python3"
    print(f"{cmd=}")
    sys.stdout.flush()
    os.execvp(cmd[0],cmd)

    
