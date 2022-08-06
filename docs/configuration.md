---
title: Configuration
nav_order: 1
---

# Configuration

This page is describing configurations of the tool itself, i.e. the contents of [/conf/settings.yml](/conf/settings.yml).
For all available plan configurations, please check [the plan configuration document page](plan-configuration.md).
There are two types of tool configuration:
most of them can be configured in global configuration file or set via environment variable,
but some special configurations can only be passed through command line argument.

The tool is using the [Dynaconf](https://www.dynaconf.com/) as the configuration parsing library.

## Loading Priority (Precedence)

The tool will choose the tool configurations in the following order:

1. Command line arguments & Environment variables[[ref](https://www.dynaconf.com/envvars/)].
2. User writen plan configuration files.
3. Global settings file and secrets file.
4. Default values set inside program.

## Setting Via Configuration File

You can use [different supported formats](https://www.dynaconf.com/settings_files/#supported-formats)
like .yaml, .toml, .ini, .json. In this page we'll use yaml format.

The name of one setting option is also the key in configuration file,
and you can [set an environment variable](#setting-via-environment-variable) for it.

| Name              | Default | Description                                                                                                                |
|-------------------|---------|----------------------------------------------------------------------------------------------------------------------------|
| `log_rotation`    | 100MB   | [Change log files writing method](https://loguru.readthedocs.io/en/stable/api/logger.html#file) (when to split a new file) |
| `block_following` | false   | Whether to block users that you're following                                                                               |
| `block_follower`  | true    | Whether to block users that following you                                                                                  |

You can [search](https://github.com/search?q=%22settings.get%22+%22plans%22+repo%3Aboholder%2Fpuntgun+in%3Afile&type=code)
how particular configuration is used in source code if you are interested.

## Setting Via Environment Variable

You can set the tool configurations via [setting environment variables](https://www.dynaconf.com/envvars/),
with the prefix `BULLET_` followed by upper case of the name,
in which you can build automated processes.
This is quite useful and simple when setting up secrets.

```text
# setting in configuration file (yaml)
caliber: 20 ga.

# variable in environment (unix-like os style)
export BULLET_CALIBER="20 ga."
```

## Setting Via Command Line Argument

There are some "one-off" configurations
(value may be different in each execution, so not suitable for the global scope).

The tool will use `--secrets_file` and `--private_key_file` to manage secrets in a safe way,
[here](#let-the-tool-manages-secrets) is more detailed introduction.

| Argument             | Default                                                                     | Description                                                                            |
|----------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `--config_path`      | [`<home directory>`](https://en.wikipedia.org/wiki/Home_directory)/.puntgun | Path of various configuration files the tool needs                                     |
| `--plan_file`        | `<config path>`/plan.yml                                                    | [Plan configuration file]() you'd like to execute                                      |
| `--settings_file`    | `<config path>`/settings.yml                                                | Global tool settings that will apply to every execution                                |
| `--private_key_file` | `<config path>`/.puntgun_rsa4096                                            | Tool generated password protected private key                                          |
| `--secrets_file`     | `<config path>`/.secrets.yml                                                | Tool generated cipher text or user writen plain text file contains [secrets](#secrets) |
| `--report_file`      | `<same directory with plan file>`/`<plan_file>`_`<time>`_report.json        | Expect path of the tool generated [execution report]()                                 |

## Secrets

Secrets are strings that need to be kept well,
and you should treat them as you would your Twitter account's password.
Anyone who has them can manipulate your Twitter account at will just like they have your password.

We need four (two pairs of) secrets to make the tool work:

1. A pair of Twitter Developer API usage credential for querying Twitter APIs,
   configuration name: `ak` & `aks`, stands for **A**pi **K**ey secrets pair key and key **S**ecrets.
   We'll [get them from Twitter Dev Platform](#registering-a-twitter-api-credential).

2. An access token pair that indicate your consent for API key above to operate your account,
   configuration name: `at` & `ats`, stands for **A**ccess **T**oken pair key and key **S**ecrets.
   We can't get them until first run the tool.

### Registering A Twitter API Credential

When the tool is first launched there is an interactive guide procedure
instructing you on how to register and save your credentials.
If you want to register one right away, keep reading, if not, skip this paragraph.

For registering a credential, first you need a Twitter account (you already have one I guess),
and you need to bind a phone number with that account. You can do unbind after get the credential,
and the credential will remain valid.
But Twitter already saved a new line of record about your phone inside the user table,
now it's up to you whether you want to continue or not.

Follow the instruction below:

1. Register the credential ("register an app" Twitter says so) on [developer.twitter.com](https://developer.twitter.com/en).

2. Turn on "OAuth 1.0a" in your App settings:
    1. Set the App permissions to "Read and write".

    2. Set the callback, website URL to "https://twitter.com" for passing
    3.
   Stay in simple, for encrypting that file we need a private key (another secret value),   
   the website's validation check.
   (We'll use the pin-based auth method, so we needn't really deploy a server for
   receiving Twitter's callback.)

All set, now you can directly paste them into the tool.
You must run the tool at least once to authorize this tool
with your Twitter account to get access token pair,
then you can [dump secrets]() and set all these four secrets for automatically running the tool.

### Let The Tool Manages Secrets

The tool will help you manage secrets by default, and interactive with you via terminal
(command line interface) while running to operate them.
In short, you create a new password and keep it, the password protects the `<private_key_file>`,
the private key protects four secret values in `<secrets_file>`.
You keep the password, let the tool arrange rest things for you.
Keep reading if you interest about details or skip if you don't.

First we talk about secrets saving. If the tool can't find some secrets in environment variables,
it will ask you to input secrets through terminal, then save all secrets into an encrypted file
(named as `<secrets_file>`), sort of like put them into a box and lock the box.
No one can figure out the secret values even they can read the `<secrets_file>`,
there are just meaningless cipher text, no plain text.

Stay in simple, for encrypting that `<secrets_file>`, we'll need a private key (another secret value),
the tool will automatically generate one for you.
This private key can act as both "key" and "lock" of the `<secrets_file>` "box".
We can't remember, and it's inconvenient to re-input this long value,
so we need to save this value down to a file,
or we'll lose it after reboot the computer like your poor office files,
so here is the second file - `<private_key_file>`.

It may disappoint you but, for saving the private key into the `<private_key_file>`
we need another password (passphrase) to protect the dumped value,
this time it's short and human-readable just like other normal passwords,
it's created and inputted by you, and you should remember it for future usage.

Make sense? Loading secrets when restart the tool afterwards is in plain reversed order.
You enter the password (through terminal), the tool load the private key,
use the private key load secrets, done.

For more security concern, read [this paragraph](https://github.com/boholder/puntgun#details-about-secrets-encryption-and-usage).

### Setting Secrets Via Other Methods For Automation

The tool's "require-input-password-to-decrypt-secrets" interaction behavior will block the program.
So here are some other ways to set secrets for integrating this tool into automating process.
You'll provide plain text format secret values with these methods,
so we'd like to remind you to keep secrets safe from bad guys.

Four secrets in total: `ak`, `aks`, `at`, `ats`, you **must** provide both four secrets
or the tool will still ask you for remains. You can provide `ak`, `aks` and `at`, `ats`
via different approach if you want.

1. You can indicate a file path with `--secrets_file` command line argument when starting the tool,
   in which contains secrets configured like other normal configuration options.
   (You can even directly write these secrets in you plan file and the tool still can load them,
   but that's dangerous and not recommended.)

2. You can [set environment variables](#setting-via-environment-variable) for them.

3. You can pass your private key file's password through *[stdin](https://en.wikipedia.org/wiki/Standard_streams)*,
   the tool will read the password from *stdin* instead of ask password interactively
   when it detects it's not facing an interactive shell (atty stdin).
