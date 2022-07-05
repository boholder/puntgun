import importlib
import pkgutil

import rules


def import_rule_classes():
    """
    This logic worth an independent module.
    It's my fault that I let specific rules depend on rules.__init__.py,
    thus I can't call this loading method in the rules.__init__.py.
    """

    # first get modules under "rules"
    for _, submodule_name, _ in list(pkgutil.iter_modules(rules.__path__)):
        # skip this loader module
        if submodule_name == 'loader':
            continue

        # then get each rule type module under that module
        submodule = importlib.import_module(f"{rules.__name__}.{submodule_name}").__path__
        for _, rule_type_module_name, _ in list(pkgutil.iter_modules(submodule)):
            rule_type_module = importlib.import_module(f"{__name__}.{submodule_name}.{rule_type_module_name}")
            print(rule_type_module)
