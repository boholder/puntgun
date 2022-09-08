# Commands

This page mainly lists the commands available for this tool and their usage,
a simple tutorial about command line usage is also provided.

## Available commands

### Start the tool

```shell
puntgun fire
```

The most important command, core function of the tool.

### Validate syntax of plan configuration file

```shell
puntgun check plan
```

It is always good to have a dry run before the actual run.
Especially if you want to run this tool in an automated way.
This command only checks if the plan configuration file can pass
the validation and be successfully parsed without a parsing error,
it cannot check if the values configured in the rule will cause Twitter API complaints.

### Generate example configuration files

```shell
puntgun gen example
```

This tool requires the help of a configuration file to run properly, but it is distributed and installed alone.
Running this command after installation will generate:

* A sample global configuration file, to help you adjust the behavior of the tool to your flavor.
* A sample plan configuration file, to help you write your first execution plan.

### Follow the tool's lead to generate the secrets file

This tool also needs [secret values](https://boholder.github.io/puntgun/configuration/tool-configuration/secrets)
registered externally on Twitter Developer Platform to enable it to work properly.
Let the tool guides you to register necessary tokens,
and leave them to the tool to safely keep them into encrypted secrets file for future use.

### Change password

```shell
puntgun gen new-password
```

Easy password change is a desirable feature, and you just need to provide the present password to change it.
Since the key file is protected by a password, this command will regenerate the private key file.
The old private key file will be added with a `.bak` suffix to prevent overwriting,
so you'll still have the chance to reverse the change.

### Dump plaintext secrets

```shell
puntgun gen plaintext-secrets
```

If you have configured the secrets configuration file,
you can use this command to export the secret values to a file in plaintext.
Please protect the exported file yourself.

## Appendix: Simple tutorial about how to use the tool

This part is for users unfamiliar with the command line interface.

If you want to use the command line interface to perform other operations not mentioned,
please make use of the search engine with keyword
"<your terminal(e.g. cmd, mac terminal)> <expected operation(switch directory)>".

Assuming that you can run the puntgun tool in the terminal, That is, when you type `puntgun` and enter,
you will see the terminal print out the logo with the help information.

```shell
> puntgun
Usage: puntgun [OPTIONS] COMMAND [ARGS]...

  LOGO HERE
  
Options: ...

Commands: ...
```

If the terminal reports an error like `puntgun not found`,
you can search for that error (key concept: [PATH environment variable](https://superuser.com/a/284351))
to find the cause and resolve or reinstall the tool.

This tool contains multi-level subcommands, and you can execute them like this:

```shell
# the tool
# |    subcommand: abbreviation of "generate" 
# v      v     secondary subcommand: generate example files
puntgun gen example
```

You can check the build-in help information by adding `--help` argument behind any command,
the command will not be executed, instead the help information about this command will be printed out.

```shell
> puntgun gen example --help
Usage: puntgun gen example [OPTIONS]   

  Generate example configuration files.

Options:
  -o, --output-path TEXT  Path of generated files.[default:
                          /home/u/.puntgun]
  -h, --help              Show this message and exit.
```

Note the **Options** section, which indicates the arguments that can be passed to this command.
Arguments can provide additional information to the tool (e.g. `-o`) or change the behavior of the tool (e.g. `--help`).
For passing information via arguments, type like this:

```shell
# "-o" is abbreviation of "--output-path", they are same, just pass one. 
# Change the directory where the tool will generate files
puntgun gen example -o "/path/you/want/to/generate/example/files"
```

I think knowledge above is enough for you to use this tool,
if you need help or want the documentation to contain more content,
please ask questions in [the forum](https://github.com/boholder/puntgun/discussions/categories/q-a).
Don't forget to search before asking to see if the question and answer you need already exist.