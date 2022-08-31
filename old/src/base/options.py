from collections import defaultdict
from typing import List, Dict, Any, Type

import util


class Option(object):
    """
    Base class of all option classes.
    Option classes are responsible for checking the validity of user-written
    configuration amd programming part of option settings,
    then extracting field values from configuration into attributes,
    for further judgement use.
    """

    # --- required setting attributes for overriding ---
    config_keyword: str = "generic_option"

    # --- optional setting attributes for overriding ---

    # Options can be nested into each other, so there are some class attributes
    # that describe one option's relationship between other brother options and
    # between its parent option.

    # For map option's inner fields,
    # parent map option will check these constraint settings when initializing:

    # list of ``config_keyword`` that cannot co-exist with this option
    conflict_with: List[str] = []
    # list of ``config_keyword`` that must be present if this option present
    require_with: List[str] = []
    # if is required in parent option
    required: bool = False

    # For list option's inner fields, list option will check these when initializing:

    # Indicate that this field can exist at most once in the configuration,
    # for example, "name" field (custom name for one option) can set this to True.
    # It's weird to have this constraint, but we need it.
    singleton: bool = False

    @classmethod
    def build(cls, config_value):
        """
        Let parent option (:class:`MapOption` and :class:`ListOption`, which has inner fields)
        can automatically initialize inner fields without knowing details.

        For now, this method return wrapped instance (:class:`NestableOption`)
        or directly return the input primitive value (:class:`Field`).

        But parent options should know exactly what type (instance, or primitive value)
        inner fields will be and how to use them.
        """
        raise NotImplementedError

    @staticmethod
    def self_and_immediate_subclasses_list(parent_options: List[Type["Option"]]) -> List[Type["Option"]]:
        subclasses = [Option.self_and_immediate_subclasses_of(o) for o in parent_options]
        return [o for lst in subclasses for o in lst]

    @staticmethod
    def self_and_immediate_subclasses_of(cls: Type["Option"]) -> List[Type["Option"]]:
        return [cls] + Option.immediate_subclasses_of(cls)

    @staticmethod
    def immediate_subclasses_of(cls: Type["Option"]) -> List[Type["Option"]]:
        return cls.__subclasses__() if hasattr(cls, "__subclasses__") else []


class Field(Option):
    """
    Option that takes only a primitive value to initialize,
    it may be just acting as a configuration checker,
    or it can have more complex logic.

    You can define a custom field by inheriting this class and override attributes,
    or using ``of`` metaclass method to generate one.

    If one field have complex logic, I recommend defining a class for it,
    and override the build method to return instance instead of raw input value.

    If one field is just holding a primitive value, using ``of`` method is more convenient.
    """

    logger = util.get_logger(__qualname__)

    # --- required setting attributes for overriding ---
    expect_type: type

    # --- optional setting attributes for overriding ---
    default_value: object = None

    @classmethod
    def of(
        cls,
        config_keyword: str,
        expect_type: type,
        default_value: object = None,
        conflict_with: List[str] = None,
        require_with: List[str] = None,
        required: bool = False,
        singleton: bool = False,
    ) -> "Field":
        """
        Define a field type directly by class method.

        :param singleton: can exist at most once in the configuration, fields like "name" can set this to True
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
        NewField.singleton = singleton

        return NewField()

    def __init__(self):
        self.__check_setting_constraints()

    @util.log_error_with(logger)
    def __check_setting_constraints(self):
        """Assertions for checking constraints set by class attributes."""

        assert self.config_keyword, 'Field\'s "config_keyword" must be set'
        assert self.expect_type, 'Field\'s "expect_type" must be set'

        for keyword in self.require_with:
            assert (
                keyword not in self.conflict_with
            ), f"Field [{self}]: keyword [{keyword}] shows in both require_with and conflict_with"

        if self.default_value:
            assert isinstance(
                self.default_value, self.expect_type
            ), f"Field [{self}]: default value [{self.default_value}] is not of expect type [{self.expect_type}]"

    @classmethod
    @util.log_error_with(logger)
    def build(cls, config_value: Any):
        # check input's type
        assert isinstance(
            config_value, cls.expect_type
        ), f"Field [{cls}]: given value [{config_value}] is not of expect type [{cls.expect_type}]"

        # then directly return the input
        return config_value

    def __str__(self):
        return self.config_keyword


class NestableOption(Option):
    """Option that can have inner fields."""

    # --- required setting attributes for overriding ---
    valid_options: List[Type[Option]] = []

    @classmethod
    def build(cls, config_value):
        raise NotImplementedError


class MapOption(NestableOption):
    """
    Represent a map-like (object-like?) option.

    * Same field can appear at most once in configuration.

    * If you set some fields' ``required`` attribute,
      these fields must be present in the configuration,
      i.e. they can't be automatically filled with ``default_value`` if absent.

    * If you set some fields' ``require_with`` attribute, those required fields must
      be present in the configuration.
    """

    logger = util.get_logger(__qualname__)

    def __init__(self, config_value: Dict[str, Any]):
        """
        :param config_value: the value corresponding to the "config_keyword" of this option
                in the parsed option dictionary.
        """

        self.raw_config = config_value

        exist_option_types: List[Type[Option]] = self.__find_options_exist_in_configuration()
        exist_option_types = self.__add_non_conflict_default_options(exist_option_types)
        self.__check_constraints_of(exist_option_types)

        self.exist_options = self.__extract_exist_options(exist_option_types)

    @util.log_error_with(logger)
    def __find_options_exist_in_configuration(self) -> list[Type[Option]]:

        assert len(self.raw_config) > 0, f"Option [{self}] must have at least one field."

        # must also consider the valid option's subclass is valid too
        valid_option_types = Option.self_and_immediate_subclasses_list(self.valid_options)

        valid_keywords = [o.config_keyword for o in valid_option_types]
        exist_keywords = self.raw_config.keys()

        for k in exist_keywords:
            assert k in valid_keywords, f"Option [{self}]: [{k}] is not a valid field."

        # return these exist options' type
        return [t for t in valid_option_types if t.config_keyword in exist_keywords]

    @util.log_error_with(logger)
    def __check_constraints_of(self, exist_types: List[Type[Option]]):
        """
        Check that all fields aren't violating the constraints
        they made in their attributes.
        """

        # check option required fields
        for required_field in [field for field in self.valid_options if field.required]:
            assert [f for f in exist_types if f in Option.self_and_immediate_subclasses_of(required_field)], (
                f"Option [{self}]: field [{required_field}] is required," f" but absent in configuration."
            )

        exist_keywords = [field.config_keyword for field in exist_types]

        for field in exist_types:
            # check exist fields required fields constraints
            for required_kwd in field.require_with:
                assert required_kwd in exist_keywords, (
                    f"Option [{self}]: field [{field}] requires another field [{required_kwd}],"
                    f" but absent in configuration."
                )

            # check exist fields conflict constraints
            for conflict_kwd in field.conflict_with:
                assert conflict_kwd not in exist_keywords, (
                    f"Option [{self}]: " f"field [{field}] is conflict with another existing field [{conflict_kwd}]."
                )

    def __add_non_conflict_default_options(self, exist_option_settings: List[Type[Option]]) -> List[Type[Option]]:
        """
        Add valid options which have default value if:
            1. Not conflict with any of existing options.
            2. Not already exist in existing options.
        """

        all_exist_keywords = [f.config_keyword for f in exist_option_settings]
        all_exist_fields_conflict_keywords = [k for f in exist_option_settings for k in f.conflict_with]

        # for all valid field types which have default value
        for field in [f for f in self.valid_options if isinstance(f, Field) and (f.default_value is not None)]:

            keyword = field.config_keyword

            # if the field is not conflict with any of existing fields,
            # and not exist in existing fields, add it
            if (keyword not in all_exist_fields_conflict_keywords) and (keyword not in all_exist_keywords):
                exist_option_settings.append(field)

        return exist_option_settings

    @util.log_error_with(logger)
    def __extract_exist_options(self, exist_option_settings: List[Type[Option]]) -> Dict[str, Any]:

        result = {}

        for field in exist_option_settings:
            keyword = field.config_keyword

            # special logic for automatically building a default Field type,
            # while it's absent in configuration
            if isinstance(field, Field) and keyword not in self.raw_config:
                result[keyword] = field.build(field.default_value)

            elif keyword in self.raw_config:
                result[keyword] = field.build(self.raw_config.get(keyword))

        return result

    @classmethod
    def build(cls, config_value: Dict[str, Any]):
        return cls(config_value)

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        if item in self.exist_options:
            return self.exist_options[item]
        else:
            raise AttributeError(f"Option [{self}]: has no attribute [{item}].")


class ListOption(NestableOption):
    """
    Represent a list-like option.

    * Same fields can occur multiple times by default
      (but can be restricted to at most once).

    * Fields' ``conflict_with``, ``required_with`` constraints
      are not allowed in this type of option.
    """

    logger = util.get_logger(__qualname__)

    def __init__(self, config_value: List[Dict[str, Any]]):
        """
        :param config_value: the value corresponding to the "config_keyword" of this option
                in the parsed option dictionary.
        """
        # check programmatic settings before parsing
        self.__check_invalid_constrain_settings_of_valid_options()

        self.raw_config = config_value
        exist_option_types = self.__find_options_exist_in_configuration()
        self.exist_options = self.__extract_exist_options(exist_option_types)

        # this method need to be called after exist_options is initialized,
        # so that it can check fields' ``singleton`` constraints
        self.__check_constraints_of(exist_option_types)

    @util.log_error_with(logger)
    def __check_invalid_constrain_settings_of_valid_options(self):
        """
        Field ``conflict_with``, ``required_with`` constraints
        are not allowed in this type of option.
        """

        for field in self.valid_options:
            assert not field.conflict_with, (
                f'Option [{self}]: field [{field}] has set "conflict_with" constraint, '
                f"which is not allowed in list-like option."
            )

            assert not field.require_with, (
                f'Option [{self}]: field [{field}] has set "require_with" constraint, '
                f"which is not allowed in list-like option."
            )

    @util.log_error_with(logger)
    def __find_options_exist_in_configuration(self) -> List[Type[Option]]:

        assert len(self.raw_config) > 0, f"Option [{self}] must have at least one field."

        # collect items' key in raw_config into a flatted list
        # for example:
        # raw_config = [{"item1": a_value}, {"item2": {"inner_field": a_value}]
        # exist_item_keywords = {"item1", "item2"}
        exist_keys_list = [item.keys() for item in self.raw_config]
        exist_item_keywords = set([k for keys in exist_keys_list for k in keys])

        # must also consider the valid option's subclass's config_keyword is valid too
        valid_option_types = Option.self_and_immediate_subclasses_list(self.valid_options)

        valid_config_keywords = [o.config_keyword for o in valid_option_types]

        for exist_field in exist_item_keywords:
            assert exist_field in valid_config_keywords, f"Option [{self}]: [{exist_field}] is not a valid field."

        # return these exist options' type
        return [field for field in valid_option_types if field.config_keyword in exist_item_keywords]

    @util.log_error_with(logger)
    def __extract_exist_options(self, exist_option_settings: List[Type[Option]]) -> Dict[str, List[Any]]:
        result = defaultdict(list)
        for field in exist_option_settings:
            keyword = field.config_keyword
            # there may be multiple same items with the same config_keyword
            matched_values = list(filter(lambda x: x is not None, [item.get(keyword) for item in self.raw_config]))

            # add all same keyword items' value into one list, under keyword key.
            for value in matched_values:
                result[keyword].append(field.build(value))

        return result

    @util.log_error_with(logger)
    def __check_constraints_of(self, exist_option_settings: List[Type[Option]]):
        """
        Check exist options' ``required`` and ``singleton`` constraint.
        """

        # check option required fields
        for required_field in [field for field in self.valid_options if field.required]:
            # assert any required field or its subclass is exists in exist_option_settings
            assert [f for f in exist_option_settings if f in Option.self_and_immediate_subclasses_of(required_field)], (
                f"Option [{self}]: field [{required_field}] is required," f" but absent in configuration."
            )

        # check "singleton" constraint
        for settings in [o for o in exist_option_settings if o.singleton]:
            value_number_of_this_type = len(self.exist_options[settings.config_keyword])
            assert value_number_of_this_type <= 1, (
                f"Option [{self}]: can only have at most one [{settings}] item,"
                f" but found {value_number_of_this_type}."
            )

    @classmethod
    def build(cls, config_value: List[Dict[str, Any]]):
        return cls(config_value)

    def __str__(self):
        return self.config_keyword

    def __getattr__(self, item):
        if item in self.exist_options:
            return self.exist_options[item]
        else:
            raise AttributeError(f"Option [{self}]: has no attribute [{item}].")
