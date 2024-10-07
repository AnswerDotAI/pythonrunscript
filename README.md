# ./pythonrunscript

`pythonrunscript` lets you

- define and run **single-file python scripts**
- which **automatically install needed dependencies into isolated environments**
- while **using normal external dependencies** from pip or conda

## How to use pythonrunscript

pythonrunscript lets you declare your script’s dependencies in the script itself.

This is in order to let you build and use scripts that *just run*, with no environment setup.

To declare your script’s pip dependencies, add a *pip requirements block* to your script’s comments. This is a comment block which embeds a normal pip requirements.txt file into script, by using Python's syntax for [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata). Here below, the block declares a dependency on the pip package `tqdm`.

``` python
#!/usr/bin/env pythonrunscript
#
# /// pythonrunscript-requirements-txt
# tqdm==4.66.4
# ///
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
```

The first time you run this script, pythonrunscript will extract the embedded requirements.txt file, create an isolated environment in a cache directory, install its dependencies, and run the script from that environment. In later runs, it will just re-use that environment. To create the environment it uses venv, which is built into python, so the only requirement to use pythonrunscript is that python itself is already installed.

To run your script, call it with `pythonrunscript hello.py`.

Or, to run your script directly by doing `./hello.py`, change your script’s first line, the shebang line, to the following: `#!/usr/bin/env pythonrunscript`.

How does this affect normal execution? It doesn't. If you script doesn't have a pip requirements.txt block, pythonrunscript will simply pass it to python3 for execution as usual. And if you run the script with `python3 hello.py`, then these special comments are ignored like all other comments. The upshot is that if you modify a script to be run by pythonrunscript, it can still be run as usual 

## Installation and Requirements

Here are two ways to install pythonrunscript:

1.  Do `python3 -m pip install pythonrunscript`, which will install `pythonrunscript` into your PATH.
2.  Or, manually copy the file `pythonrunscript` from the `bin/` directory of this repo into a directory named in your `PATH` variable.

`pythonrunscript` runs on Linux and macOS, and needs Python 3.9.6 or higher (which means it can run using the system Python built into macOS Sonoma). It requires conda only if you want to run scripts which themselves require conda.

## How can I check what it will do? If it worked? What happened exactly?

Run pythonrunscript in `--dry-run` mode to get a preview of how it parses your file and the actions it *would* take.

Run with `--verbose` to hear copious commentary, and to see all output of subprocess commands. Normally, pythonrunscript only prints in case of an installation error. Under all circumstances it saves all generated output in a logs directory, as well as saving an `environment-resolved.yml` and a `pip-list.txt` that reflect the exact state of the environment after creation. These files are saved in the script’s project directory, in the cache, which is revealed by running with the `--show-cache` command. Running with `--clean-cache` erases all cached directories (actually, it moves them to the OS’s temporary directory for automatic disposal).

## What about conda dependencies?

Some popular dependencies, like [cudatoolkit](https://developer.nvidia.com/cuda-toolkit), cannot be installed by pip but need conda.

To specify conda dependencies, you must add a *conda environment.yml block* or a *conda_install_specs_.txt block*. You may use this instead of, or in addition to, a pip requirements.txt block. They use two other types of fenced comment blocks. The environment block is intoduced by ```` /// pythonrunscript-environment-yml ```` and it should contain an environment.yml file verbatim.

The install spec block is introduced by ```` /// pythonrunscript-conda-install-specs-txt ```` block, and it should introduce conda install specs. A conda install spec is simply the string passed to the `conda install` command. Conda documents the [exact syntax for a conda install spec](https://conda.io/projects/conda/en/latest/user-guide/concepts/pkg-search.html), which only requires naming the conda package, but also allows specifying the version, the channel, or specific builds.

For instance, this script uses a conda environment.yml block:

``` python
#!/usr/bin/env pythonrunscript
#
# /// pythonrunscript-environment-yml
# dependencies:
#   - python=3.10
#   - numpy
# ///
#
import numpy
import sys

print("I depend on numpy")
```

And this script uses a conda install specs block, for the same dependencies:

``` python
#!/usr/bin/env pythonrunscript
#
# /// pythonrunscript-conda-install-specs-txt
# python=3.10
# numpy
# ///
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
```

Do you really need conda? Maybe not! If you don’t specify conda dependencies, pythonrunscript won’t use conda.

But you might need conda if you want to use conda-only dependencies, to specify the version of python itself, or to use packages outside of the Python ecosystem. This [weights & biases blog post](https://wandb.ai/wandb_fc/pytorch-image-models/reports/A-faster-way-to-get-working-and-up-to-date-conda-environments-using-fastchan---Vmlldzo2ODIzNzA) explains the situation well, and [this script will install conda](https://github.com/fastai/fastsetup/blob/master/setup-conda.sh) on all the platforms.)

## What, why would I want this?

(For a muuuch longer explanation, check out [dev chat with me (Alexis), Jeremy Howard, and Johno Whitaker](https://www.youtube.com/watch?v=IECcEbXlIl8).)

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


## Wait, is pythonrunscript an implementation of PEP-723? The same as tools like `uv`?

Good questions! The answers are yes and no. Here is the situation.

PEP-723 defines the official syntax for embedding _any kind of metadata_ in a Python script.

It also shows _one_ particular implementation of that standard, with the "script" type of metadata. This is a metadata block introduced by the opening delimiter ```` /// script ````. Here's an example of a script with such a block:

``` python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
# ]
# ///
#
import numpy
import sys

print("I depend on numpy")
```

As you can see, the "script" metadata type requires a TOML-like syntax, and it lets you declare pip dependencies (like `numpy`) as well as a required version of python (like `3.11`). When a Python script has this "script" type metadata, a compliant tool _can_ use it to run the Python script as a single-file script, by reading the metadata, fetching the dependencies, and running the script in an isolated environment containing those dependencies.

`pythonrunscript` will do this. It consumes the "script" metadata type. If the "script" metadata only declares pip dependencies, pythonrunscript just uses pip to install them. If it also declares a required python version, then pythonrunscript requires that you have conda installed, since it will use conda to manage the python version itself.

Another tool (at the time of this writing, the only other tool?) which supports this "script" metadata type is [uv](https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies), which is excellent and which I highly recommend. It doesn't rely on conda.

Bu in addition to the "script" type metadata, PEP-723 also defines the syntax by which you can define _other_ metadata types. pythonrunscript also defines the following types:

- `pythonrunscript-requirements-txt`, which lets you embed a standard `requirements.txt` file
- `pythonrunscript-conda-install-specs-txt`, which lets you embed a list of normal conda install specs
- `pythonrunscript-environment-yml`, which lets you embed a normal `environment.yml` file.

In other words, pythonrunscript complies the required PEP-723 syntax for embedding inline metadata, complies with its mechanism for defining particular types of inline metadata, and defines three types which simply represent embeeding exactly the dependency files which we people already use.

## Alternatives: `uv`

I'd say that pythonrunscript is a better choice if:

- You want to describe your dependencies using exactly the files and formats you already use.
- You need certain dependencies available only on conda, such as substantial executable like `ffmpeg` for video transcoding, `poppler` for processing PDFs, or various heavier ML components.
- You like using a tool which requires only python, and possibly conda, and which does not introduce much that is new or hard to inspect. (pythonrunscript itself is less than 600 lines of Python.)

Given that both pythonrunscript and uv support the "script" type metadata, which should you use?

I'd say that `uv` is better choice if:

- You don't mind writing your dependencies as TOML fragments.
- You don't need conda-only dependencies.
- You value `uv`'s speed, which is much better.

## Alternatives: pip.wtf

I have not tried this but it seems like a great solution if you don't want your users or yourself to have to install anything new.

It's beautifully simple, it's just eight lines of code which defines a function, whcih you add directly to your script. In your script, calling this function will install the script's dependencies and run it using them. This strikes me as perfect for certain use cases.

However, it might not be approriate when you want your script to run like a normal script by default, e.g., not to install dependencies when you just run it with the normal interpreter, or when you need conda because your project depends on conda-only dependencies.


## Inspiration and related projects

- [pip.wtf](https://pip.wtf), as mentioned above.
- [uv](https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies), as mentioned above.
- [PEP-723](https://peps.python.org/pep-0723/) defines a standard, general syntax for different types of *inline script metadata*. This lets you embed metadata into a script's comments (just like pythonrunscript does). 
- [swift-sh](https://github.com/mxcl/swift-sh) does the same trick for Swift
- [rust-script](https://rust-script.org) does the same trick for rust
- [scriptisto](https://github.com/igor-petruk/scriptisto) does this for any language, but at the cost of shifting the complexity into the comment block.

