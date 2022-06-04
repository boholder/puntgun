# Punt Gun - a configurable automation command line tool for Twitter

[![unit test coverage badge](./coverage/converage.svg)](./coverage)

## Installation

## Usage

## Technical details you need to know

### Limitation of the Twitter Developer API

Note that as puntgun's performance is depending on the complexity of configuration you set,
it is also subject to the limitations of the Twitter Developer API because [your api query volume is not unlimited](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api),
meanwhile the Twitter Dev API [have rate limits restriction with different permissions on different endpoints](https://developer.twitter.com/en/docs/twitter-api/rate-limits).
What's more, you can only [search for last 7 days tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction) (using "search/recent" API) with Essential Twitter API permission, and query string length is limited up to 512.

### Details about secrets encryption

Currently, we use the [RSA4096](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) with the [Cryptography](https://github.com/pyca/cryptography/) python cryptographic library for processing secrets to prevent them being saved into configuration file in plain-text format. For implementation details, check [this source file](puntgun/conf/encrypto.py). For Cryptography's security limitation, check [this document](https://cryptography.io/en/latest/limitations/).