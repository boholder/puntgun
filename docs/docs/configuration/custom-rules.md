# Custom Rules

This page describes how to develop custom rules.

This tool is distributed as a standalone application, you cannot add rules by modifying the source code,
so first please follow [this documentation](https://boholder.github.io/puntgun/development/contributing/#prepare-for-local-development)
to make your local development environment ready.

## Directory structure of source code

All rule-related code are stored under the [**rules**](https://github.com/boholder/puntgun/tree/main/puntgun/rules) module.
Depending on the type of entity that the rule operates, rules are divided into two categories:
user rules and tweet rules, which are stored in the corresponding **user** and **tweet** submodules.
The rules are further categorized by the purpose (source, filter, action...) and stored in different modules.

```test
┌─cmp@user ../puntgun/puntgun/rules ‹main*›
└─▪ $ tree
.
├── __init__.py
├── config_parser.py
├── tweet
│   └── __init__.py
└── user
    ├── __init__.py
    ├── action_rules.py
    ├── filter_rules.py
    ├── plan.py
    ├── rule_sets.py
    └── source_rules.py
```

## Useful reusable components



## How the rules are loaded

