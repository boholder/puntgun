---
title: Configuration
nav_order: 1
---

# Configuration

This page is describing configurations of the tool itself, i.e. the contents of [/conf/settings.yml](/conf/settings.yml).
For all available Plan configurations, please check [the plan configuration document page](plan-configuration.md).
The tool is using [Dynaconf](https://www.dynaconf.com/) as the configuration parsing library.

## Loading Priority

The tool will load the tool configurations in the following order:

1. Environment variables
2. User writen plan configuration file
3. global settings file and saved secrets file
4. default values set by program logic

In particular, when plaintext secrets cannot be loaded automatically, the program prompts the user to create and enter them in the terminal or enter the password to decrypt saved secrets in an interactive way, which will stuck the automated processes. So **remember to [pre-set the secrets](#setting-secrets-via-other-methods) if you want to run this tool in an automatic way**.

## Setting via Environment variables

You can set the tool configurations via [setting environment variables](https://www.dynaconf.com/envvars/), with the prefix `BULLET_` followed by upper case of the name, in which you can build automated processes. This is quite useful and simple when setting up secrets.

```text
# setting in configuration file (yaml)
size: 20 ga.
# variable in environment
BULLET_SIZE="20 ga."
```

## Setting via configuration file

The default configuration is written in yaml format (you may want to learn about [yaml's syntax](https://yaml.org/)), but you can also use [other supported formats](https://www.dynaconf.com/settings_files/#supported-formats) like .toml, .ini, .json. In this page we'll use yaml format for displaying. The default configuration files are located at [/conf](/conf) directory when you download the tool.

## Secrets

We need four (two pairs of) secrets to make the tool work:

* A pair of Twitter Developer API usage credential for querying Twitter APIs, configuration name: `AK` & `AKS`
* An access token pair that indicate your consent for API key above to operate your account, configuration name: `AT` & `ATS`

Essentially we make the tool a third-party application that can access the Twitter platform by registering a credential and using your Twitter account to authorizing this tool (the credential you registered from Twitter, specifically) to operate your account (for blocking users, etc.).

### Registering a Twitter API credential

When the tool is first launched there is interactive guide procedure instructing you on how to register and save your credentials, if you don't want to try it right away you can just skip this step.

For registering a credential, first you need a Twitter account (you already have one I guess), and you need to bind a phone number with that account. You can do unbind after get the credential, and the credential will remain valid. But Twitter already saved a new line of record about your phone inside the user table, now it's up to you whether you want to continue or not.

Register the credential (register an app) on [developer.twitter.com](https://developer.twitter.com/en).

And turn on OAuth 1.0a in your App settings:

1. Set the App permissions to "Read and write".

2. Set the callback, website URL to "https://twitter.com" for passing
   the website's validation check.
   (We'll use the pin based auth method, so we needn't really deploy a server for
   receiving Twitter's callback.)

All set, now you can directly paste it into the tool or set them as secrets for automatically running the tool.

### Setting Secrets via other methods

There are [other approaches](https://www.dynaconf.com/secrets/) to set secrets if you don't like the straight environment variable way. But currently the tool only support the [providing-a-plaintext-secret-file](https://www.dynaconf.com/secrets/#additional-secrets-file-for-ci-jenkins-etc) method, you can indicate that file with `--secrets_file` option when starting the tool.