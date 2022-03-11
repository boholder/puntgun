# Recommend Rule Combination

We're trying to use rule combinations to reflect user behaviors.

## User Information Metrics

### "just-watch-not-speak" type user

```yaml
# by accurate number
all-of:
  - user-follower-less-than: 20
  - user-following-more-than: 500
  
# by ratio
- user-foer-foing-ratio-less-than: 0.01 
```

Combining `user-following-more-than` with `user-follower-less-than`,
you can get a pretty nice complex-rule to mark the "just-watch-not-speak" type user,
which I used in my previous processing.
Only post,retweet,reply behavior maybe increase follower number,
despite of auto-follow-back-when-being-followed.

(I don't want this type of users to watch my tweets,
because I suspect some of them are bot,
or even worse: data collecting endpoint,
or spy for disabling the effort of turning on "protect your account" in the future.)
