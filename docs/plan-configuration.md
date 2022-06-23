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
    - names: [ 'Alice', 'Bob', 'Charlie' ]
  # user filter rule
  that:
    - follower:
        less_than: 10
  # user action rule 
  do:
    - block

# <process type>:
#   from: <source rules>
#   that: <filter rules>
#   do: <action rules>
```

Currently, the tool only support processing Twitter accounts (blocking accounts for example), but we left a place for processing tweets in the future (like deleting embarrassing past tweets).

Some rules contain fields that worth a paragraph to explain, but if we put all the details into this single page, it will be too long. So here we just list all the available rules with a brief description, and leave the details in other corresponding pages.

## User rules

### User source rules

#### names

```yaml
users:
  from:
    - names: [ 'Alice', 'Bob', 'Charlie' ]
```

Specify users in a list of [username](https://help.twitter.com/en/managing-your-account/change-twitter-handle) (also called "handle" by Twitter) as source. Usernames are easy to get, so this rule is pretty good for your first try with a handful usernames. Manually typing down or parsing amount of usernames is awkward and not recommended.

### User filter rules

#### follower

```yaml
users:
  that:
    - follower:
        less_than: 10
        more_than: 5
```

Follower count itself doesn't tell much, but it's good to have a filter rule to set the absolute range.

### User action rules