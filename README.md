# puntgun - a configurable automation command line tool for Twitter

```text
     ____              _      ____
,___|____\____________|_|____/____|____________________
|___|_|_)_|_|_|_|_'__\|___|_|_|___|_|_|_|_'__\__[____]  ""-,___..--=====
    |  __/| |_| | | | | |_  | |_| | |_| | | | |   \\_____/   ""        |
    |_|    \__,_|_| |_|\__|  \____|\__,_|_| |_|      [ ))"---------..__|
```

[![TEST](https://github.com/boholder/puntgun/actions/workflows/test.yml/badge.svg)](https://github.com/boholder/puntgun/actions/workflows/test.yml)
[![coverage status badge](https://coveralls.io/repos/github/boholder/puntgun/badge.svg?branch=main)](https://coveralls.io/github/boholder/puntgun?branch=main)
[![downloads badge](https://img.shields.io/pypi/dm/puntgun)](https://pypi.org/project/puntgun/)
[![pypi version badge](https://img.shields.io/pypi/v/puntgun)](https://pypi.org/project/puntgun/)
[![pypi python version badge](https://img.shields.io/pypi/pyversions/puntgun)](https://pypi.org/project/puntgun/)

> **Warning**
> This tool is not available yet, it will be soon!

This tool was originally conceived as a configurable automatic Twitter account blocker.
What could be a better name for it than the [**Punt Gun**](https://en.wikipedia.org/wiki/Punt_gun),
a special hunting weapon used to kill a large number of waterfowl in one shot.
But that type of gun is a huge threat to the natural environment,
and fortunately this tool only inherits the meaning of its origin,
even to the benefit of the platform environment (or at least to its users).

You can use this tool to do some boring Twitter account management
(such as automatically select and block users from a source like a tweet's likes, your follower...),
so you can free up your time for other things.

## Installation

This tool needs to be installed with the Python application management tool, no separate executable file is distributed, sorry for the inconvenience.
The most convenient way to install (and update in the future) this tool is with the help of [**pipx**](https://github.com/pypa/pipx),
which is a handy Python application management tool. [**Install it**](https://pypa.github.io/pipx/#install-pipx) first, then run:

```shell
pipx install puntgun
```

Or your can install this tool via [**pip**](https://pip.pypa.io/en/stable/user_guide/#installing-packages) which is installed with Python.
This tool requires Python **version 3.10** or above.
[Install Python](https://www.python.org/downloads/) if you haven't installed or your Python version not meet the required, then run:

```shell
python -m pip install -U puntgun
```

## Usage

This tool is a cross-platform command line tool, which means you need to use it in your [Windows Command-line shell](https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/windows-commands#command-line-shells)
or [Apple Mac Terminal](https://support.apple.com/guide/terminal/execute-commands-and-run-tools-apdb66b5242-0d18-49fc-9c47-a2498b7c91d5/mac)
or any other terminal (every Unix/Linux user knows how to open a terminal, right?).

First you need a "Twitter Dev OAuth App API" to enable the tool, with this we can request the developer APIs provided by Twitter.
Run the command below to let the tool interactively guide you register one on Twitter platform for free.
For more information, read [the documentation](https://boholder.github.io/puntgun/configuration/tool-configuration#secrets).

```shell
puntgun gen secrets
```

Then you need a Plan Configuration file to instruct what the tool will do for you, run the command below to generate an example file.
For more information about plan configuration, read [the documentation](https://boholder.github.io/puntgun/configuration/plan-configuration).

```shell
puntgun gen example
```

Now you can start the tool with your plan file with:

```shell
puntgun fire
```

If the tool doesn't exit quickly due to configuration errors (with red error logs printed pointing out what's wrong),
you can leave the terminal (window) open and move on to other things.
The tool will generate a [report file](https://boholder.github.io/puntgun/usage/report-file) (and log file) during runtime,
which you can view later to see what happened.

For more information on usage, see [the documentation website](https://boholder.github.io/puntgun).

## Technical details you may want to know

### How it works

Essentially we make the tool a third-party application
that can access the Twitter platform by registering a credential (a pair of secret token)
with your Twitter account and then using your Twitter account to authorize this tool
(the credential you registered from Twitter, in fact) to operate your account
(for blocking users, etc.).

### Limitation of the Twitter Developer API

Note that as this tool's performance is depending on the complexity of configuration you set,
it is also subject to the limitations of the Twitter Developer API because [your api query volume is not unlimited](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api),
meanwhile the Twitter Dev API [have rate limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits) with different permissions on different endpoints.
What's more, you can only [search for last 7 days tweets](https://developer.twitter.com/en/docs/twitter-api/tweets/search/introduction)
(using "search/recent" API) with Essential Twitter API permission, and query string length is limited up to 512.

### Details about secrets encryption and usage

Currently, we use the [RSA4096](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) with
the cryptographic library [Cryptography](https://github.com/pyca/cryptography/)
for processing secrets to prevent them being saved into configuration file in plaintext format.
For implementation details, check [this source code file](https://github.com/boholder/puntgun/tree/main/puntgun/conf/encrypto.py).
For Cryptography's security limitation, check [this documentation](https://cryptography.io/en/latest/limitations/).

When the tool is running, the secrets will stay inside a client object of the Twitter API client library [Tweepy](https://docs.tweepy.org),
and it seems that they are [stored as plaintext string](https://github.com/tweepy/tweepy/blob/master/tweepy/client.py#L48).
As it can't be garbage collected while we're invoking this client instance all the time when running,
I guess we can't prevent secrets from a [memory dump attack](https://en.wikipedia.org/wiki/Cold_boot_attack) or something similar.

## License

This project is open sourced under [MIT license](https://github.com/boholder/puntgun/blob/main/LICENSE).