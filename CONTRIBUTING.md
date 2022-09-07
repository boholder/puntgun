# Contributing to the puntgun

Thank you for considering making this tool better.

You'll need a [GitHub account](https://github.com/) to participate in contributing,
which can be an obstacle, and I apologize for that.
You can also [email me](mailto:bottleholder@anche.no) (I generally check email once a week),
but it is difficult for me personally to reply to everyone appropriately,
so please consider this as a backup option only.

There is no strict limit to how and what you can contribute, here are a few ways we can think of.

## Programming aspect

* Improving unsatisfied code: There are some unsatisfactory pieces of logic in the code, they work, but they deserve to be better.
  You can find them by [searching for **IMPROVE** marks](https://github.com/search?q=%22IMPROVE%22+repo%3Aboholder%2Fpuntgun+in%3Afile&type=code)
  in the code.
* Join the discussion about or deal with [unclosed issues](https://github.com/boholder/puntgun/issues).
* Develop [new features](https://github.com/boholder/puntgun/discussions/categories/feature-requests)
  to this tool (and we recommend developing in the steps [described below](#prepare-for-local-development)).
* Improve CI/CD process.
* Add more test cases.

For local development, please read [this part](#prepare-for-local-development).
For security and vulnerability reports, please read [this documentation](https://github.com/boholder/puntgun/security/policy).

## Non-programming aspect

* Improving [documentation](https://github.com/boholder/puntgun/tree/main/docs/docs):
    * Make documentation easier to understand by changing expressions.
    * Fixing syntax and typo errors in documentation.
    * Add more necessary details for the user to know the specific behavior of the tool without having to read the code.

* Join [the community](https://github.com/boholder/puntgun/discussions) on the GitHub:
    * Help others by [answering questions](https://github.com/boholder/puntgun/discussions/categories/q-a).
    * [Request or vote new features](https://github.com/boholder/puntgun/discussions/categories/feature-requests) (the more details the better!).
    * [Share](https://github.com/boholder/puntgun/discussions/categories/good-usage) good plan configuration and automation usage.

## Recommended contributing approaches

### Tell us what you intend to do before finishing it

When you decide to make programming aspect contributions,
we expect you to indicate in the corresponding issue or new issue that you intend to do this and how you intend to implement it,
like [this article](https://blog.jetbrains.com/upsource/2017/01/18/code-review-as-a-gateway).
Industry experience tells us that shift-left checks and discussions is good for software development,
for example we can provide more relevant knowledge, project details and advice to help you do things better when we know what you want to do.

Of course there is no mandatory requirement
(compliments of [the freewheeling open source community](http://www.catb.org/~esr/writings/cathedral-bazaar/)!),
the code for this project is open source under [the MIT license](https://github.com/boholder/puntgun/blob/main/LICENSE),
and you do not need to get anyone's permission to make changes to (your fork of) this project,
**you just need to make it work for your personal needs**.
If you feel that your changes will also benefit the upstream, you can submit a Pull Request to the upstream,
and only then does the "contribution" begin.

### PR should pass lint checks

Remember to run `pdm run lint` and make sure all checks pass before creating Pull Request,
[the CI](https://github.com/boholder/puntgun/blob/main/.github/workflows/test.yml) will fail if any lint tool complains.

### Remember to write changelog

There is a [`CHANGELOG.md`](https://github.com/boholder/puntgun/blob/main/CHANGELOG.md) file
under the project root directory that is used to record changes,
please modify this file correspondingly when you commit the Pull Request.
The contents of this file will be copied by release CI to the GitHub Release when the version is released.
The maintainer will manually check the change logs before the release,
so there is no need to get too hung up on the details of change log writing.

Summarize your change in an imperative or descriptive sentence
(just like a commit message: `Fix... [#issue-number]`, `follower - new user filter rule for...`),
and try to keep it both short and specific, with specificity taking precedence.
Check the [Change Log](https://github.com/boholder/puntgun/blob/main/CHANGELOG.md) file for more examples.

The Change Log has the following categories (create if current release does not have the category titles you need):

* `Features`: New rules, new command line options... what users can sense
* `Removals`: Removals or deprecations, what users can sense
* `Improvements`: Code refactors, better error handling... changes on existing code, CI, tests...
* `Bug Fixes`: Newly closed `bug` issues
* `Documentation`: Documentation updates
* `Dependencies`: Changes to dependencies
* `Miscellany`: Changes that don't fit any of the other categories

Although uncommon, there are cases where one change involves multiple categories,
in these cases multiple change logs can be written correspondingly.
For reference, here are some common cases with treatments:

* **Modifying documentation while modifying code**: Omitting `Documentation` change log
* **Modified dependencies while modifying code**: Write both code modification and `Dependencies` change logs
* **Modifying existing code while adding new features**: Write both `Features` and `Improvements` change logs

## Prepare for local development

This project requires Python version **3.10** or above.
If you are not familiar with how to clone a project and submit a Pull Request using GitHub,
please read [this documentation from GitHub official](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

(Sorry to be abrupt, but... [**pipx**](https://github.com/pypa/pipx) is an excellent tool for managing executable python libraries,
you may want to use it instead of **pip** for installing pypi-based executable tools.
Almost all tools used in the project can be happily installed in this convenient way,
though they will be well cared by other managing tools, so you need not manually install them while you using scripts.
If you install them with **pipx** in addition to venv and **PDM**, you can use them anywhere, that is convenient.)

This project uses the [**PDM**](https://pdm.fming.dev/latest/) as package managing tool,
if you are not skilled enough to use other package management tools to
be compatible with the **PDM** configuration (scripts defined in `pyproject.toml`, etc.),
[install the **PDM**](https://pdm.fming.dev/latest/#recommended-installation-method).

PDM will [detect and reuses](https://pdm.fming.dev/latest/usage/venv/) the virtualenv python environment under the project directory,
so you can write code with your PDM-not-supported IDEs (PyCharm for example) in virtualenv style,
while using PDM truly managing everything via terminal.

Now simply install all dependencies with `pdm install`.
All set, now you can play with the code or get your hands dirty to make things happen.

## Scripts and tools for development

All development scripts are defined under `[tool.pdm.scripts]` section in `pyproject.toml`.

### Run tests

```shell
pdm run test
```

This project uses [**pytest**](https://docs.pytest.org/en/7.1.x/) as the unit testing framework,
which will be installed with development dependencies.
Test cases are written under `./tests` directory with `test_` prefix.

```shell
pdm run coverage
```

This script will run the test suite with **pytest** while
generating a html format coverage report with [**coverage.py**](https://coverage.readthedocs.io).

### Linting

> **Warning**
> Running this script will **actually change the code**, make sure commit your code before running.

```shell
pdm run lint
```

This project uses [**pre-commit**](https://pre-commit.com/#intro) for [linting](https://en.wikipedia.org/wiki/Lint_(software)),
it will help us to manage other linting tools.
Check `.pre-commit-config.yaml` under root directory to see pre-commit hooks configuration.
Currently, this project uses:

* [**black**](https://black.readthedocs.io/en/stable/) for code style automatic formatting.
* [**isort**](https://pycqa.github.io/isort/) for import statements sorting.
* [**codespell**](https://github.com/codespell-project/codespell) for typo checking.
* [**flake8**](https://flake8.pycqa.org/en/latest/index.html) for common Python programming problem checking.
* [**mypy**](https://mypy.readthedocs.io/en/stable/) for static type hint scanning.

As we all know, the rigid linting results sometimes does not make sense or have false positives,
if your changes encounter unreasonable linting results,
feel free to modify the configuration of the corresponding tool.

### Render the documentation website

```shell
pdm run doc
```

This project uses [**MkDocs**](https://www.mkdocs.org/getting-started/) as documentation website framework,
with [**Material for MkDocs**](https://squidfunk.github.io/mkdocs-material/getting-started/#getting-started) as website theme.
They will also be installed with development dependencies.
Documentation source is written in Markdown format, under `./docs` directory.