from unittest import TestCase

from hamcrest import assert_that, equal_to, calling, raises

from puntgun.config.config_option import Field, MapOption, ListOption


class TestAbstractField(TestCase):
    def test_check_same_field_in_two_constraints(self):
        class TestField(Field):
            config_keyword = "test_field"
            expect_type = str
            conflict_with = ["same"]
            require_with = ["same"]
            is_init_by_class_attr = True

            def __init__(self):
                super().__init__()

        assert_that(calling(TestField).with_args(),
                    raises(AssertionError, pattern="both require_with and conflict_with"))

    def test_check_default_value_is_of_expect_type(self):
        assert_that(calling(Field.of).with_args("test_field", str, default_value=1),
                    raises(AssertionError, pattern="expect type"))

    def test_manually_call_expect_type_check_on_given_value(self):
        class TestField(Field):
            is_init_by_class_attr = True
            config_keyword = "test_field"
            expect_type = str

        assert_that(calling(TestField.build).with_args(1),
                    raises(AssertionError, pattern="expect type"))

    def test_normal_initialization_with_class_attr(self):
        class TestField(Field):
            is_init_by_class_attr = True
            config_keyword = "test_field"
            expect_type = str
            default_value = "default"
            conflict_with = ["c"]
            require_with = ["r"]
            required = True

        self.assert_normal_field_attrs(TestField())

    def test_normal_initialization_with_class_method(self):
        self.assert_normal_field_attrs(Field.of("test_field",
                                                str,
                                                default_value="default",
                                                conflict_with=["c"],
                                                require_with=["r"],
                                                required=True))

    @staticmethod
    def assert_normal_field_attrs(ins):
        assert_that(ins.config_keyword, equal_to("test_field"))
        assert_that(ins.expect_type, equal_to(str))
        assert_that(ins.default_value, equal_to("default"))
        assert_that(ins.conflict_with, equal_to(["c"]))
        assert_that(ins.require_with, equal_to(["r"]))
        assert_that(ins.required, equal_to(True))


class TestAbstractMapOption(TestCase):

    def test_check_exist_field_number_is_not_zero(self):
        assert_that(calling(MapOption).with_args({}),
                    raises(AssertionError, pattern="at least one field"))

    def test_check_field_validation(self):
        assert_that(calling(MapOption).with_args({'field': 'field'}),
                    raises(AssertionError, pattern="not a valid field"))

    def test_check_option_required_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field", str),
                             Field.of("required_field", str, required=True)]

        assert_that(calling(TestOption).with_args({"field": "value"}),
                    raises(AssertionError, pattern="required_field"))

    def test_check_exist_fields_required_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str, require_with=["field2"])]

        assert_that(calling(TestOption).with_args({"field1": "value"}),
                    raises(AssertionError, pattern="field2"))

    def test_check_exist_fields_conflict_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str, conflict_with=["field2"]),
                             Field.of("field2", str)]

        assert_that(calling(TestOption).with_args({"field1": "value", "field2": "value"}),
                    raises(AssertionError, pattern="conflict"))

    def test_field_extraction(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str)]

        assert_that(getattr(TestOption({"field1": "value"}), "field1"), equal_to("value"))


class TestAbstractListOption(TestCase):

    def test_check_exist_field_number_is_not_zero(self):
        assert_that(calling(ListOption).with_args({}),
                    raises(AssertionError, pattern="at least one field"))

    def test_check_field_validation(self):
        assert_that(calling(ListOption).with_args([{'field': 'field'}]),
                    raises(AssertionError, pattern="not a valid item"))

    def test_field_extraction(self):
        class TestOption(ListOption):
            valid_options = [Field.of("item1", str),
                             Field.of("item2", dict)]

        option = TestOption([{"item1": "t1"},
                             {"item1": "t2"},
                             {"item2": {"inner": "t3"}},
                             {"item2": {"inner": "t4"}}])
        assert_that(getattr(option, "item1"), equal_to(["t1", "t2"]))
        assert_that(getattr(option, "item2"), equal_to([{"inner": "t3"}, {"inner": "t4"}]))
