# ./pythonrunscript

`pythonrunscript` lets you

- define and run **single-file python scripts**
- which **can use external dependencies** from pip or conda
- while **automatically installing dependencies into isolated environments**

## Installation

There are two possible ways to install pythonrunscript:

2.  Either, do `python3 -m pip install pythonrunscript`.
1.  Or, just copy the file `pythonrunscript` into a directory named in your `PATH` variable.

## How to use pythonrunscript

pythonrunscript lets you declare your script’s dependencies in the script itself.

That is, the goal is to let you build and use scripts that *just run*, with no setup.

To declare your script’s pip dependencies, add a *pip requirements.txt block* to your script’s comments. This is a comment block which specifies the script’s external requirements, delimited by markdown code fencing, using the exact syntax of a pip requirements.txt file. Here below, the block declares a dependency on the pip package tqdm.

``` python
#!/usr/bin/env pythonrunscript
#
# ```requirements.txt:
# tqdm==4.66.4
# ```
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
```

The first time you run this script, pythonrunscript will parse its requirements.txt block, create an isolated environment in a cache directory, install its dependencies, and run the script from that environment. In later runs, it will just re-use that environment. To create the environment it uses venv, which is built into python, so the only requirement to use pythonrunscript is that python itself is already installed.

To run your script, call it with `pythonrunscript hello.py`.

To run your script directly (e.g, `./hello.py`), change your script’s first line, the shebang line, to the following: `#!/usr/bin/env pythonrunscript`.

How will this affect normal execution? It won’t. If you script does not have a pip requirements.txt block, pythonrunscript will simply pass it to python3 for execution as usual.

## How can I check what it will do? If it worked? What happened exactly?

Run pythonrunscript in `--dry-run` mode to get a preview of how it parses your file and the actions it *would* take.

Run with `--verbose` to hear copious commentary, and to see all output of subprocess commands. Normally, pythonrunscript only prints in case of an installation error. Under all circumstances it saves all generated output in a logs directory, as well as saving an `environment-resolved.yml` and a `pip-list.txt` that reflect the exact state of the environment after creation. These files are in a script’s project directory, in the cache, which is revealed by running with the `--show-cache` command. Running with `--clean-cache` erases all cached directories (actually, it moves them to the OS’s temporary directory for automatic disposal).

## What about conda dependencies?

Some popular dependencies, like [cudatoolkit](https://developer.nvidia.com/cuda-toolkit), cannot be installed by pip but need conda.

To specify conda dependencies, you must add a *conda environment.yml block* or a *conda<sub>installspecs</sub>.txt block*. You may use this instead of, or in addition to, a pip requirements.txt block. They use two other types of fenced comment blocks. The environment block is intoduced by ```` ```environment.yml ```` and it should contain an environment.yml file verbatim.

The install spec block is introduced by ```` ```conda_install_specs.txt ```` block, and it should introduce conda install specs. which should specify a “conda install specification”. A conda install spec is simply the string passed to the `conda install` command. Conda documents [exact syntax for an install specification](https://conda.io/projects/conda/en/latest/user-guide/concepts/pkg-search.html), which only requires naming the conda package, but also allows specifying the version, the channel, or specific builds.

For instance, this script uses a conda environment.yml block:

``` python
#!/usr/bin/env pythonrunscript
#
# ```environment.yml
# dependencies:
#   - python=3.10
#   - numpy
# ```
#
import numpy
import sys

print("I depend on numpy")
```

And this script uses a conda install specs block, for the same dependencies:

``` python
#!/usr/bin/env pythonrunscript
#
# ```conda_install_specs.txt
# python=3.10
# numpy
# ```
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
```

Do you really need conda? Maybe not! If you don’t specify conda dependencies, pythonrunscript won’t try to use it.

But you might need conda if you need conda-only dependencies, if you want to specify the version of python itself or to use packages outside of the Python ecosystem. This [weights & biases blog post](https://wandb.ai/wandb_fc/pytorch-image-models/reports/A-faster-way-to-get-working-and-up-to-date-conda-environments-using-fastchan---Vmlldzo2ODIzNzA) explains the situation well, and [this script will install conda](https://github.com/fastai/fastsetup/blob/master/setup-conda.sh) on all the platforms.)

## What, why would I want this?

If none of the above appeals to you, perhaps you never had problems with python dependency management before? (Congrats!) But if the dilemma is totally alien to you and you’re curious, here is the issue.

Suppose you’re writing a single-file Python module, i.e., a script, `hello.py`, like this:

``` python
#!/usr/bin/env python3
print("Hello, world")
```

Running it is easy. You can run the script by running `./hello.py` and it will just work. Hurray!

But then you need some functionality outside of the standard library, like yaml-parsing from an external dependency like PyYAML. So now you need to install that dependency. This is where pain starts.

Where do you install it? In your system’s python? Should you use sudo? Or in a managed environment? Managed how? With venv? With virtualenv? With conda? With nix, docker, something else? So should you install that manager first? Where? Do you need requirements.txt? Pipenv? Poetry? pyproject.toml? Something else? These questions all have answers but they are *boring and painful*. Once you distribute your script to someone else, the pain falls on them too. Can you just give them the file? No, since now you need to give them your script and also, perhaps, a mini-essay on how to answer those questions. If you are lucky enough (?) to be a seasoned expert in python dependency management and to associate only with other such experts, then you may not see the problem here. But it is real outside such orbits.

(soapbox mode…)

There is a reason that the Go and rust communities excel at shipping so many charming and effective command line applications. Why? Because their language toolchains have good support for shipping a static linked executable – that is to say, a single damn file which Just Works. Python would be truly great for scripting, except for the fact that it lacks this power, which makes it impractical to give your script to someone else who just wants to solve their problem with the minimum possible fuss. Sad.

Hopefully, this tool helps. The dependency syntaxes which it uses are exactly the syntaxes already supported by pip and conda. There is nothing exotic here. So you can do everything you can normally do with pip, such as specify dependencies not only as public PyPI packages but also as [URLs to GitHub repos](https://pip.pypa.io/en/stable/topics/vcs-support/). And you can do everything you can normally do with conda, such as specify the version of Python itself, or install vast wads of awkward binary code from dedicated channels like nvidia’s.

(soapbox off…)

## Wait, but I *enjoy* manually keeping environments nice and tidy, even for tiny little scripts!

Great, then, this is not for you. 😇 Cultivate your garden.

## Inspiration

- [swift-sh](https://github.com/mxcl/swift-sh) does the same trick for Swift
- [rust-script](https://rust-script.org) does the same trick for rust
- [scriptisto](https://github.com/igor-petruk/scriptisto) does this for any language, but at the cost of shifting the complexity into the comment block.
