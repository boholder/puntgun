from unittest import TestCase

from hamcrest import assert_that, calling, equal_to, raises

from old.test import Field, ListOption, MapOption


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

        assert_that(
            calling(TestField).with_args(), raises(AssertionError, pattern="both require_with and conflict_with")
        )

    def test_check_default_value_is_of_expect_type(self):
        assert_that(
            calling(Field.of).with_args("test_field", str, default_value=1),
            raises(AssertionError, pattern="expect type"),
        )

    def test_manually_call_expect_type_check_on_given_value(self):
        class TestField(Field):
            is_init_by_class_attr = True
            config_keyword = "test_field"
            expect_type = str

        assert_that(calling(TestField.build).with_args(1), raises(AssertionError, pattern="expect type"))

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
        self.assert_normal_field_attrs(
            Field.of("test_field", str, default_value="default", conflict_with=["c"], require_with=["r"], required=True)
        )

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
        assert_that(calling(MapOption).with_args({}), raises(AssertionError, pattern="at least one field"))

    def test_raise_exception_for_invalid_config_keyword(self):
        # raise exception for invalid config_keyword
        assert_that(
            calling(MapOption).with_args({"field": "field"}), raises(AssertionError, pattern="not a valid field")
        )

    def test_check_valid_fields_subclass_as_valid(self):
        class TestField(Field):
            config_keyword = "test_field"
            expect_type = str

        class TestSubClassField(TestField):
            config_keyword = "test_sub_class_field"

        # suppress unused warning
        TestSubClassField.expect_type = str

        class TestOption(MapOption):
            config_keyword = "test_option"
            valid_options = [TestField]

        # must also consider the valid option's subclass's config_keyword is valid too
        option = TestOption({"test_sub_class_field": "s_field", "test_field": "field"})
        assert_that(option.test_field, equal_to("field"))
        assert_that(option.test_sub_class_field, equal_to("s_field"))

    def test_check_option_required_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field", str), Field.of("required_field", str, required=True)]

        assert_that(calling(TestOption).with_args({"field": "value"}), raises(AssertionError, pattern="required"))

    def test_check_exist_fields_required_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str, require_with=["field2"])]

        assert_that(calling(TestOption).with_args({"field1": "value"}), raises(AssertionError, pattern="field2"))

    def test_check_exist_fields_conflict_fields(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str, conflict_with=["field2"]), Field.of("field2", str)]

        assert_that(
            calling(TestOption).with_args({"field1": "value", "field2": "value"}),
            raises(AssertionError, pattern="conflict"),
        )

    def test_field_extraction(self):
        class TestOption(MapOption):
            valid_options = [Field.of("field1", str)]

        assert_that(TestOption({"field1": "value"}).field1, equal_to("value"))

    def test_auto_fill_default_field(self):
        class TestOption(MapOption):
            valid_options = [Field.of("p", str), Field.of("d", str, default_value="default_value")]

        assert_that(TestOption({"p": "value"}).d, equal_to("default_value"))

    def test_do_not_auto_fill_default_field_if_conflict(self):
        class TestOption(MapOption):
            valid_options = [Field.of("p", str, conflict_with=["d"]), Field.of("d", str, default_value="default_value")]

        assert_that(hasattr(TestOption({"p": "value"}), "d"), equal_to(False))


class TestAbstractListOption(TestCase):
    def test_check_exist_field_number_is_not_zero(self):
        assert_that(calling(ListOption).with_args({}), raises(AssertionError, pattern="at least one field"))

    def test_raise_exception_for_invalid_config_keyword(self):
        # raise exception for invalid config_keyword
        assert_that(
            calling(MapOption).with_args({"field": "field"}), raises(AssertionError, pattern="not a valid field")
        )

    def test_check_valid_fields_subclass_as_valid(self):
        class TestField(Field):
            config_keyword = "test_field"
            expect_type = str

        class TestSubClassField(TestField):
            config_keyword = "test_sub_class_field"

        TestSubClassField.expect_type = str

        class TestOption(MapOption):
            valid_options = [TestField]

        # must also consider the valid option's subclass's config_keyword is valid too
        option = TestOption({"test_field": "field", "test_sub_class_field": "s_field"})
        assert_that(option.test_field, equal_to("field"))
        assert_that(option.test_sub_class_field, equal_to("s_field"))

    def test_check_required_field_constraint(self):
        class TestOption(ListOption):
            valid_options = [Field.of("f1", str, required=True), Field.of("f2", str)]

        assert_that(calling(TestOption).with_args([{"f2": "value"}]), raises(AssertionError, pattern="required"))

    def test_check_valid_options_not_allowed_constraints(self):
        """these three constraints are not allowed in list option"""

        class TestOption(ListOption):
            valid_options = [Field.of("f2", str, require_with=["f1"])]

        assert_that(calling(TestOption).with_args([{"f2": "value"}]), raises(AssertionError, pattern="require_with"))

        class TestOption2(ListOption):
            valid_options = [Field.of("f3", str, conflict_with=["f1"])]

        assert_that(calling(TestOption2).with_args([{"f3": "value"}]), raises(AssertionError, pattern="conflict_with"))

    def test_check_fields_can_exist_at_most_once_constraint(self):
        class TestOption(ListOption):
            valid_options = [Field.of("f3", str, singleton=True)]

        assert_that(
            calling(TestOption).with_args([{"f3": "value"}, {"f3": "value"}]),
            raises(AssertionError, pattern="at most one"),
        )

    def test_field_extraction(self):
        class TestOption(ListOption):
            valid_options = [Field.of("item1", str), Field.of("item2", dict)]

        option = TestOption([{"item1": "t1"}, {"item1": "t2"}, {"item2": {"inner": "t3"}}, {"item2": {"inner": "t4"}}])
        assert_that(option.item1, equal_to(["t1", "t2"]))
        assert_that(option.item2, equal_to([{"inner": "t3"}, {"inner": "t4"}]))
