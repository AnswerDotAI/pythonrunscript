#!/usr/bin/env python3
import subprocess,os,shutil

def run_with_logging(command:str,out_f,err_f,verbosity:str):
    '''
    Runs command. Logs and maybe streams stdout and stderr.
    '''
    assert (verbosity in {'silent','errors','verbose'}), "unexpected verbosity"
    if verbosity == 'silent':
        command += f' 2> "{err_f}"'
        command += f' 1> "{out_f}"'
    elif verbosity == 'errors':
        command += f' 2> >(tee "{err_f}")'
        command += f' 1> "{out_f}"'
    elif verbosity == 'verbose':
        command += f' 2> >(tee "{err_f}")'
        command += f' 1> >(tee "{out_f}")'
    else:
        assert True, "unreachable"
    
    cp = subprocess.run(command,
                        shell=True,
                        executable=shutil.which('bash'))
    return cp

cp = run_with_logging("./printer.py","printed.out","printed.err", verbosity='errors')

success = cp.returncode

if success:
    print("run succeeded")
else:
    print("run failed")
    
