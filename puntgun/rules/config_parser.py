import importlib
import pkgutil
from typing import List, TypeVar

from loguru import logger
from pydantic import ValidationError

from rules import FromConfig


def import_rule_classes():
    """
    :class:`ConfigParser` will dynamically construct rule class base on configuration passed to it,
    ( using object.__subclasses__ )
    but it requires that all the rule classes need to be preloaded
    or the config parser can't get all valid candidates.
    This function will do this job.
    """

    for rule_module_name in ['rules.user']:
        rule_module = importlib.import_module(rule_module_name)
        for _, name, _ in list(pkgutil.iter_modules(rule_module.__path__)):
            importlib.import_module(f'{rule_module_name}.{name}', 'puntgun')


class ConfigParser(object):
    # There are only once parsing process for each run,
    # so I guess it's ok to use a class variable to store the errors,
    # and use this class as singleton pattern.
    # Sort of inconvenient when unit testing.
    _errors: List[Exception] = []

    _T = TypeVar('_T', bound=FromConfig)

    @staticmethod
    def parse(conf: dict, expected_type: _T):
        """
        Take a piece of configuration and the expected type from caller,
        recognize which rule it is and parse it into corresponding rule instance.
        Only do the find & parse work, won't construct them into cascade component instances.

        Collect errors occurred during parsing,
        by this way we won't break the whole parsing process with error raising.
        So that we can report all errors at once after finished all parsing work
        and the user can fix them at once without running over again for configuration validation.
        """

        def generate_placeholder_instance():
            """
            Return a placeholder instance which inherits from the given expected class.
            For letting caller continue parsing.
            """
            return type('FakeSubclassOf' + expected_type.__name__, (expected_type,), {})()

        logger.debug('Config parsing called with: expect type:{}, config:{}',
                     expected_type.__name__, conf)

        for subclass in expected_type.__subclasses__():
            if subclass.keyword() in conf:
                try:
                    # let the subclass itself decide how to parse
                    return subclass.parse_from_config(conf)
                except (ValidationError, ValueError) as e:
                    # catch validation exceptions raised by pydantic and store them
                    ConfigParser._errors.append(e)
                    return generate_placeholder_instance()

        error = ValueError(f"Can not find the rule of the [{expected_type}] type from configuration: {conf}")
        logger.error(error)
        ConfigParser._errors.append(error)

        return generate_placeholder_instance()

    @staticmethod
    def errors():
        """Get errors occurred when paring plan configuration"""
        return ConfigParser._errors

    @staticmethod
    def clear_errors():
        ConfigParser._errors = []


# import all rule classes when loading this module
import_rule_classes()
