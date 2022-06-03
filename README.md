# Punt Gun - a configurable automation command line tool for Twitter

[![unit test coverage badge](./coverage/converage.svg)](./coverage)

## How to use

## Technical details you need to know

### Limitation from the Twitter Developer API

Note that the script's speed is depending on the block rules you set,
because [your api query volume is not unlimited usually](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api),
meanwhile the Twitter Dev API [have rate limits restriction with different permissions on different endpoints](https://developer.twitter.com/en/docs/twitter-api/rate-limits).

What's more, you can only [search for last 7 days tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction) (using "search/recent" API) with Essential Twitter API permission, and query string length is limited up to 512.
