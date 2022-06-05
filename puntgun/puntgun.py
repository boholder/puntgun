import fire


class Command(object):
    @staticmethod
    def pow(plan_file='', config_file='', secrets_file='', block_following=False):
        """Check & block/mute users base on the given configuration file.

        :param plan_file: the plan configuration file this time.
        :param config_file: the tool behavior configuration file.
        :param secrets_file: the file containing the plaintext secrets.
        :param block_following: whether to block users that you are following.
        """
        print_banner()
        print(f'start blocking:{plan_file}')

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
        # TODO 配置文件里可配套写测试用例和预期结果
        print(f"check rule file:{config_file}")

    @staticmethod
    def report(report_file='report.yml'):
        """Show a brief of the given report file, number of blocked users for example."""
        print(f"check old record file:{report_file}")


def print_banner():
    print("""
,______________________________________
|______________________________ [____]  ""-,___..--=====
Punt Gun - a configurable Twitter \\_____/   ""         |
             user blocking script    [ ))"---------..__|
    """)


if __name__ == '__main__':
    # expose subcommands
    fire.Fire(Command)
