import importlib
import pkgutil


def import_rule_classes():
    """
    :class:`ConfigParser` in `rules.__init__.py` will
    dynamically construct rule class base on configuration passed to it,
    ( using object.__subclasses__ )
    but it requires that all the rule classes need to be preloaded
    or the config parser can't get all valid candidates.
    This function will do this job.

    This logic needs an independent module.
    It's my fault that I let specific rules depend on `rules.__init__.py`
    (and I think it's ok and needn't refactoring),
    thus I can't put and call this loading method in the `rules.__init__.py`
    which will compose a circular import.

    Must manually call this method before doing any configuration parsing work.
    """
    user_rules = 'rules.user'
    submodule = importlib.import_module(user_rules)
    for _, name, _ in list(pkgutil.iter_modules(submodule.__path__)):
        importlib.import_module(f'{user_rules}.{name}', 'puntgun')
