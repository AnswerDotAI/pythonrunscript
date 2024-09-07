#!/usr/bin/env python3
# python>=3.9.6
import sys, re, os, subprocess, hashlib, logging, platform, argparse, tempfile, shutil, uuid, textwrap, shlex
from abc import ABC
from enum import Enum
from typing import NoReturn, Union

logging.basicConfig(level=logging.WARNING)
Log = Enum('Log', ['SILENT','ERRORS','VERBOSE'])

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.description='Runs a script, installing its dependencies in a cached, isolated environment'
    parser.add_argument('--dry-run',    action='store_true', help='report what pythonrunscript would do, without writing any files')
    parser.add_argument('--verbose',    action='store_true', help='comments on actions and prints all outputs and errors')
    parser.add_argument('--show-cache', action='store_true', help='print the cache directory of script environments')
    parser.add_argument('--clean-cache', action='store_true', help='purges all pythonrunscript environments')
    parser.add_argument('script', nargs='?', default=None, help='path to the script to run')
    parser.add_argument('arguments', nargs=argparse.REMAINDER, help='optional arguments to be passed to that script')
    parser.epilog='''    pythonrunscript runs Python scripts, handling their dependencies.

    To be exact, it will automatically install any needed dependencies in an
    isolated environment dedicated to your script (and possibly to other scripts
    with exactly identical dependencies).

    To do this it relies on your script having comments which declare its dependencies.
    
    You can use pythonrunscript to call your script directly (e,g, running
    `./pythonrunscript myscript.py`), or by changing your script's shebang to be
    pythonrunscript (e.g., setting your script's first line to
    "#!/usr/bin/env pythonrunscript").
    
    To find the dependencies, pythonrunscript parses your script's pre-code comment
    lines to find three kinds of dependency blocks: a requirements.txt block (for pip
    dependencies), or an environment.yml or conda_install_specs.txt block (for
    conda dependencies).

    A dependency block is defined by a single space of indentation and
    markdown-style code fences, including the file name which defines that type of
    block. So, for instance, you could add these comments to the head of your script
    before any code, to declare a dependency on tqdm:

    # ```requirements.txt
    # tqdm=4.66.4
    # ```

    The fencing syntax is analogous for environment.yml and conda_install_specs.txt
    blocks. An environment.yml block should contain an environment.yml file.
    Every line on a conda_intall_specs.txt block should be a "conda install spec",
    which is just the syntax used for arguments passed to `conda install`. It is
    documented here:
    https://conda.io/projects/conda/en/latest/user-guide/concepts/pkg-search.html

    To run a script with conda dependencies, you must already have conda installed.

    pythonrunscript works on Python 3.9.6 and later, which ships with macOS Sonoma.
    Since it creates isolated environments, you can run it using that system
    Python without corrupting the system Python.It also works on Linux, but not Windows.
    '''
    args = parser.parse_args()

    if sys.version_info < (3,9,6):
        print(f"I am being interpreted by Python version:\n{sys.version}")  # pyright: ignore
        print("But I need python version 3.9.6 or higher.\nAborting.") # pyright: ignore
        exit(1)         # pyright: ignore
    elif are_dependencies_missing():
        print(f"I am being run on the platform {platform.system()} and")
        print("I cannot find the required external commands bash and tee, so")
        print("I probably will not work. Aborting.")
        exit(1)
    elif args.show_cache:
        print_base_dirs()
        exit(0)
    elif args.clean_cache:
        pseudo_erase_dir(cache_base())
        exit(0)
    elif args.script is None:
        print(f"Error: pythonrunscript  must be called with either the path to a script, --show-cache, --clean-cache, or --help.")
        exit(1)
    else:
        script = args.script
        
    if not os.path.exists(script):
        print(f"Error: did not find the script {script}. Nothing to do.")
        exit(1)

    if args.dry_run:
        print("## This is a dry run. No files will be written.\n")

    if args.verbose:
        logging.info("Running in verbose")
        
    proj = Project.make_project(script,args.verbose,args.dry_run)
    
    if args.dry_run:
        perform_dry_run(proj)
        exit(0)

    if isinstance(proj, ProjectNoDeps):
        logging.info("No pip block and no conda block detected. Running directly")
        if args.verbose:
            print("## No dependencies needed. Running the script directly")
        proj.run(args.arguments)
    elif not proj.exists():
        logging.info("Needs an environment but none exists. Creating it")
        creation_success = proj.create()
        if not creation_success:
            trashed_env = pseudo_erase_dir(proj.project_path)
            print(f"## Creating a managed environment failed. Moved the broken environment to {trashed_env}",file=sys.stderr)
            exit(1)
    else:
        logging.info(f"Found pre-existing project dir: {proj.project_path}")
        if args.verbose:
            print(f"## Found pre-existing project dir: {proj.project_path}")
    # assert: proj exists
    if args.verbose:
        print("## Running the script using the project directory environment")
    proj.run(args.arguments)

def perform_dry_run(proj):
    "Describes actions for exists(), creates(), runs()"
    print("## After parsing, I would take these actions.\n")
    if isinstance(proj, ProjectNoDeps):
        print(f"## No project directory is needed since parsing found no dependencies in the file {proj.script}\n")
        print(f"## In a live run, I would run the script using the first python3 in your PATH.\n")
        print_python3_path()
        return
    elif not proj.exists():
        print(f"## The needed project directory does not exist so I would create this project directory:\n{proj.project_path}\n")
        print(f"## Inside, I would create this environment directory:\n{proj.envdir}\n")
        if proj.conda_envyml:
            print(f"## I found an environment.yml dependency block, so I'd use that.")
            print(f"## To install conda dependencies, I'd execute this conda environment creation command:\n")
            install_env_f = os.path.join(proj.project_path,'environment.yml')
            print(f"\t{make_conda_install_yml_command(proj.project_path,install_env_f)}\n")
        elif proj.conda_specs:
            print(f"## I found a conda_install_specs.txt block, so I'd use that.")
            print(f"## To install conda dependencies, I'd execute this conda install command:\n")
            install_spec_f = os.path.join(proj.project_path,'conda_install_specs.txt')
            print(f"\t{make_conda_install_spec_command(proj.project_path, install_spec_f)}\n")
        if proj.pip_requirements:
            print(f"## To install pip dependencies, I'd execute the following pip command:\n")
            print(f"\tpython3 -m pip install -r {os.path.join(proj.envdir,'requirements.txt')}\n")
            print_python3_path()
    print(f"## At this point, this project directory would exist:\n{proj.project_path}\n")
    print(f"## I'd run using this env dir:\n{proj.envdir}\n")
    return

def parse_dependencies(script, verbose=False) -> tuple[str,str,str,str]:
    "Parses script and returns any conda or pip dep blocks"
    LT = Enum('LT', [ 
        'BEG_CONDA_SPEC_YML','BEG_CONDA_ENV_YML','BEG_PIP_YML','END_YML',
        'BEG_CONDA_SPEC','BEG_CONDA_ENV','BEG_PIP','END',
        'TEXT'])
    
    p = {
        LT.BEG_CONDA_SPEC_YML : r"^# /// pythonrunscript-conda-install-specs-txt$",
        LT.BEG_CONDA_ENV_YML  : r"^# /// pythonrunscript-environment-yml$",
        LT.BEG_PIP_YML        : r"^# /// pythonrunscript-requirements-txt$",
        LT.END_YML            : r"^# ///$",
        LT.BEG_CONDA_SPEC     : r"^# ```conda_install_specs.txt$",
        LT.BEG_CONDA_ENV      : r"^# ```environment.yml$",
        LT.BEG_PIP            : r"^# ```requirements.txt$",
        LT.END                : r"^# ```$",
        LT.TEXT               : r"^#(| .*)$",
    }

    boxed_pip_block = ['']
    boxed_conda_spec_block = ['']
    boxed_conda_env_block = ['']

    block_type_content_delimiters = [
        ('requirements.txt', boxed_pip_block, [(LT.BEG_PIP_YML,LT.END_YML),
                                 (LT.BEG_PIP,LT.END),]),
        ('conda_install_specs.txt', boxed_conda_spec_block, [(LT.BEG_CONDA_SPEC_YML,LT.END_YML),
                                        (LT.BEG_CONDA_SPEC,LT.END),]),
        ('environment.yml', boxed_conda_env_block, [(LT.BEG_CONDA_ENV_YML,LT.END_YML),
                                       (LT.BEG_CONDA_ENV,LT.END),]),
    ]

    def make_block_pattern(begend:tuple[LT,LT]) -> str:
        (beg,end) = begend
        return rf"(?m:{p[beg]}\s(?P<content>({p[LT.TEXT]}\s)+?){p[end]}(?:\s)?)"

    def extract_content(match):
        return ''.join(
            line[2:] if line.startswith('# ') else line[1:]
            for line in match.group('content').splitlines(keepends=True)
        )

    # collect all comment lines starting with "# " or equalling "#"
    # transforming to strip # prefix
    comments = open(script,'r').read()
    if verbose:
        print(f"## Parsing this script for dependencies: {script}\n")
        print()
    
    for (block_type, boxed_content, begend_pairs) in block_type_content_delimiters:
        for begend in begend_pairs:
            block_pattern = make_block_pattern(begend)
            match = re.compile(block_pattern).search(comments)
            if match:
                if verbose:
                    print(f"### Extracted this {block_type} comment block:\n")
                    print(textwrap.indent(match.group('content'),'\t'))
                    print()
                boxed_content[0] = extract_content(match)
                break
    
    hash = hashlib.md5()
    hash.update(boxed_pip_block[0].encode('utf-8'))
    hash.update(boxed_conda_env_block[0].encode('utf-8'))
    hash.update(boxed_conda_spec_block[0].encode('utf-8'))
    return (hash.hexdigest(), boxed_pip_block[0], boxed_conda_env_block[0], boxed_conda_spec_block[0])

def tomlconfig_to_pip_conda(toml_config) -> tuple[str,str]:
    "From a TOML dict, to (pip reqs, conda python spec)"
    if 'requires-python' in toml_config:
        conda_python_install_spec = f"python{toml_config['requires-python']}"
    else:
        conda_python_install_spec = ''
    if 'dependencies' in toml_config:
        pip_reqs = '\n'.join(toml_config['dependencies']) + '\n'
    else:
        pip_reqs = ''
    return (pip_reqs,conda_python_install_spec)

def parse_script_toml(toml_str) -> tuple[str,str]:
    """
    From script TOML text, to (pip_reqs,conda python spec).
    
    This parses the TOML fragment in a PEP723 metadata block where TYPE=script.
    Uses a limited custom parser to neeed only Python 3.9.6 and zero deps.
    """
    toml_str = re.sub(r'#.*$', '', toml_str, flags=re.MULTILINE)
    config = {}
    requires_python_match = re.search(r'requires-python\s*=\s*"([^"]*)"', toml_str)
    if requires_python_match:
        config['requires-python'] = requires_python_match.group(1)
    dependencies_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', toml_str, re.DOTALL)
    if dependencies_match:
        dependencies_str = dependencies_match.group(1)
        dependencies = re.findall(r'"([^"]*)"', dependencies_str)
        config['dependencies'] = dependencies
    return tomlconfig_to_pip_conda(config)    

class Project(ABC):
    @staticmethod
    def make_project(script:str, verbose:bool, dry_run:bool):
        (dep_hash, pip_requirements, conda_envyml, conda_specs ) = parse_dependencies(script,verbose or dry_run)
        if conda_envyml or conda_specs:
            logging.info("dep block implies script will need conda for an environment.yml or conda_specs installation")
            return ProjectConda(script, dep_hash, pip_requirements, conda_specs, conda_envyml, verbose)
        elif pip_requirements:
            logging.info("dep block implies script will need only venv + pip")
            return ProjectPip(script, dep_hash, pip_requirements,conda_specs, conda_envyml, verbose)
        else:
            logging.info("no valid dep block found. no environment needed")
            return ProjectNoDeps(script,dep_hash, pip_requirements,conda_specs, conda_envyml, verbose)
        
    def __init__(self, script:str, dep_hash, pip_requirements:str, conda_specs:str, conda_envyml:str, verbose:bool):
        assert isinstance(conda_specs,str), "Bad input"
        self.script = script
        self.dep_hash = dep_hash
        self.pip_requirements = pip_requirements 
        self.conda_specs = conda_specs
        self.conda_envyml = conda_envyml
        self.verbose = verbose

    @property
    def project_path(self):
        "path to the project dir"
        return os.path.join( cache_base(), self.dep_hash )
    @property
    def envdir(self) -> str:
        "for pip projects, the venv dir. for conda, the prefix dir"
        return ""
    @property
    def interpreter(self) -> str:
        return os.path.join( self.envdir, 'bin','python3')
    def exists(self) -> bool:
        return False
    def create(self) -> bool:
        "False if creation failed, maybe leaving self.project_path in a non-runnable state"
        return True
    def run(self, args) -> NoReturn:
        run_script(self.interpreter,self.script,args)

def log_level_for_verbose(v:bool) -> Log:
    return Log.VERBOSE if v else Log.ERRORS

class ProjectPip(Project):
    @property
    def envdir(self): return os.path.join( self.project_path, 'venv' )
    def exists(self): return os.path.exists( self.project_path )
    def create(self):
        return create_venv(self.project_path, self.envdir,
                           self.pip_requirements,
                           log_level_for_verbose(self.verbose))


class ProjectConda(Project):
    @property
    def envdir(self): return os.path.join( self.project_path, 'condaenv' )
    def exists(self): return os.path.exists( self.project_path )
    def create(self):
        return setup_conda_prefix(self.project_path, self.envdir,
                                  self.conda_envyml,
                                  self.conda_specs,
                                  self.pip_requirements,
                                  log_level_for_verbose(self.verbose))
class ProjectNoDeps(Project):
    def exists(self): return True
    def create(self): return True
    @property
    def interpreter(self):
        return sys.executable


def run_with_logging(command:Union[str,list],proj_dir,out_f,err_f,verbosity):
    '''
    Runs command. Logs and maybe streams stdout and stderr.

    verbosity=Log.SILENT: log out and err. Report errors later
    verbosity=Log.VERBOSE: log and stream out and err.
    '''
    log_dir = os.path.join(proj_dir,"logs")
    os.makedirs(log_dir,exist_ok=True)
    out_f = os.path.join(log_dir, os.path.basename(out_f))
    err_f = os.path.join(log_dir, os.path.basename(err_f))
    if isinstance(command,list):
        command = shlex.join(command)
    if verbosity == Log.SILENT:
        command += f' 2>> "{err_f}"'
        command += f' 1>> "{out_f}"'
    elif verbosity == Log.ERRORS:
        command += f' 2> >(tee -a "{err_f}")'
        command += f' 1>> {out_f}'
    elif verbosity == Log.VERBOSE:
        command += f' 2> >(tee -a "{err_f}")'
        command += f' 1> >(tee -a "{out_f}")'
    else:
        assert True, "unreachable"

    cp = subprocess.run(command,
                        shell=True,
                        executable=shutil.which('bash'))
    did_succeed = (cp.returncode == 0)

    if (verbosity, did_succeed)   == (Log.VERBOSE,True):
        print(f"## This command completed successfully:\n\t{command}")
    elif (verbosity, did_succeed) == (Log.VERBOSE,False):
        print(f"## This command failed:\n\t{command}\n", file=sys.stderr)
        print(f"## Standard error output was printed above\n", file=sys.stderr)
        print(f"## Logs may be found in:\n\t{proj_dir}/logs", file=sys.stderr)
    elif (verbosity, did_succeed) == (Log.ERRORS,True):
        pass
    elif (verbosity, did_succeed) == (Log.ERRORS,False):
        print(f"## Error encountered trying to run this command:\n\t{command}", file=sys.stderr)
        print(f"## Logs may be found in:\n\t{proj_dir}/logs\n", file=sys.stderr)
        print(f"## This is the contents of the stderr:\n")
        with open(err_f,"r") as f:
            print(f.read())
    else:
        pass

    return did_succeed

    
def create_conda_prefix(proj_dir,condaprefix_dir:str,log_level:Log):
    success = run_with_logging(f'conda create --quiet --yes --prefix "{condaprefix_dir}"',
                               proj_dir,
                               "conda_create.out","conda_create.err",
                               log_level)
    if success:
        return True
    else:
        print("## Errors trying to create conda prefix directory",file=sys.stderr)
        return False


def pseudo_erase_dir(path):
    "Pseudo-erases a project dir by moving it to the temporary dir"
    logging.info(f"Moving {path} to {trash_base()}")
    dst = os.path.join( trash_base(), os.path.basename(path), str(uuid.uuid4()) )
    return shutil.move(path, dst )


def install_pip_requirements(proj_dir, pip_requirements, interpreter, log_level:Log) -> bool:
    reqs_path = os.path.join(proj_dir,'requirements.txt')
    with open(reqs_path, 'w') as f:
        f.write(pip_requirements)

    success = run_with_logging([interpreter, "-m", "pip", "install", "-r", reqs_path],
                               proj_dir,
                               "pip_install.out","pip_install.err",
                               log_level)
    if success:
        with open(os.path.join(proj_dir,"piplist.txt"),"w") as f:
            subprocess.run(shlex.join([interpreter, "-m", "pip", "list"]),
                           stdout=f, stderr=f,
                           shell=True,executable=shutil.which('bash'))
        return True
    else:
        print("## Errors trying to install pip requirements",file=sys.stderr)
        return False


def make_conda_install_yml_command(condaprefix_dir, env_yml_file) -> str:
    return f'conda env create --quiet --yes --file "{env_yml_file}" --prefix "{condaprefix_dir}"'

def make_conda_install_spec_command(condaprefix_dir, install_spec_file) -> str:
    return f'conda install --quiet --yes --file "{install_spec_file}" --prefix "{condaprefix_dir}"'

def setup_conda_prefix(proj_dir:str, condaprefix_dir:str,
                       conda_envyml:str,
                       conda_specs:str,
                       pip_requirements,
                       log_level:Log) -> bool:
    logging.info(f"creating conda prefix {condaprefix_dir}")
    create_conda_prefix(proj_dir, condaprefix_dir, log_level)

    success = False
    if conda_envyml:
        install_env_f = os.path.join(proj_dir,'environment.yml')
        with open(install_env_f, 'w') as f:
            f.write(conda_envyml)
        command_to_run = make_conda_install_yml_command(condaprefix_dir, install_env_f)
        success = run_with_logging(command_to_run,
                                   proj_dir,
                                   "conda_env_create_f.out","conda_env_create_f.err",
                                   log_level)
    elif conda_specs:
        install_spec_f = os.path.join(proj_dir,'conda_install_specs.txt')
        with open(install_spec_f, 'w') as f:
            f.write(conda_specs)
        command_to_run = make_conda_install_spec_command(condaprefix_dir, install_spec_f)
        success = run_with_logging(command_to_run,
                                   proj_dir,
                                   "conda_install.out","conda_install.err",
                                   log_level)
    else:
        assert True, "unreachable. "
    if success:
        with open(os.path.join(proj_dir,"exported-environment.yml"),"w") as f:
            cmd = ["conda","env","export","--quiet", "--prefix",condaprefix_dir]
            logging.info(f"exporting env with {cmd}")
            subprocess.run(shlex.join(cmd),
                           stdout=f, stderr=f,
                           shell=True,executable=shutil.which('bash'))
    else:
        print("## Errors trying to install conda dependencies",file=sys.stderr)
        return False

    if pip_requirements:
        interpreter = os.path.join(condaprefix_dir, 'bin','python3')
        return install_pip_requirements(proj_dir,pip_requirements,
                                        interpreter,
                                        log_level)
    else:
        return True


def run_script(interpreter, script, args) -> NoReturn:
    logging.info(
        f"running {script} using {interpreter} with args: {args}"
    )
    sys.stdout.flush()
    logging.info(f'os.execvp({interpreter}, [{interpreter},{script}] + {args})')
    os.execvp(interpreter, [interpreter,script] + args)

#
# venv operations
# 

def create_venv(proj_dir, venv_dir, pip_requirements, log_level:Log) -> bool:
    "Creates a script project dir for script at script_path"
    logging.info(f"Creating venv at  {venv_dir}")

    success = run_with_logging(["python3", "-m", "venv", venv_dir],
                               proj_dir,
                               "create_venv.out","creat_evenv.err",
                               log_level)
    if not success:
        print(f"## Error trying to create venv",file=sys.stderr)
        return False
    
    if pip_requirements:
        interpreter = os.path.join(venv_dir, 'bin','python3')
        return install_pip_requirements(proj_dir,
                                        pip_requirements,
                                        interpreter,log_level)
    else:
        return True


#
# helpers
#

def clean_name_from_path(p):
    return re.sub(r'[^A-Za-z0-9-]', '', os.path.basename(p))


def print_base_dirs():
    print(f"Cached project directores are in:\n{cache_base()}\n\n")
    print(f"Each directory's contains logs and other build artifacts.\n\n")
    print(f"Trashed and cleaned projects are here, waiting for disposal by the OS:\n{trash_base()}")


def trash_base() -> str:
    "Directory to use for trashing broken project dirs"
    return os.path.join( tempfile.gettempdir(), "pythonrunscript" )

def print_python3_path():
    if p := shutil.which('python3'):
        print(f"## The first python3 in your PATH: {p}")
    else:
        print("## There is no python3 in your PATH!")
    
def cache_base():
    cache_base = None
    if "XDG_CACHE_HOME" in os.environ:
        cache_base = os.environ["XDG_CACHE_HOME"]
    elif platform.system() == "Darwin":
        cache_base = os.path.join(os.path.expanduser("~"), "Library", "Caches")
    else:
        cache_base = os.path.join(os.path.expanduser("~"), ".cache")
    cache_base = os.path.join(cache_base, "pythonrunscript")
    return cache_base

def are_dependencies_missing() -> bool:
    return (platform.system() not in ['Linux','Darwin']
            and (shutil.which('bash') is None
                 or shutil.which('tee') is None))

if __name__ == "__main__":
    main()

