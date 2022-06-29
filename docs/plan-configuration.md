---
title: Plan Configuration
nav_order: 2
---

# Plan Configuration

This page describes configurations for plan, one run of the tool -
setting processing rules through the configuration file (also referred to as Plan).

Some rules contain fields that worth a paragraph to explain,
but if we put all the details into this single page, it will be too long.
So here we just list all the available rules with a brief description,
and leave the details in other corresponding pages.

The example configuration is written in yaml format
(you may want to learn about [yaml's syntax](https://yaml.org/)),
but you can also use [other supported formats](https://www.dynaconf.com/settings_files/#supported-formats)
like .toml, .ini, .json. In this page we'll use yaml format.

Currently, the tool only support processing Twitter accounts ("user_plan") (blocking accounts for example),
but we left a place for processing tweets in the future (like deleting embarrassing past tweets).

## How to write a plan

One plan contains at most three types of rules, together they construct a processing pipeline:

1. **Source rules** - Where to get source candidates (Twitter accounts or tweets)?
2. **Filter rules** - (optional) What type(s) of candidates should be chosen from the source to take actions?
3. **Action rules** - What actions to take on candidates that trigger filter rules?

One plan configuration file can contain several plans (under field `plans`).
We tried to make plan configuration look natural, one of the simplest is:

```yaml
plans:
  # Name (explain) of this plan
  - user_plan: Do block on three users depend on their follower number
    from:
      # '@Alice', '@Bob' and '@Charlie'
      - names: [ 'Alice', 'Bob', 'Charlie' ]
    that:
      # who has less than 10 (0~9) followers
      - follower:
          less_than: 10
    do:
      # block them
      - block
```

The syntax structure is:

```yaml
plans:
  [ - <plan> ]

# <plan>
<plan_type>: <string>
from: [ <source_rule> ]
that: [ <filter_rule> ]
do: [ <action_rule> ]
```

As the filter rule is optional, we can directly take action on every user in the source:

```yaml
plans:
  - user_plan: Again
    from:
      - names: [ 'Alice', 'Bob', 'Charlie' ]
    do:
      - block
```

## How plans are executed

Plans are executed in the order they are defined in the configuration file,
one by one i.e. in parallel (so plans won't compete for limited API invocation resources).

For a single plan:

1. The source rules are executed first, results are default union together as one final set.
2. Users in the source set are judged by a chain of filter rules,
   results are default ORed together, so if any filter rule is matched,
   that user will be considered as the target.
3. The action rules are executed on the target set of users,
   in the order they are defined in the configuration file.

In natural language, the summary is:
Run **all** `action_rule`s on targets from **any** `source_rule`  that trigger **any** `filter_rule`.

You can arrange more complex but flexible executing orders by nesting rule sets below.

## Rule Sets

any all

## User source rules

### ids

```yaml
from:
  - ids: [ 123456789, 987654321 ]
```

Specify users with a list of user id as source.
Where to get them? Somehow you can get them from another automatic twitter processing tool I guess.
If you want to get one user's id manually, maybe you can find it in the [Twitter Web Client](https://twitter.com)'s
[XHRs](https://developer.mozilla.org/en_US/docs/Web/API/XMLHttpRequest) via browser developer console?
And there are some online websites that allows you to get the id of a user with its name,
google 'Twitter user id' and you'll find them.

### names

```yaml
from:
  - names: [ 'Alice', 'Bob', 'Charlie' ]
```

Specify users with a list of [username](https://help.twitter.com/en/managing-your-account/change-twitter-handle)
(also called "handle" by Twitter) as source.
Usernames are easy to get, so this rule is pretty good for your first try with a handful usernames.
Like the user id, manually typing down or parsing amount of usernames is awkward and not recommended.

## User filter rules

### follower

```yaml
that:
  - follower:
      less_than: 10
      more_than: 5

  - follower-less-than: 10
```

Follower count itself doesn't tell much, but it's good to have a rule aiming at it.
The `follower-less-than` is a shortcut for `follower: { less_than: n }`.

### following

```yaml
that:
  - following:
      less_than: 10
      more_than: 5

  - following-more-than: 5
```

And... the following rule.

## User action rules

### block

```yaml
do:
  - block:
      block_already_followed: true
```

Block users that trigger the filter rules.