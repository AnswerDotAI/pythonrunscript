#!/usr/bin/env python3
import os, logging, sys
from typing import NoReturn

# The purpose of this script
# is to verify how to call an executable in a specified conda env
#
# conda run seems to have a bug, where it grabs arguments intended to be arguments for the executable
#
# findings:
# - `./run_conda.py test ffmpeg -version`:
#   - fails, because conda tries to parse -version rather than letting fmpeg use it
#   - this is a known bug: https://github.com/conda/conda/issues/13639
#   - workaround: auto-generate an exec script with the args, and call that from conda???
# - `./run_conda.py test ffmpeg --version`:
#   - works, because
# - ./run_conda test ffmpeg --help:
#   - works
# 
def conda_run_script(interpreter, script, args,conda_env_dir) -> NoReturn:
    logging.info(
        f"using conda run to run {script} using {interpreter} with args: {args}"
    )
    sys.stdout.flush()
    logging.info(f'os.execvp({interpreter}, [{interpreter},{script}] + {args})')
    cmd = ["conda","run","--name",conda_env_dir,interpreter,script] + args
    print(f"os.execvp: {cmd=}")
    sys.stdout.flush()
    os.execvp(cmd[0],cmd)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"usage: {sys.argv[0]} conda_env_path executable_path executable_args...")
        sys.exit(1)
    print(f"{sys.argv=}")
    conda_run_script(interpreter=sys.argv[2],
                     script=sys.argv[3],
                     args=sys.argv[4:],
                     conda_env_dir=sys.argv[1])
