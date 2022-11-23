# Custom Rules

This page describes knowledge about developing custom rules.

This tool is distributed as a standalone application, you cannot add rules by modifying the source code,
so first please follow [this documentation](https://boholder.github.io/puntgun/dev//development/contributing/#prepare-for-local-development)
to make your local development environment ready.

## Structure of rules source code

All rule-related code are stored under the [**rules**](https://github.com/boholder/puntgun/tree/main/puntgun/rules) module.
Depending on the type of entity that the rule operates, rules are divided into two categories:
user rules and tweet rules, which are stored in the corresponding **user** and **tweet** submodules.
The rules are further categorized by the purpose (source, filter, action...) and stored in different modules.

```text
[../puntgun/puntgun/rules ‹main*›] $ tree
.
├── __init__.py
├── config_parser.py
├── data.py
├── tweet
│   └── __init__.py
│   └── ...
└── user
    ├── __init__.py
    ├── action_rules.py
    ├── filter_rules.py
    ├── plan.py
    ├── rule_sets.py
    └── source_rules.py
```

## Inheritance structure of one example rule class

This project is developed using object-oriented design pattern,
and each rule exists in the form of a class structure.
Take example from inheritance diagram of "FollowerUserFilterRule":

```text
         ┌────────────► BaseModel
         │                   ▲
         │                   │
FieldsRequired ◄──┬───► FromConfig ◄────┐
                  │                     │
NumericRangeCheckingMixin ◄──┬───► UserFilterRule
                             │
                  FollowerUserFilterRule
```

| Class                       | Position                                                        | Purpose                                                                                          |
|-----------------------------|-----------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `FollowerUserFilterRule`    | `rules.user.filter_rules`                                       | User filter rule, for checking if user's follower count within given range                       |
| `NumericRangeCheckingMixin` | `rules.__init__`                                                | Reusable class which providing range checking function on numeric type value                     |
| `UserFilterRule`            | `rules.user.filter_rules`                                       | Rule type tagging for runtime rule classes loading                                               |
| `FieldsRequired`            | `rules.__init__`                                                | Contain an auto-validating function to check at least one field is provided with configuration   |
| `FromConfig`                | `rules.__init__`                                                | Indicate that one class can be parsed from loaded plan configuration (Python dictionary type)    |
| `BaseModel`                 | `pydantic` [(dependency)](https://pydantic-docs.helpmanual.io/) | Use this dependency to get easy instance initialization and field values validation capabilities |

We reuse the functions through the [mixin](https://stackoverflow.com/a/547714/11397457) practice,
so the final rule implementation will be simple (if it doesn't need additional logic):

```python
class FollowerUserFilterRule(NumericRangeCheckingMixin, UserFilterRule):
    """Check user's follower count."""

    # Inherits from [FromConfig].
    # Same-name in plan configuration, works like index of rule classes for configuration parsing,
    # let the configuration parser knows which rule class the configuration should be parsed to.
    _keyword: ClassVar[str] = "follower"

    # Overrides from [UserFilterRule].
    # Returns a wrapper DTO which contains itself (for latter reporting) and the filtering result.
    def __call__(self, user: User) -> RuleResult:
        #                       call NumericRangeCheckingMixin.compare()
        return RuleResult(self, super().compare(user.followers_count))
```

To create instances of this class:

```python
# 1. Normal way
# Two initializing parameters are inherited from [NumericRangeCheckingMixin]
r = FollowerUserFilterRule(less_than=100, more_than=1)

# 2. Parse from configuration 
# using BaseModel.parse_obj()
# https://pydantic-docs.helpmanual.io/usage/models/#helper-functions
#
# follower:
#   less_than: 100
#   more_than: 1
#
r = FollowerUserFilterRule.parse_obj({"follower": {"less_than": 100, "more_than": 1}})
```

In the rule class developing we use quite a few features provided by [pydantic](https://pydantic-docs.helpmanual.io/).
For the most part using **pydantic** speed-up our development, but it made the rule class has unknown behavior,
and implementing some simple features on the rule class (such as adding `_keyword` **class variable**)
required more time reading the documentation and experimenting. Take it as a trade-off.

## How the rule instances are generated from the plan configuration

Since the exact logic may change in the future, the description here does not involve specific implementation.
The description will be given with the following plan configuration.

```text
plans:
  - user_plan: Name #(3)
    from:
      - names: ['TwitterDev', 'TwitterAPI']
    that:
      - follower: #(4)
          less_than: 10
      - following:
          more_than: 100000000
    do:
      - block: {}
```

1. When the program starts, Python loads module [`rules.config_parser`](https://github.com/boholder/puntgun/blob/main/puntgun/rules/config_parser.py)
   into the namespace, the function call written in the global environment in module `rules.config_parser` are executed,
   loads all the rule classes (all classes inherited `FromConfig`, in fact, including plan classes, etc.) in module `rules` recursively in runtime
   (simply import all classes in this module will cause circular dependency problem, while move importing to other upper modules looks awkward).

2. Once the program takes the plan configuration (in Python dictionary type) from the full configuration,
   the program will recursively parse the plan configuration using the `ConfigParser` under the `rules.config_parser` module,
   converting it into a list of plan instances which contain rule instances.

3. The `ConfigParser` matching configuration and rules with the help of inheritance chain of rule classes and `_keyword` class variables of each rule class.
   The first step is to parse the root of the plan configuration (Python dictionary) i.e. the plan class,
   which inherit from the `Plan` parent class, so we know that all `Plan`'s subclasses are candidates for this step (and it is hard-coded).
   Now assuming that the root of first plan configuration is "user_plan",
   we'll look for the subclass which `_keyword`'s value is exactly `user_plan`,
   and it turns out to be the `UserPlan` class (if no answer occur, the `ConfigParser` will raise an error).
   Now the `ConfigParser` knows that it should try to pass the configuration to `UserPlan`'s constructor.

4. Inside `UserPlan`'s constructor, the `ConfigParser` is called again for parsing rules inside this plan instance.
   This time the `ConfigParser` is given `UserSourceRule`, `UserFilterRule`, `UserActionRule` as candidate transforming targets' parent classes,
   and the `ConfigParser` will again search for the same `_keyword` class variables.
   For example, `UserFilterRule` + `_keyword:follower` => `FollowerUserFilterRule`.

5. Repeating step 3 and step 4, whole plan configuration dictionary is transformed into plan instances.
   Possible construction and parsing errors are caught and collected outside the `ConfigParser` invoking logic.
   If no errors occur during the whole parsing process, the program will start executing the plan,
   otherwise the program will exit and print these errors to notify the user to fix them.