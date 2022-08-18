"""
This might be a bad idea...
save all content of example config files as text blocks.
Any better idea?
"""
# TODO doc link
tool_settings = """# The settings of the tool itself.
# Options can be overridden by the same-name ones in the user-writen plan configuration file
# or in the environment variables.
# The values of the commented out options are default values
# Reference documentation: TODO

# Log level of the log file and stderr
# https://loguru.readthedocs.io/en/stable/api/logger.html#levels
#log_level: info

# Change log files writing method (when to split a new file)
# https://loguru.readthedocs.io/en/stable/api/logger.html#file
#log_rotation: 100MB

# Whether to block users that you're following.
#block_following: false

# Whether to block users that following you.
#block_follower: true

# Let the tool read the password (for loading private key file) from stdin 
# instead of ask user input it through terminal.
# One of several ways to automate the running of this tool.
#read_password_from_stdin: false
"""
# TODO doc link
plan_config = """# This is an example configuration file of plan.
# Reference documentation: TODO
 """
