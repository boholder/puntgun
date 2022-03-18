"""
These class check the (syntactic) legality of user-written configuration,
and extract field values from yaml-converted raw structure for further use.

It's sort of reinventing a wheel about argument parsing library like GNU readline,
but theses' input is a structured object (parsed from yaml file).
"""
import logging
from collections import defaultdict
from typing import List, Dict, Any

from puntgun.util import get_logger, log_assertion_error_with


class Field:
    """
    Pure config, the settings of the option that doesn't have inner fields
    (just "config-keyword: value" in yaml file).

    Rules use a set of this class to indicate what kind of field is valid inside them.
    You can define a field class by directly setting class attributes or using "of" class method.

    If you define one by using "of" class method, please set the ``is_init_by_class_attr`` to ``True``,
    to enable constraint checking when initialing instance.
    """
    logger = get_logger(__name__)

    # remain for child class to override
    is_init_by_class_attr = False
    config_keyword: str
    expect_type: type

    # optional setting attributes for overriding
    default_value: object = None
    conflict_with: List[str] = []
    require_with: List[str] = []
    required: bool = False

    @classmethod
    def of(cls,
           config_keyword: str,
           expect_type: type,
           default_value: object = None,
           conflict_with: List[str] = None,
           require_with: List[str] = None,
           required: bool = False) -> 'Field':
        """
        :param config_keyword: the keyword of this field in configuration file
        :param expect_type: what type its value should be
        :param default_value: default value when this field is absent in parent option
        :param conflict_with: list of ``config_keyword`` that cannot co-exist with this field
        :param require_with: list of ``config_keyword`` that must be present if this field present
        :param required: if is required in parent option
        """
        instance = cls()
        instance.config_keyword = config_keyword
        instance.expect_type = expect_type
        instance.default_value = default_value
        instance.conflict_with = conflict_with if conflict_with else []
        instance.require_with = require_with if require_with else []
        instance.required = required

        # now we can perform the check
        instance.__check_constrains()
        return instance

    def __init__(self):
        # Perform constrains check need class attributes to be set,
        # or will raise AttributeError.
        #
        # But if we initialize an instance by class method,
        # we need to first generate one instance via __init__ method,
        # without setting class attributes,
        # so let's skip the check if so.
        if self.is_init_by_class_attr:
            self.__check_constrains()

    @log_assertion_error_with(logger)
    def __check_constrains(self):
        """Assertions for checking constraints"""
        assert self.config_keyword, "Field's \"config_keyword\" must be set"
        assert self.expect_type, "Field's \"expect_type\" must be set"

        for keyword in self.require_with:
            assert keyword not in self.conflict_with, \
                f"Field [{self}]: " \
                f"keyword [{keyword}] shows in both require_with and conflict_with"

        if self.default_value:
            assert isinstance(self.default_value, self.expect_type), \
                f"Field [{self}]: " \
                f"default value [{self.default_value}] is not of expect type [{self.expect_type}]"

    def __str__(self):
        return self.config_keyword


class MapOption:
    """
    Represent a map-like (object-like?) option, ``Action`` for example.

    You can define a map-like option only by directly setting class attributes.
    """
    logger = get_logger(__name__)

    # remain for child class to override
    config_keyword = "map-option-generic"
    valid_fields: List[Field] = []

    def __init__(self, raw_config_value: Dict[str, Any]):
        """
        :param raw_config_value: the value corresponding to the "config_keyword" of this option
                in the parsed config dictionary.
        """
        self.raw_config = raw_config_value
        exist_field_settings = self.__filter_exist_field_settings()
        self.__check_constraints_of(exist_field_settings)
        self.exist_fields = self.__extract_exist_fields_into_dict(exist_field_settings, raw_config_value)

    @log_assertion_error_with(logger)
    def __filter_exist_field_settings(self) -> List[Field]:
        assert len(self.raw_config) > 0, \
            f"Option [{self}] must have at least one field."
        exist_fields = self.raw_config.keys()
        # check invalid fields
        valid_config_keywords = [field.config_keyword for field in self.valid_fields]
        for field in exist_fields:
            assert field in valid_config_keywords, \
                f"Option [{self}]: [{field}] is not a valid field."
        # then shrink exist fields to valid fields
        exist_fields = [field for field in self.valid_fields
                        if field.config_keyword in exist_fields]
        return exist_fields

    @log_assertion_error_with(logger)
    def __check_constraints_of(self, exist_field_settings: List[Field]):
        """
        Check that all fields aren't violating the constraints themselves made.
        """

        # check (option) required fields
        for field in [field for field in self.valid_fields if field.required]:
            assert field.config_keyword in exist_field_settings, \
                f"Option [{self}] requires " \
                f"field [{field}] must be configured," \
                f"but it's absent."

        # check (exist fields) required fields
        for field in exist_field_settings:
            for required_field in field.require_with:
                assert required_field in exist_field_settings, \
                    f"Option [{self}]: " \
                    f"field [{field}] requires another field [{required_field}] must be configured, " \
                    f"but it's absent."

        # check fields conflict constraints
        for field in exist_field_settings:
            for required_field in field.conflict_with:
                assert required_field in exist_field_settings, \
                    f"Option [{self}]: " \
                    f"field [{field}] is conflict with another existing field [{required_field}]."

    @log_assertion_error_with(logger)
    def __extract_exist_fields_into_dict(self, exist_field_settings: List[Field],
                                         raw_config: dict) -> Dict[str, Any]:
        result = {}
        for field in exist_field_settings:
            keyword = field.config_keyword
            value = raw_config[keyword]

            # check if type is same as expect
            assert isinstance(value, field.expect_type), \
                f"Option [{self}]: " \
                f"field [{keyword}] must be of type [{field.expect_type}], " \
                f"but it's given in type [{type(value)}] and value [{value}]."

            result[keyword] = value

        return result

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        return self.exist_fields[item]


class ListOption:
    """
    Represent a list-like option, ``RuleSet`` for example.

    You can define a list-like option only by directly setting class attributes.

    * Same fields can occur multiple times, which is different from ``AbstractMapOption``.
    * Fields' ``conflict_with``, ``required_with``, ``required`` constraints
      are not validated in this type of option.
    """
    logger = logging.getLogger(__name__)

    # remain for child class to override
    config_keyword = "list-option-generic"
    valid_fields: List[Field] = []

    def __init__(self, raw_config_value: List[Dict[str, Any]]):
        """
        :param raw_config_value: the value corresponding to the "config_keyword" of this option
                in the parsed config dictionary.
        """
        self.raw_config = raw_config_value
        self.exist_fields = self.__extract_exist_fields_into_dict(self.__filter_exist_field_settings(),
                                                                  raw_config_value)

    @log_assertion_error_with(logger)
    def __filter_exist_field_settings(self) -> List[Field]:
        """
        Check that all fields are valid.
        """
        assert len(self.raw_config) > 0, \
            f"Option [{self}] must have at least one field."

        # collect items' key in raw_config into a flatted list
        # for example:
        # raw_config = [{"item1": a-value}, {"item2": {"inner-field": a-value}]
        # exist_item_names = {"item1", "item2"}
        exist_keys_list = [item.keys() for item in self.raw_config]
        exist_item_names = set([key for keys in exist_keys_list for key in keys])

        # check invalid fields
        valid_config_keywords = [field.config_keyword for field in self.valid_fields]
        for field in exist_item_names:
            assert field in valid_config_keywords, \
                f"Option [{self}]: [{field}] is not a valid item."

        # then shrink exist fields to valid fields
        return [field for field in self.valid_fields
                if field.config_keyword in exist_item_names]

    @log_assertion_error_with(logger)
    def __extract_exist_fields_into_dict(self, exist_field_settings: list,
                                         raw_config: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        result = defaultdict(list)
        for field in exist_field_settings:
            keyword = field.config_keyword
            # there may be multiple same items with the same config_keyword
            matched_values = list(filter(lambda x: x is not None, [item.get(keyword) for item in raw_config]))

            for value in matched_values:
                # check if type is same as expect
                assert isinstance(value, field.expect_type), \
                    f"Option [{self}]: " \
                    f"field [{field}] must be of type [{field.expect_type}], " \
                    f"but it's given in type [{type(value)}] and value [{value}]."

                # add all same keyword items' value into one list, under keyword key.
                result[keyword].append(value)

        return result

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        return self.exist_fields[item]
