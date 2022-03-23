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

    # --- required setting attributes for overriding
    config_keyword: str = "generic-option"

    # --- optional setting attributes for overriding

    # For map option's inner field,
    # map option will check these constraint settings when initializing:

    # list of ``config_keyword`` that cannot co-exist with this option
    conflict_with: List[str] = []
    # list of ``config_keyword`` that must be present if this option present
    require_with: List[str] = []
    # if is required in parent option
    required: bool = False

    # For list option's inner field, list option will check these when initializing:

    # can exist at most once in the configuration,
    # fields like "name" can set this to True
    singleton: bool = False

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

    @staticmethod
    def expand_to_all_immediate_subclasses(parent_options: List[Type['Option']]) -> List[Type['Option']]:
        subclasses = [Option.expand_to_immediate_subclasses(o) for o in parent_options]
        return [o for lst in subclasses for o in lst]

    @staticmethod
    def expand_to_immediate_subclasses(cls: Type['Option']) -> List[Type['Option']]:
        return [cls] + Option.get_immediate_subclasses_of(cls)

    @staticmethod
    def get_all_immediate_subclasses_of(parent_options: List[Type['Option']]) -> List[Type['Option']]:
        exist_possible_subclass_settings = [Option.get_immediate_subclasses_of(o) for o in parent_options]
        return [o for lst in exist_possible_subclass_settings for o in lst]

    @staticmethod
    def get_immediate_subclasses_of(cls: Type['Option']) -> List[Type['Option']]:
        return cls.__subclasses__() if hasattr(cls, "__subclasses__") else []


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

    Keep in mind that if you define a field which has inner fields, remember to
    override ``build`` method to build inner fields on their own, because Field's
    ``build`` method only directly return the input primitive value.
    """

    logger = util.get_logger(__qualname__)

    # required settings for overriding
    config_keyword: str
    expect_type: type

    # optional settings for overriding
    default_value: object = None

    @classmethod
    def of(cls,
           config_keyword: str,
           expect_type: type,
           default_value: object = None,
           conflict_with: List[str] = None,
           require_with: List[str] = None,
           required: bool = False,
           singleton: bool = False) -> 'Field':
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

    * Same field can only appear at most once in configuration.
    * If you set some fields' ``required`` attribute,
      these fields must be present in the configuration,
      which means these fields' ``default_value`` will be ignored and not be automatically filled.
    * If you set some fields' ``require_with`` attribute, those required fields must
      be manually, explicitly set in configuration file.
    *
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
        # we'll get valid option types which exist in both self.valid_options and config_value,
        # and all of immediate subclasses of these options.
        exist_option_settings: List[Type[Option]] = self.__clac_exist_option_settings()
        self.__check_constraints_of(exist_option_settings)
        exist_option_settings = self.__add_non_conflict_default_options(exist_option_settings)
        self.exist_options = self.__extract_exist_options_into_dict(exist_option_settings, config_value)

    @util.log_error_with(logger)
    def __clac_exist_option_settings(self) -> list[Type[Option]]:
        """
        Filter out settings from valid_options which exist in config_value,
        and add the subclasses of these settings, then return.
        """
        assert len(self.raw_config) > 0, \
            f"Option [{self}] must have at least one field."

        # check invalid fields
        # must also consider the valid option's subclass's config_keyword is valid too
        valid_keywords = [o.config_keyword for o in Option.expand_to_all_immediate_subclasses(self.valid_options)]

        exist_keywords = self.raw_config.keys()
        for exist_field in exist_keywords:
            assert exist_field in valid_keywords, \
                f"Option [{self}]: [{exist_field}] is not a valid field."

        # then shrink exist fields to valid fields
        # and expand this list to include all subclasses of exist options
        return [field for field in Option.expand_to_all_immediate_subclasses(self.valid_options)
                if field.config_keyword in exist_keywords]

    @util.log_error_with(logger)
    def __check_constraints_of(self, exist_option_settings: List[Type[Option]]):
        """
        Check that all fields aren't violating the constraints themselves made.
        """

        # check (option) required fields
        for field in [field for field in self.valid_options if field.required]:
            # assert any required field or its subclass is exists in exist_option_settings
            assert [f for f in exist_option_settings
                    if f in Option.expand_to_immediate_subclasses(field)], \
                f"Option [{self}]: requires field [{field}] must be configured, but it's absent."

        exist_keywords = [field.config_keyword for field in exist_option_settings]

        # check (exist fields) required fields
        for field in exist_option_settings:
            for required_keyword in field.require_with:
                assert required_keyword in exist_keywords, \
                    f"Option [{self}]: " \
                    f"field [{field}] requires another field [{required_keyword}] must be configured, " \
                    f"but it's absent."

        # check fields conflict constraints
        for field in exist_option_settings:
            for conflict_field in field.conflict_with:
                assert conflict_field not in exist_keywords, \
                    f"Option [{self}]: " \
                    f"field [{field}] is conflict with another existing field [{conflict_field}]."

    def __add_non_conflict_default_options(self, exist_option_settings: List[Type[Option]]) -> List[Type[Option]]:
        """
        Add valid options which have default value if:
         1. Not conflict with any of existing options.
         2. Not already exist in existing options.

        As you can see in __init__ method, I put the constraint check before this method,
        so this method should not violate existing ``conflict_with`` constraints.
        """
        all_exist_fields_conflict_keywords = [k for f in exist_option_settings for k in f.conflict_with]
        all_exist_keywords = [f.config_keyword for f in exist_option_settings]

        # for all valid Field type options which have default value
        for field in [f for f in self.valid_options
                      if isinstance(f, Field) and (f.default_value is not None)]:
            keyword = field.config_keyword
            # if the field is not conflict with any of existing fields,
            # and not exist in existing fields, add it
            if (keyword not in all_exist_fields_conflict_keywords) \
                    and (keyword not in all_exist_keywords):
                exist_option_settings.append(field)

        return exist_option_settings

    @util.log_error_with(logger)
    def __extract_exist_options_into_dict(self, exist_option_settings: List[Type[Option]],
                                          raw_config: dict) -> Dict[str, Any]:
        result = {}
        for field in exist_option_settings:
            keyword = field.config_keyword

            # special logic for automatically building a default Field type.
            if isinstance(field, Field) and keyword not in raw_config:
                result[keyword] = field.build(field.default_value)
            elif keyword in raw_config:
                result[keyword] = field.build(raw_config.get(keyword))

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


class ListOption(Option):
    """
    Represent a list-like option, ``RuleSet`` for example.

    You can define a list-like option only by directly setting class attributes.

    * Same fields can occur multiple times, which is different from ``AbstractMapOption``.
    * Fields' ``conflict_with``, ``required_with``, ``required`` constraints
      are not allowed in this type of option.
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
        self.__check_list_option_constrains_on(self.valid_options)
        exist_option_settings = self.__clac_exist_option_settings()
        self.exist_options = self.__extract_exist_options_into_dict(exist_option_settings, config_value)
        self.__check_constraints_on_exist_options(exist_option_settings)

    @util.log_error_with(logger)
    def __clac_exist_option_settings(self) -> List[Type[Option]]:
        """
        Filter out settings from valid_options which exist in config_value.
        """
        assert len(self.raw_config) > 0, \
            f"Option [{self}] must have at least one field."

        # collect items' key in raw_config into a flatted list
        # for example:
        # raw_config = [{"item1": a-value}, {"item2": {"inner-field": a-value}]
        # exist_item_keywords = {"item1", "item2"}
        exist_keys_list = [item.keys() for item in self.raw_config]
        exist_item_keywords = set([key for keys in exist_keys_list for key in keys])

        # check invalid fields
        # must also consider the valid option's subclass's config_keyword is valid too
        valid_config_keywords = [o.config_keyword for o in
                                 Option.expand_to_all_immediate_subclasses(self.valid_options)]

        for exist_field in exist_item_keywords:
            assert exist_field in valid_config_keywords, \
                f"Option [{self}]: [{exist_field}] is not a valid field."

        # then shrink exist fields to valid fields
        # and expand this list to include all subclasses of exist options
        return [field for field in Option.expand_to_all_immediate_subclasses(self.valid_options)
                if field.config_keyword in exist_item_keywords]

    @util.log_error_with(logger)
    def __check_list_option_constrains_on(self, valid_options: List[Type[Option]]):
        """
        Fields' ``conflict_with``, ``required_with`` constraints
        are not allowed in this type of option.
        """

        for field in valid_options:
            assert not field.conflict_with, \
                f"Option [{self}]: field [{field}] has set \"conflict_with\" constraint, " \
                f"which is not allowed in list-like option."

            assert not field.require_with, \
                f"Option [{self}]: field [{field}] has set \"require_with\" constraint, " \
                f"which is not allowed in list-like option."

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

    @util.log_error_with(logger)
    def __check_constraints_on_exist_options(self, exist_option_settings: List[Type[Option]]):
        """
        Check exist options' ``singleton`` constraint.
        """

        # check (option) required fields
        for field in [field for field in self.valid_options if field.required]:
            # assert any required field or its subclass is exists in exist_option_settings
            possible_subclasses = field.__subclasses__() if hasattr(field, "__subclasses__") else []
            assert [f for f in exist_option_settings if f in [field] + possible_subclasses], \
                f"Option [{self}]: requires field [{field}] must be configured, but it's absent."

        # check "singleton" constraint
        for settings in [o for o in exist_option_settings if o.singleton]:
            item_number_of_this_type = len(self.exist_options[settings.config_keyword])
            assert item_number_of_this_type <= 1, \
                f"Option [{self}]: can only have at most one [{settings}] item, but found {item_number_of_this_type}."

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
