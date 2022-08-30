# Contributing to the puntgun

Thank you for considering making this tool even better.

You'll need a [GitHub account](https://github.com/) to participate in contributing,
which can be an obstacle, and I apologize for that.
You can also email me (I generally check my email once a week),
but it is difficult for me personally to reply to everyone appropriately,
so please consider this as a backup option only.

There is no strict limit to how and what you can contribute, here are a few ways we can think of.

## Programming aspect

* Improving unsatisfied code: There are some unsatisfactory pieces of logic in the code, they work, but they deserve to be better.
  You can find them by [searching for **IMPROVE** marks](https://github.com/search?q=%22IMPROVE%22+repo%3Aboholder%2Fpuntgun+in%3Afile&type=code)
  in the code.
* Join the discussion about or deal with [unclosed issues](https://github.com/boholder/puntgun/issues).
* Develop new features, new rules to this tool (and we recommend developing in the steps [described below](#recommended-developing-steps)).
* Improve CI/CD process.
* Add more test cases.

For local development, please read [this part](#prepare-for-local-development).
For security and vulnerability reports, please read [this documentation](https://github.com/boholder/puntgun/security/policy).

## Non-programming aspect

* Improving documentation:
    * Make documentations easier to understand by changing expressions.
    * Fixing syntax and typo errors in documentation.
* Join [the community](https://github.com/boholder/puntgun/discussions) on the GitHub:
    * Help others by [answering questions](https://github.com/boholder/puntgun/discussions/categories/q-a).
    * [Request or vote new features](https://github.com/boholder/puntgun/discussions/categories/feature-requests).

## Prepare for local development

If you are not familiar with how to clone a project and submit a pull request using GitHub,
please read this [documentation](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

This project requires Python version 3.10,
please [download a new one](https://www.python.org/downloads/) or upgrade your existing Python's version.

Sorry to be abrupt, but... [pipx](https://github.com/pypa/pipx) is an excellent tool for managing executable python libraries,
you may want to use it instead of `pip` for installing pypi-based tools,
almost all tools used in the project can be happily installed in this convenient way.

This project uses the [PDM](https://pdm.fming.dev/latest/) as package managing tool,
if you are not skilled enough to use other package management tools to
be compatible with the PDM configuration (scripts defined in `pyproject.toml`, etc.),
[install the PDM](https://pdm.fming.dev/latest/#recommended-installation-method).

PDM will [detect and reuses](https://pdm.fming.dev/latest/usage/venv/) the virtualenv python environment under the project directory,
so you can develop with your PDM-not-supported IDEs (PyCharm for example) in virtualenv style,
while using PDM truly managing everything via terminal.

Now simply install both production and development dependencies with `pdm install`.
All set, now you can play with the code or get your hands dirty to make things happen.

## Scripts and tools for development

All development scripts are defined under `[tool.pdm.scripts]` section in `pyproject.toml`.

### Run tests

```shell
pdm run test
```

This project uses [pytest](https://docs.pytest.org/en/7.1.x/) as the unit testing framework.
Test cases are written under `./tests` directory with `test_` prefix.

### Correct code style

> **Warning**
> Running this script will **actually change the code**, make sure commit your code before running.

```shell
pdm run lint
```

### Render the documentation website

```shell
pdm run doc
```

This project uses [MkDocs](https://www.mkdocs.org/getting-started/) as documentation website framework,
with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/getting-started/#getting-started) as website theme.
Documentation source is written in Markdown format, under `./docs` directory.

## Recommended developing steps

实现issue前要先声明接下工作，并简述准备做的实现方式。（这样能在写代码前指出需要注意的地方）
https://blog.jetbrains.com/upsource/2017/01/18/code-review-as-a-gateway