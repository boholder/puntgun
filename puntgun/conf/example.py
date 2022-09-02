"""
This might be a bad idea...
save all content of example config files as text blocks.
Any better idea?
"""
tool_settings = """# The settings of the tool itself.
# Options can be overridden by the same-name ones
# in the user-written plan configuration file or in the environment variables.
# The values of the commented out options are default values.
# Reference documentation:
# https://boholder.github.io/puntgun/configuration/tool-configuration/

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

plan_config = """# This is an example plan configuration file.
# This file does not cover all available rules,
# you'd better check the documentation for more detailed description.
# Reference documentation:
# https://boholder.github.io/puntgun/configuration/plan-configuration/

plans:
  # Name (explain) of this plan
  - user_plan: Do block on three users depend on their follower number
    from:
      # '@TwitterDev' and '@TwitterAPI'
      - names: ['TwitterDev', 'TwitterAPI']
    that:
      # who has less than ten followers
      - follower:
            less_than: 10
      # or has more than one hundred million following
      # why so big? just for prevent making it really works.
      - following:
            more_than: 100000000
    do:
      # block them
      - block: {}
 """
