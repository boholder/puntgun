# Configuration Manual

Configuration file is written in YAML format.
Your can refer [official documentation](https://yaml.org/) for the syntax.
For character escaping content, read [this part](https://pyyaml.org/wiki/PyYAMLDocumentation#scalars).

## Index

* [Script Behavior Settings](#script-behavior-settings)
    * [manually_confirm](#manually_confirm)
* [Action](#action)
* [Rules](#rule-description)
    * [User Selecting Rule](#user-selecting-rule)
        * [who](#who)
        * [id_are](#id_are)
        * [username_are](#username_are)
        * [are_my_follower](#are_my_follower)
        * [hit_search_results_of](#hit_search_results_of)
        * [agree_with_tweet](#agree_with_tweet)
    * [Filter Rule](#filter-rule)
        * [search](#search)
        * [user-*](#user_something)
            * [user_created](#user_created)
            * [user_texts_match](#user_texts_match)
            * [user_follower](#user_follower)
            * [user_following](#user_following)
            * [user_foer_foing_ratio](#user_foer_foing_ratio)
            * [user_tweet_count](#user_tweet_count)
            * [user_recent_speaking_ratio](#user_recent_speaking_ratio)
        * [last_active_time](#last_active_time)
    * [Let_me_check Rule](#let_me_check-rule)
        * [user_info](#user_info)
        * [recent_tweets](#recent_tweets)
        * [recent_replies](#recent_replies)
        * [recent_likes](#recent_likes)
* [Rule Set](#rule-set)
    * [all_of](#all_of)
    * [any_of](#any_of)
    * [weight_of](#weight_of)
* [Reusable Mechanism](#reusable-mechanism)

## Script Behavior Settings

All the script behavior settings should be put directly under the root of configuration file.

### manually_confirm

| field | value |
|:--:|:-----:|
| possible | `true` `false`|
| default if absent | `false` |

```yaml
manually_confirm: true
```

Decide if you want to let the script executes blocking action automatically
when block/mute decision of one user is ready,
or confirm it manually by interacting with terminal.

Note that the rate limit of block/mute API is **50 requests per 15 minutes**, pretty slow.
So do it automatically is recommended.

There are some rules will override this setting
and force user to confirm manually on the terminal.

## Action

Currently, there are only one action: block.
One action can have a list of [User Selecting Rule](#user-selecting-rule)s,
represent multiple groups of target users.

[Block API](https://developer.twitter.com/en/docs/twitter-api/users/blocks/api-reference/post-users-user_id-blocking)
rate of limit is **50 requests per 15 minutes**.

```yaml
block:
  - users:
      who:
        id_are: [ "12345678", "87654321" ]
  - users:
      who:
        username_are: [ "Twitter", "TwitterAPI" ]
```

## Rule Description

The rules work together like:

1. An [Action](#action) can have multiple [User Selecting Rule](#user-selecting-rule)s,
   we've mentioned above.

2. A [User Selecting Rule](#user-selecting-rule) specifies a group of users,
   it's the start of a processing stream.

3. An optional [Rule Set](#rule-set) contains multiple rigid [Filter Rule](#filter-rule)s
   and nested [Rule Set](#rule-set), driven by relationships between various data
   (e.g. `follower_less_than: {a number}`).
   One [User Selecting Rule](#user-selecting-rule) can have 0~1 [Rule Set](#rule-set) as further filter chain.
   [User Selecting Rule](#user-selecting-rule)'s result user group is passed through these filters,
   and users who satisfy the conditions will be blocked/muted.

4. An optional [Let_me_check Rule](#let_me_check-rule) allows you to check for
   users who didn't trigger the filter rule by your self and manually decide their fate.

Here this is a sample complete example:

```yaml
block:
  - users:
      who:
        id_are: [ "12345678", "87654321" ]
      all_of:
        - follower_less_than: 10
      let_me_check: [ "user_info" ]
```

## User Selecting Rule

This type of rules can be put directly under the [action](#action) field,
each of which can specify a group of potential target user with [who](#who) field.

If there is no [Rule Set](#rule-set) or [Let_me_check Rule](#let_me_check-rule)
under one "users" rule, perform the action on all users in the [who](#who)'s result group.

```yaml
block:
  - users:
      who: # required
        id_are: [ "12345678", "87654321" ]
      all_of: # optional
        - follower_less_than: 10
      let_me_check: [ "user_info" ] # optional
```

### who

| field | value |
|:--:|:-----:|
| possible | `id_are` `username_are` `are_my_follower` `hit_search_results_of` `agree_with_tweet`|
| [id_are](#id_are) | a list of user id |
| [username_are](#username_are) | a list of username |
| [are_my_follower](#are_my_follower) | inner fields |
| [hit_search_results_of](#hit_search_results_of) | a list of [search](#search) rules |
| [agree_with_tweet](#agree_with_tweet) | inner fields |

This is a required field under [User Selecting Rule](#user-selecting-rule),
indicating user selection metric type and value.

### id_are

Specify a list of user id.

Somehow you get them from another automatic_twitter_process source,
because these users' id are not displayed by the client normally,
although this field is positioned like the primary key in every user API queries.

If you want to get one user's id manually, maybe you can get it in [Twitter Web Client](https://twitter.com)'s
[XHRs](https://developer.mozilla.org/en_US/docs/Web/API/XMLHttpRequest) via browser dev tools?
BTW I found [a website](https://commentpicker.com/twitter_id.php)
where you can query the Twitter user id with
[username](https://help.twitter.com/en/managing_your_account/change_twitter_handle) e.g. "@Twitter".

But if you insist to manually type them into configuration file,
I suggest you to straightly view and block these users via a client,
that's faster (smartphone client is more convenient than web client on doing this job).

```yaml
users:
  who:
    id_are: [ "12345678", "87654321" ]
```

### username_are

Specify a list of [username](https://help.twitter.com/en/managing-your-account/change-twitter-handle) (also called "
handle").

It's easy to get it, just remove the first "@" symbol.
But same as above, manually typing down them is awkward, not recommended.

```yaml
users:
  who:
    username_are: [ "Twitter", "TwitterAPI" ]
```

### are_my_follower

| field | value |
|:--:|:-----:|
| possible | `last` |
| `last` | the last N number of (newest) followers |

Select users from your followers.

Currently, there are only one config: specify the number of newcomers.
(I'm sad that I can't give you some configs like "followed_me_after: time",
because I haven't found a way to get this information from the API.)

```yaml
users:
  who:
    are_my_follower:
      last: 100
```

### hit_search_results_of

Specify users that appear in (any of) a set of tweet search results.
Check [search](#search) rule for more details.

```yaml
users:
  who:
    hit_search_results_of:
      - search_query: 'tweet_query_string-1'
      - search_query: 'tweet_query_string-2'
```

### agree_with_tweet

| field | value |
|:--:|:-----:|
| possible | `id`, or a [search](#search) rule |
| `id` | the tweet id, **string** |
| [search](#search) | inner fields |

Specify users who liked or retweeted (except "Quote Tweet") one specific tweet.
There are more than one way to indicate that tweet,
the script will **choose the first**.

Please note that the "like"/"retweet" action itself does not just mean
that user agrees with the content of the tweet.
So be careful when using this rule,
or consider manually checking with [Let_me_check Rule](#let_me_check-rule).

The [tweet id](https://developer.twitter.com/en/docs/twitter-ids)
can be found in that tweet's share link, for example,
in `https://twitter.com/{username}/status/{12345678}` the tweet id is "12345678".
These days the length of tweet id is 64-bit (8 bytes, a `long` type)
accounting to official documentation.

If you choose the search rule:

* Please try it manually on client before running script,
  **make sure only that one tweet hit** your query criteria.
  The script will blindly pick the first one from query response.

* And please make sure the script can search that tweet (7-days_time_limit etc.).
  If the script can't find it via searching, you can try to find that tweet's id,
  and use the `id` field instead.

```yaml
users:
  who:
    agree_with_tweet:
      id: "12345678"
      # search_query: 'tweet_query_string'
```

## Filter Rule

This type of rules can't exist independently, and must be put under a [rule set](#rule-set).
Though they can't indicate user group from nothing,
but they can help to further specify the behavior of the target user,
helping the script to make the final decision.

```yaml
users:
  who:
    id_are: [ "12345678", "87654321" ]
  # this is a option set
  any_of:
    # these two are filter rules
    - search_query: 'tweet_query_string-1'
    - user_created:
        after: '2022-01-01'
```

### search

| field | value |
|:--:|:-----:|
| possible | `name` `count` `query` |
| `name` | optional, custom name of this search rule, string |
| `count` | optional, number of tweets to be searched, integer, default 100 |
| `query` | required, a tweet query, string |

#### basic

This rule is basically
maps [the Twitter Tweet Search API](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent)
.
According to official documentation, the query length is limited up to 512 characters,
and can only search the last 7 days of tweets with Essential Twitter API permission.

This rule is powerful but easily being misused, due to its fuzzy search feature,
make sure you have read advices [below](#more) and knowing clearly
what tweet content will hit your searching query.

About `count`: There is no max number limit of one query can get,
but sending one API query can get 100 at most,
so calculate the number of query you need to send by your own.

Check [this guide](https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query)
for how to write a search `query` string.
For character escaping concern when writing query,
read [this documentation](https://pyyaml.org/wiki/PyYAMLDocumentation#scalars).
(It's better to test it before running the script.)

If search query result is not empty, triggered.

#### more

You can save your api query volume by integrating search query rules to minimum number.
The rate of limit
of [tweet searching API](https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent)
is **180 requests per 15 minutes** with Essential Twitter API permission.

When used as a further filter rule (not under [who](#who) field),
the script will generate a prefix `from:{user_id}` followed by this query string,
to specify searching only that user's tweets,
which also means you should leave about 25 characters space
from 512 length limit for the prefix appending.

I'd like to tell you more about how to write a proper `query` string:

* Be careful to construct the query string, example 1 below may wrongly hit something like
  `"I like coffee, and I don't hate cats, I love them"` which is not what you want.

* My suggestion? Use long accurate (quoted by double quotation mark) query keyword, like example 2.

* Or use highly emotive and offensive keywords,
  which means you hate the user who just use these words to express themselves. like example 3.

```yaml
# example 1, detailed rule
- search:
    name: hate coffee or cats
    query: '"hate" "coffee" OR "cats"'
    count: 100
```

And... here is a simple format of search rule -- `search_query`,
you just need to specify the `query` string, the `count` is set to 100 by default.

```yaml
# example 2, long accurate keyword with quotation mark
- search_query: '"收留无家可归的乌克兰小姐姐"'

# example 3, highly emotive and offensive keyword
- search_query: '"son of a b*tch"'
```

### user_something

These rules show how to use user information relative metrics,
they have a common prefix: `user-`.

#### user_created

| field | value |
|:--:|:-----:|
| possible | `before` `after` |
| `before` | time, string |
| `after` | time, string |
| `within_days` | day number, number |

The time format of `before` and `after` are
"date" `yyyy_MM_dd` or "date time" `yyyy_MM_dd HH:mm:ss`,
when using former format, the time part will be extended as `00:00:00`.
They can be used together or separately,
but be careful of the validity of two times relation.

For convenience of scheduled repeatable task,
the `whitin_days` field can be used to specify a time range from now,
to specify newly created accounts.
It can't be used with `before` or `after` fields.

Times your configured are considered at UTC (+0) timezone.

```yaml
- user_created:
    after: "2019-01-01 00:00:00"
    before: "2020-01-01"

- user_created:
    within_days: 30
```

Shorten version:

```yaml
- user_created_after: "2019-01-01"

- user_created_within_days: 30
```

#### user_texts_match

| field | value |
|:--:|:-----:|
| possible | a regular expression |

Another rule that **can easily be misused**, same as [search](#search) rule,
due to its highly possible wrongly triggered feature, be careful when using it.

There are three part of text directly bind (can be queried along with Twitter user info query API) with user:

1. user's name (the name you see aside the avatar)
2. user's description (also called profile)
3. pinned tweet's text

This rule independently performs [python regular expression](https://docs.python.org/3/howto/regex.html) match on
each of these texts.
If any part of them matches the given expression, the rule triggered. Simple, yet powerful.
The script will not automatically anchor the expression with `^$`.

You can test your regular expression on [this website](https://regex101.com/).
Also, be careful of character escaping concern,
for both yaml context (quote the expression with single/double quotation mark)
and python regex context (with [backslash character](https://docs.python.org/3/howto/regex.html#the-backslash-plague)).

```yaml
# note that if you quote the expression in yaml,
# you should use double backslash for python regex escaping
user_texts_match: '[\\u1F100-\\u1F1E5]'

# it's same as above without quote and double backslash
# user_texts_match: [\u1F100-\u1F1E5]
```

#### user_follower

| field | value |
|:--:|:-----:|
| possible | `less_than` `more_than` |
| `less_than` | integer |
| `more_than` | integer |

Two fields can be used together or separately. Edge case (equal) result in False.

```yaml
- user_follower:
    more_than: 100
    less_than: 1000
```

Shorten version:

```yaml
- user_follower_less_than: 10
```

#### user_following

| field | value |
|:--:|:-----:|
| possible | `less_than` `more_than` |
| `less_than` | integer |
| `more_than` | integer |

Two fields can be used together or separately. Edge case (equal) result in False.

```yaml
- user_following:
    more_than: 100
    less_than: 1000
```

Shorten version:

```yaml
- user_following_more_than: 10
```

#### user_foer_foing_ratio

| field | value |
|:--:|:-----:|
| possible | `less_than` `more_than` |
| `less_than` | float |
| `more_than` | float |

Two fields can be used together or separately. Edge case (equal) result in False.

```yaml
- user_foer_foing_ratio:
    more_than: 0.1  # 1 follower / 10 following
    less_than: 10.0 # 10 follower / 1 following
```

Shorten version:

```yaml
# 1 follower / 100 following, this ratio tells something
- user_foer_foing_ratio_less_than: 0.01 
```

#### user_tweet_count

| field | value |
|:--:|:-----:|
| possible | `less_than` `more_than` |
| `less_than` | number |
| `more_than` | number |

Two fields can be used together or separately. Edge case (equal) result in False.
There is a simple format: `user_tweet_count_less_than`.
Just notice that this count includes both post and retweet.

```yaml
- user_tweet_count:
    more_than: 100
    less_than: 1000

- user_tweet_count_less_than: 10
```

#### user_recent_speaking_ratio

| field | value |
|:--:|:-----:|
| possible | `recent` `less_than` `more_than` |
| `recent` | number of recent tweets in count, default 100 |
| `less_than` | number, (0,1.0] |
| `more_than` | number, (0,1.0] |

`less_than` and `more_than` can be used together or separately.
`recent` is optional, default 100 when absent.

The definition of "speaking" is either a post or reply operation,
two operations that user must type something before sending out.
The ratio is calculated as:

> (reply + post) / (reply + post + retweet)

The higher the ratio, the more user intend to show his/her own thought,
instead of silently retweeting others thought.

```yaml
- user_recent_speaking_ratio:
    count: 100
    more_than: 0.2 # at least 20% of recent tweets are post
    less_than: 0.9 # not more 90% of recent tweets are post
```

### last_active_time

| field | value |
|:--:|:-----:|
| possible | `ignore` `before` `after` `within_days`|
| `ignore` | number of ignored activity trace, default 0 |
| `before` | time, string |
| `after` | time, string |
| `within_days` | day number, number |

This rule will search for the last activity traces of the user,
the definition of activity trace including: post, reply, like, retweet.

The time format of `before` and `after` are
"date" `yyyy_MM_dd` or "date time" `yyyy_MM_dd HH:mm:ss`,
when using former format, the time part will be extended as `00:00:00`.
They can be used together or separately.
The `whitin_days` field can be used to specify a time range from now.
It can't be used with `before` or `after` fields.

You can set the `ignore` field to judge the 2nd (`ignore=1`), 3rd (`ignore=2`)... last active time.
It's useful when you already know the last activity of user,
for example you specified the target user group by [agree_with_tweet](#agree_with_tweet) rule,
so "agree with that fresh tweet" will be at least one of the last activity of the user.

```yaml
last_active_time:
  ignore: 1
  within_days: 7
```

## Let_me_check Rule

| field | value |
|:--:|:-----:|
| possible | `user_info`, `recent_tweets`, `recent_replies`, `recent_likes` |
| [user_info](#user_info) | the value doesn't matter |
| [recent_tweets](#recent_tweets) | number of recent tweets |
| [recent_replies](#recent_replies) | inner fields |
| [recent_likes](#recent_likes) | number of recent liked tweets |

This rule can only be put directly under a [User Selecting Rule](#user-selecting-rule).

The human brain is excellent at natural language processing work,
and this special rule helps scripts make decisions
with the help of your subjective judgment ...
In other words, the script first helps you (via [Filter Rule](#filter-rule)s)
automatically select users who meet the filter rules conditions,
and then YOU make the final decision on the remaining users
who do not trigger the filter rules, and make the final decision on them.

The different fields determine what information the script will print to the terminal for your judgment.
This rule can override the [manually_confirm](#manually_confirm) settings,
and force you to integrate with the script.

```yaml
users:
  who:
    id_are: [ "123456789","987654321" ]
  let_me_check:
    user_info: true
    recent_tweets: 3
    recent_replies:
      count: 3
      with_origin_tweet: true
    recent_likes: 3
```

### user_info

Provides information about the user, including:

* user's name (besides the avatar), screen name (behinds an "@"),
* following, follower count
* profile, pinned tweet text

This field's value can be anything because the script will ignore it.

(I wish I can give you a `which_your_following_is_following_this_user` option,
(you can see that on various Twitter Clients when you're viewing a user's profile),
which provides you a measure of trust of acquaintances. But for making sense of it,
the script has to send a large number of request on every target user,
which is not a good choice at a time when the Twitter Dev API has rate_limitation.)

```yaml
let_me_check:
  user_info: true
```

### recent_tweets

| field | value |
|:--:|:-----:|
| possible | number of recent tweets |

Provide the recent tweets of the user, including post and retweet,
if the retweet is a quote tweet, the original quoted tweet will be printed together.

```yaml
let_me_check:
  recent_tweets: 3
```

### recent_replies

| field | value |
|:--:|:-----:|
| possible | `count` `with_origin_tweet` |
| `count` | number of recent replies, default 3 |
| `with_origin_tweet` | whether to print the origin tweet text, `true` or `false`, default `false` |

Provide the recent replies of the user, optionally with the origin tweet text.

Since a reply is necessarily written by the user_self,
expressing an opinion about the content of some else tweet,
it provides a clearer picture of the user's thoughts.

```yaml
let_me_check:
  recent_replies:
    with_origin_tweet: true
```

### recent_likes

| field | value |
|:--:|:-----:|
| possible | number of recent liked tweets |

Provide the recent liked tweets of the user.

Almost every user will like tweets, including those that don't express their thoughts much,
and this is the easiest interaction action.

We can label users by looking at what content they liked, which is undoubtedly reckless,
because one can provide quality content while unabashedly showing a love for NSFW or other bad content,
and the "like" action itself does not just mean that user agrees with the content of the tweet.
But... it's still a practical way to decide whether a user needs to be blocked, it's up to you after all.

```yaml
let_me_check:
  recent_likes: 3
```

## Rule Set

| field | value |
|:--:|:-----:|
| possible | a `name`, and other [Filter Rule](#filter-rule)s or nested [Rule Set](#rule-set)s |
| `name` | optional, the custom name of the rule set |

An [Rule Set](#rule-set) contains a list of [Filter Rule](#filter-rule)s
and nested [Rule Set](#rule-set)s.
Like the [who](#who) field, a rule set can be put under a [User Selecting Rule](#user-selecting-rule),
and one [User Selecting Rule](#user-selecting-rule) can have 0~1 rule set as further filter chain.

You can optionally give a rule set a custom name with `name` field.

```yaml
users:
  who:
    id_are: [ "123456789","987654321" ]
  all_of:
    - name: "new account"
    # a filter option
    - user_created:
        after: "2022-01-01"
    # a nested option set
    - any_of:
        - name: "not speak much"
        - user_foer_foing_ratio_less_than: 0.1
        - user_tweet_count_less_than: 10
        - user_recent_speaking_ratio_less_than: 0.05
```

### all_of

AND logic rule set, all of under rules triggered, this set triggered.
I don't think I need to introduce it more, do I?

### any_of

OR logic rule set, any of under rules triggered, this set triggered.

### weight_of

| field | value |
|:--:|:-----:|
| possible | required `goal`, optional `name`, and multiple `condition` |
| `name` | the custom name of the rule set |
| `goal` | when to trigger the rule, number |
| `condition` | contains one `weight` and one [Filter Rule](#filter-rule) or nested [Rule Set](#rule-set) |

As you can see in the example,
filter rules and nested rule sets need to be wrapped into a `condition`,
pairing with a `weight` to indicate the weight of this rule.

The value of `goal`, `weight` field can be any positive integer.
When accumulated triggered rules' weights not less than this value,
the `weight_of` rule triggered.

```yaml
weight_of:
  - goal: 2
  - condition:
      - weight: 2
      - user_foer_foing_ratio_less_than: 0.1
  - condition:
      - weight: 1
      - user_tweet_count_less_than: 10
  - condition:
      - weight: 1
      - any_of:
          - user_recent_speaking_ratio_less_than: 0.05
          - last_active_time:
              ignore: 1
              before: "2022-01-01"
```

## Reusable Mechanism

There must be a reusable mechanism in one configuration system
to reduce redundancy, here it is.
Fields defined under `fragments` with a custom name as referring key can be repeatedly referenced with `refer`.
One fragment can contain several fields.

You may notice that fields can be arranged as
both field (e.g. "numeric_fields") or list (e.g. "search_rules") format,
and this format will remain unchanged after the script parsing `refer` field,
so if you wrongly referred a list_format fragment under a field_format_required field,
the configuration file parser will complain about that and quit.

```yaml
block:
  - users:
      who:
        hit_search_results_of:
          # equal to:
          # - search_query: 'tweet_query_string-1'
          # - search_query: 'tweet_query_string-2'
          - refer: search_rules
          # can still add more fields
          - search_query: 'tweet_query_string-3'
      any_of:
        - user_follower:
            # equal to:
            # more_than: 10
            # less_than: 100
            refer: numeric_fields

fragments:
  - search_rules:
      - search_query: 'tweet_query_string-1'
      - search_query: 'tweet_query_string-2'

  - numeric_fields:
      more_than: 10
      less_than: 1000
```
