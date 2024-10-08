#!/usr/bin/env pythonrunscript
# ```conda_install_specs.txt
# python=3.10
# ffmpeg
# ```

# if pythonrunscript works properly,
# then ffmpeg should be run properly
#
# this shows pythonrunscript is not only running scripts with the python
# interpreter associated with the ad-hoc conda environment, but that it
# is reproducing the PATH variable and other parts of the environment,
# which is needed to allow the full benefit of conda deps.

import os, logging, sys
from typing import NoReturn

print("top-line")
sys.stdout.flush()

if __name__ == "__main__":
    print("main: ENTRY")
    print(f"{sys.argv=}")
    cmd = sys.argv
    cmd[0] = "ffmpeg"
    print(f"{cmd=}")
    sys.stdout.flush()
    os.execvp(cmd[0],cmd)

    
