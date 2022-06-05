# Punt Gun - a configurable automation command line tool for Twitter

[![unit test coverage badge](./coverage/converage.svg)](./coverage)

## Usage

## Technical details you may want to know right now

### Limitation of the Twitter Developer API

Note that as puntgun's performance is depending on the complexity of configuration you set,
it is also subject to the limitations of the Twitter Developer API because [your api query volume is not unlimited](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api),
meanwhile the Twitter Dev API [have rate limits restriction with different permissions on different endpoints](https://developer.twitter.com/en/docs/twitter-api/rate-limits).
What's more, you can only [search for last 7 days tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction) (using "search/recent" API) with Essential Twitter API permission, and query string length is limited up to 512.

### Details about secrets encryption

Currently, we use the [RSA4096](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) with the [Cryptography](https://github.com/pyca/cryptography/) cryptographic library for processing secrets to prevent them being saved into configuration file in plaintext format. For implementation details, check [these source codes](puntgun/conf/encrypto.py). For Cryptography's security limitation, check [this document](https://cryptography.io/en/latest/limitations/).

## Disclaimer

There always has to be such a statement. (Where else would I need to put it?)

This tool may have unrecoverable (or very difficult to recover) effects on Twitter accounts (if your plan configuration is too crazy). The maintainers of this tool are not responsible for any damage caused by the use of this tool. (Hopefully our unit tests are sufficient to avoid tragedy.)