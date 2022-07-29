import fire

from conf import config

banner = """
,______________________________________
|______________________________ [____]  ""-,___..--=====
Punt Gun - a configurable Twitter \\_____/   ""        |
             user blocking script    [ ))"---------..__|
"""


class Command(object):
    @staticmethod
    def fire(config_path='', plan_file='', settings_file='', private_key_file='', secrets_file='',
             report_file=''):
        """Run a plan configuration.

        :param config_path: Path of various configuration files the tool needs.
        :param plan_file: Plan configuration file you'd like to execute.
        :param settings_file: Global tool settings that will apply to every execution.
        :param private_key_file: Tool generated password protected private key.
        :param secrets_file: Tool generated cipher text or user writen plain text file contains secrets.
        :param report_file: Expect path of the tool generated execution report.
        """
        config.reload_config_files_base_on_cmd_args(config_path, plan_file, settings_file,
                                                    private_key_file, secrets_file, report_file)

    @staticmethod
    def rebirth(report_file='report.yml'):
        """Unblock/mute users in the given report file that this tool generated before."""
        print(f'start unblocking users in:{report_file}')

    @staticmethod
    def check():
        """Perform a dry run on the given file, for checking file's syntactic correctness etc."""
        return PreCheckCommand()


class PreCheckCommand(object):
    @staticmethod
    def config(config_file='config_parsing.yml'):
        """Check the syntactic correctness of the given configuration file,
        run test cases if the file contains."""
        print(f"check rule file:{config_file}")

    @staticmethod
    def report(report_file='report.yml'):
        """Show a brief of the given report file, number of blocked users for example."""
        print(f"check old record file:{report_file}")


if __name__ == '__main__':
    # expose subcommands
    fire.Fire(Command)
