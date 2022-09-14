# Report File

Each run (with the `fire` command, particularly) of this tool will generate a corresponding report file
for the user to check later or as a data source for another process.

The content of the report file is in [JSON](https://www.json.org/json-en.html) format.
Due to the strict format restriction of JSON itself,
the content will only form the correct json format after the tool exits normally
(including exit after unexpected error caught).
If the tool exits abnormally the content will lack `]}` as a complementary part,
you can manually append `]}` to report file end to correct the format.

## Report File Content

The report contains three parts: information about the tool, information about this run,
and key events that occurred during the run.
All fields are generated before the first plan starts running,
except for the records field, which is continuously expanded at runtime.

| Field                     | Example                        | Description                                                                                            |
|---------------------------|--------------------------------|--------------------------------------------------------------------------------------------------------|
| `reference_documentation` | URL of this documentation      | JSON doesn't allow comments exist, so...                                                               |
| `tool_version`            | `"0.1.0"`                      | Current tool version, indicate what data structure this report is                                      |
| `generate_time`           | `"2022-01-01T00:00:00.000000"` | Report generating time in ISO 8601 format at UTC+0 timezone                                            |
| `plan_configuration`      | `[<plan config>,...]`          | [Plan configuration](https://boholder.github.io/puntgun/configuration/plan-configuration/) of this run |
| `plan_ids`                | `[<plan id>,...]`              | See description below                                                                                  |
| `records`                 | `[<record>,...]`               | See description below                                                                                  |

```json
{
  "reference_documentation": "https://boholder.github.io/puntgun/usage/report-file",
  "tool_version": "0.1.0",
  "generate_time": "2022-01-01T00:00:00.000000",
  "plan_configuration": [],
  "plan_ids": [],
  "records": []
}
```

!!! note
    If the tool exits normally, **the last item of `records` is empty**.
    It's a trade-off. JSON does not allow a comma to exist after the last item in the list,
    and the writing of the records file is delegated to the logger library
    (can not manually gain write access to report file and remove the extra comma).

### Plan Id

Relationship of plans and plan result records for de-redundancy purpose.
The plans are numbered according to their order in the configuration, starting from zero.
Records can indicate which plan it belonging to just with plan id.

```json
{
  "name": "plan name",
  "id": 0
}
```

### Record

The Record data is records of key events that occurred during the run.

```json
{
  "type": "the event type of this record",
  "data": {
    "information_of_this_record": "fields differ by event type"
  }
}
```

#### User Plan Result

When a candidate triggers filter rule set and actions are performed, a plan result record is generated
(only the action rule will actually make changes to the Twitter account,
so candidates that do not trigger the filter rule will not be recorded).
This record can be used to perform further operations, such as undo actions.

| Field in `data`                 | Example                           | Description                                                                                                 |
|---------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------------------------|
| `plan_id`                       | `0`                               | Indicate which plan it belonging to (see **Plan Id**)                                                       |
| `target`                        | `{...}`                           | Target user of action rules who triggered filter rule set                                                   |
| `target.id`                     | `2244994945`                      | User id, integer                                                                                            |
| `target.username`               | `"TwitterDev"`                    | User [handle](https://help.twitter.com/en/managing-your-account/change-twitter-handle)                      |
| `decisive_filter_rule`          | `{...}`                           | Which filter rule this user triggered                                                                       |
| `decisive_filter_rule.keyword`  | `"following"`                     | Triggered filter rule's keyword                                                                             |
| `decisive_filter_rule.value`    | `"less_than=100.0 more_than=1.0"` | Triggered filter rule's configuration in plan (just for human reading, can't parse the origin rule from it) |
| `action_rule_results`           | `[<action rule result>,...]`      | Execution result of each action rule                                                                        |
| `action_rule_results[].keyword` | `"block"`                         | One action rule's keyword                                                                                   |
| `action_rule_results[].value`   | `"..."`                           | One action rule's configuration                                                                             |
| `action_rule_results[].done`    | `true`                            | Whether this action rule is successfully executed                                                           |

Example: User **@TwitterDev** who was **blocked** for triggering **following count filter** rule.

```json
{
  "type": "user_plan_result",
  "data": {
    "plan_id": 0,
    "target": {
      "id": 2244994945,
      "username": "TwitterDev"
    },
    "decisive_filter_rule": {
      "keyword": "following",
      "value": "less_than=100.0 more_than=1.0"
    },
    "action_rule_results": [
      {
        "keyword": "block",
        "value": "",
        "done": true
      }
    ]
  }
}
```

#### Twitter API Error

This type of error is raised when a Twitter Development API query returns success status (http status code is 200),
but has an "errors" field in the response body, which indicates several "Partial error" occurs
and the result only contains what Twitter server can figure out.
This type of expected error does not cause the tool to exit.
Check this [Twitter official documentation](https://developer.twitter.com/en/support/twitter-api/error-troubleshooting#partial-errors) for more details.

We'll record these errors along with the invoked API and passed arguments,
so we can reproduce the error for improving the tool's logic or
feed another process with these errors for handling them.

| Field in `data`      | Example              | Description                                          |
|----------------------|----------------------|------------------------------------------------------|
| `query_func_name`    | `"get_users"`        | Which client function (Twitter API) is invoked       |
| `query_params`       | `{...}`              | All parameters passed to the function (to query API) |
| `errors`             | `[<api error>,...]`  | Errors returned by the Twitter platform              |
| `errors[].title`     | `"Not Found Error"`  | The error type defined by Twitter                    |
| `errors[].ref_url`   | `"https://..."`      | URL of Twitter documentation about this error        |
| `errors[].detail`    | `"..."`              | Human readable explanation about where is wrong      |
| `errors[].parameter` | `"usernames"`        | In which parameter does the error exist              |
| `errors[].value`     | `"UsErNoTExIst4242"` | The value that caused the error                      |

Example: **Resource Not Found** error is returned because
we request information from Twitter about a user who does not exist.

```json
{
  "type": "twitter_api_errors",
  "data": {
    "query_func_name": "get_users",
    "query_params": {
      "all_args_passed_to_the_client_function": "too long to show here"
    },
    "errors": [
      {
        "title": "Not Found Error",
        "ref_url": "https://api.twitter.com/2/problems/resource-not-found",
        "detail": "Could not find user with usernames: [UsErNoTExIst4242].",
        "parameter": "usernames",
        "value": "UsErNoTExIst4242"
      }
    ]
  }
}
```