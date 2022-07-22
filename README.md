# puntgun - a configurable automation command line tool for Twitter

[![ci workflow status badge](https://github.com/boholder/puntgun/actions/workflows/ci.yml/badge.svg)](https://github.com/boholder/puntgun/actions/workflows/ci.yml)
[![unit test coverage badge](./coverage/coverage.svg)](./coverage)
[![releases total download badge](https://img.shields.io/github/downloads/boholder/puntgun/total)](https://github.com/boholder/puntgun/releases)
[![pypi python version badge](https://img.shields.io/pypi/pyversions/puntgun)](https://pypi.org/project/puntgun/)

This tool was originally conceived as a configurable automatic Twitter account blocker. What could be a better name for it than [the punt gun](https://en.wikipedia.org/wiki/Punt_gun), a special hunting weapon used to kill a large number of waterfowl in one shot. But that type of gun is a huge threat to the natural environment, and fortunately this tool only inherits the meaning of its origin, even to the benefit of the social platform environment (or at least to the mental health of its users).

## Usage

## Technical details you may want to know right now

### Limitation of the Twitter Developer API

Note that as puntgun's performance is depending on the complexity of configuration you set,
it is also subject to the limitations of the Twitter Developer API because [your api query volume is not unlimited](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api),
meanwhile the Twitter Dev API [have rate limits restriction with different permissions on different endpoints](https://developer.twitter.com/en/docs/twitter-api/rate-limits).
What's more, you can only [search for last 7 days tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction) (using "search/recent" API) with Essential Twitter API permission, and query string length is limited up to 512.

### Details about secrets encryption and usage

Currently, we use the [RSA4096](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) with the cryptographic library [Cryptography](https://github.com/pyca/cryptography/) for processing secrets to prevent them being saved into configuration file in plaintext format. For implementation details, check [these source codes](puntgun/conf/encrypto.py). For Cryptography's security limitation, check [this document](https://cryptography.io/en/latest/limitations/).

When the tool is running, the secrets will stay inside a client object instance of the Twitter API client library [Tweepy](https://docs.tweepy.org), and it seems that they are [stored as plaintext string](https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L48). As we're calling this cilent instance all over the tool while running, so I guess we can't prevent secrets from a [memory dump attack](https://en.wikipedia.org/wiki/Cold_boot_attack) or something similar.

## Disclaimer

There always has to be such a statement (where else would I need to put it?). Hopefully our unit tests are sufficient to avoid tragedies caused by faulty logic. However, we have the cheek to state that such errors are still covered by the disclaimer, although we will still suffer from a guilty conscience and do our best to fix them if these god-forbidden things happen:

> This tool may have unrecoverable (or very difficult to recover) effects on users' Twitter accounts (for example, if your plan configuration is too crazy, it happens). The maintainers of this tool are not responsible for any damage caused by the use of this tool.