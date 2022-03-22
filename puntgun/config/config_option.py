from collections import defaultdict
from typing import List, Dict, Any, Type

from puntgun import util


class Option(object):
    """
    Option classes are responsible for checking the validity of user-written
    configuration, and extracting field values from yaml-converted raw dictionary structure,
    and act as a wrapper for the contained values.

    Options can be nested, so there are some class attributes
    that describe relationships between other options and between parent option.
    """

    # ---remain for child class to override
    config_keyword: str = "generic-option"

    # ---optional setting attributes for overriding
    # list of ``config_keyword`` that cannot co-exist with this option
    conflict_with: List[str] = []
    # list of ``config_keyword`` that must be present if this option present
    require_with: List[str] = []
    # if is required in parent option
    required: bool = False

    @classmethod
    def build(cls, config_value):
        """
        Return wrapped instance (:class:`ListOption`, :class:`MapOption`)
        or directly return the input primitive value (Field).

        Called by :class:`MapOption` and :class:`ListOption`'s ``__init__`` method
        to automatically build inner fields,
        so one parent option (which inherited from these two) doesn't need to
        manually build their inner fields (has-a).

        But parent options should know exactly what type (instance, or primitive value)
        inner fields will be and how to use them.
        """
        raise NotImplementedError


class Field(Option):
    """
    Represent a basic option that doesn't have inner fields or items,
    only have a primitive value.
    Rules in source code use a set of this type to indicate
    what kind of field is valid inside them.

    You can define a child class by directly setting class attributes
    or using ``of`` metaclass method to generate one.
    If one field has its own inner fields or have complex logic,
    I recommend defining class attributes, if that field is just a primitive value,
    using ``of`` method is more convenient.
    """

    logger = util.get_logger(__qualname__)

    # remain for child class to override
    config_keyword: str
    expect_type: type

    # optional setting attributes for overriding
    default_value: object = None

    @classmethod
    def of(cls,
           config_keyword: str,
           expect_type: type,
           default_value: object = None,
           conflict_with: List[str] = None,
           require_with: List[str] = None,
           required: bool = False) -> 'Field':
        """
        Define a field type directly by class method.

        :param config_keyword: the keyword of this field in configuration file
        :param expect_type: what type its value should be
        :param default_value: default value when this field is absent in parent option
        :param conflict_with: list of ``config_keyword`` that cannot co-exist with this field
        :param require_with: list of ``config_keyword`` that must be present if this field present
        :param required: if is required in parent option
        """

        class NewField(Field):
            def __init__(self):
                super().__init__()

        NewField.config_keyword = config_keyword
        NewField.expect_type = expect_type
        NewField.default_value = default_value
        NewField.conflict_with = conflict_with if conflict_with else []
        NewField.require_with = require_with if require_with else []
        NewField.required = required

        return NewField()

    def __init__(self):
        Field.__check_setting_constraints(self.__class__)

    @staticmethod
    @util.log_error_with(logger)
    def __check_setting_constraints(cls: Type['Field']):
        """Assertions for checking constraints"""
        assert cls.config_keyword, "Field's \"config_keyword\" must be set"
        assert cls.expect_type, "Field's \"expect_type\" must be set"

        for keyword in cls.require_with:
            assert keyword not in cls.conflict_with, \
                f"Field [{cls}]: " \
                f"keyword [{keyword}] shows in both require_with and conflict_with"

        if cls.default_value:
            assert isinstance(cls.default_value, cls.expect_type), \
                f"Field [{cls}]: " \
                f"default value [{cls.default_value}] is not of expect type [{cls.expect_type}]"

    @classmethod
    def build(cls, config_value: Any):
        cls().__check_expect_type_constraints(config_value)
        return config_value

    @util.log_error_with(logger)
    def __check_expect_type_constraints(self, value):
        assert isinstance(value, self.expect_type), \
            f"Field [{self}]: " \
            f"given value [{value}] is not of expect type [{self.expect_type}]"

    def __str__(self):
        return self.config_keyword


class MapOption(Option):
    """
    Represent a map-like (object-like?) option, ``Action`` for example.

    You can define a map-like option only by directly setting class attributes.
    """
    logger = util.get_logger(__qualname__)

    # remain for child class to override
    config_keyword = "generic-map-option"
    valid_options: List[Type[Option]] = []

    def __init__(self, config_value: Dict[str, Any]):
        """
        :param config_value: the value corresponding to the "config_keyword" of this option
                in the parsed config dictionary.
        """
        self.raw_config = config_value
        exist_option_settings = self.__filter_exist_option_settings()
        self.__check_constraints_of(exist_option_settings)
        self.exist_options = self.__extract_exist_options_into_dict(exist_option_settings, config_value)

    @util.log_error_with(logger)
    def __filter_exist_option_settings(self) -> list[Type[Option]]:
        assert len(self.raw_config) > 0, \
            f"Option [{self}] must have at least one field."

        # check invalid fields
        exist_options = self.raw_config.keys()
        valid_config_keywords = [field.config_keyword for field in self.valid_options]
        for field in exist_options:
            assert field in valid_config_keywords, \
                f"Option [{self}]: [{field}] is not a valid field."

        # then shrink exist fields to valid fields
        return [field for field in self.valid_options
                if field.config_keyword in exist_options]

    @util.log_error_with(logger)
    def __check_constraints_of(self, exist_option_settings: List[Type[Option]]):
        """
        Check that all fields aren't violating the constraints themselves made.
        """

        # check (option) required fields
        for field in [field for field in self.valid_options if field.required]:
            # any subclass of required field or itself is exists
            # a field may don't have subclasses
            possible_subclasses = field.__subclasses__() if hasattr(field, "__subclasses__") else []
            assert [f for f in exist_option_settings if f in [field] + possible_subclasses], \
                f"Option [{self}] requires " \
                f"field [{field}] must be configured," \
                f"but it's absent."

        # check (exist fields) required fields
        for field in exist_option_settings:
            for required_field in field.require_with:
                assert required_field in exist_option_settings, \
                    f"Option [{self}]: " \
                    f"field [{field}] requires another field [{required_field}] must be configured, " \
                    f"but it's absent."

        # check fields conflict constraints
        for field in exist_option_settings:
            for required_field in field.conflict_with:
                assert required_field in exist_option_settings, \
                    f"Option [{self}]: " \
                    f"field [{field}] is conflict with another existing field [{required_field}]."

    @util.log_error_with(logger)
    def __extract_exist_options_into_dict(self, exist_option_settings: List[Type[Option]],
                                          raw_config: dict) -> Dict[str, Any]:
        result = {}
        for field in exist_option_settings:
            keyword = field.config_keyword
            result[keyword] = field.build(raw_config[keyword])

        return result

    @classmethod
    def build(cls, config_value: Dict[str, Any]):
        return cls(config_value)

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        return self.exist_options[item]


class ListOption(Option):
    """
    Represent a list-like option, ``RuleSet`` for example.

    You can define a list-like option only by directly setting class attributes.

    * Same fields can occur multiple times, which is different from ``AbstractMapOption``.
    * Fields' ``conflict_with``, ``required_with``, ``required`` constraints
      are not validated in this type of option.
    """

    logger = util.get_logger(__qualname__)

    # remain for child class to override
    config_keyword = "generic-list-option"
    valid_options: List[Type[Option]] = []

    def __init__(self, config_value: List[Dict[str, Any]]):
        """
        :param config_value: the value corresponding to the "config_keyword" of this option
                in the parsed config dictionary.
        """
        self.raw_config = config_value
        self.exist_options = self.__extract_exist_options_into_dict(self.__filter_exist_option_settings(),
                                                                    config_value)

    @util.log_error_with(logger)
    def __filter_exist_option_settings(self) -> List[Type[Option]]:
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
        valid_config_keywords = [field.config_keyword for field in self.valid_options]
        for field in exist_item_names:
            assert field in valid_config_keywords, \
                f"Option [{self}]: [{field}] is not a valid item."

        # then shrink exist fields to valid fields
        return [field for field in self.valid_options
                if field.config_keyword in exist_item_names]

    @util.log_error_with(logger)
    def __extract_exist_options_into_dict(self, exist_option_settings: List[Type[Option]],
                                          raw_config: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        result = defaultdict(list)
        for field in exist_option_settings:
            keyword = field.config_keyword
            # there may be multiple same items with the same config_keyword
            matched_values = list(filter(lambda x: x is not None, [item.get(keyword) for item in raw_config]))

            for value in matched_values:
                # add all same keyword items' value into one list, under keyword key.
                result[keyword].append(field.build(value))

        return result

    @classmethod
    def build(cls, config_value: List[Dict[str, Any]]):
        return cls(config_value)

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        return self.exist_options[item]
