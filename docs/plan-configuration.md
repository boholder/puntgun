---
title: Plan Configuration
nav_order: 2
---

# Plan Configuration

This page describes configurations for one run of the tool, the core function of this tool - setting processing rules through the configuration file (also referred to as Plan).

The example configuration is written in yaml format (you may want to learn about [yaml's syntax](https://yaml.org/)), but you can also use [other supported formats](https://www.dynaconf.com/settings_files/#supported-formats) like .toml, .ini, .json. In this page we'll use yaml format.

One plan configuration file can only contain one pipeline. A complete plan configuration contains at most three types of rules, they construct a processing pipeline:

1. **Source rules** - Where to get source candidates (Twitter accounts or tweets)?
2. **Filter rules** - (optional) What type(s) of candidates should be chosen from the source to take actions?
3. **Action rules** - What actions to take on candidates that trigger filter rules?

We tried to make plan configurations look natural, one of the simplest is:

```yaml
# this process line is for Twitter accounts
users:
  # user source rule
  from:
    # '@Alice', '@Bob' and '@Charlie'
    - name: [ 'Alice', 'Bob', 'Charlie' ]
  # user filter rule
  that:
    - follower:
        less_that: 10
  # user action rule 
  do:
    - block

# <process type>:
#   from: <source rules>
#   that: <filter rules>
#   do: <action rules>
```

Currently, the tool only support processing Twitter accounts (blocking accounts for example), but we left a place for processing tweets in the future (like deleting embarrassing past tweets).

## User rules

### User Action rules

