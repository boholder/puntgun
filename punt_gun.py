from puntgun.hunter import Hunter
from puntgun.hunting_plan import HuntingPlan


def print_banner():
    print(' ,______________________________________\n'
          '|______________________________ [____]  ""-,__  __..--=====\n'
          'Punt Gun                         \\_____/   ""            |\n'
          '- a configurable Twitter             [ ))"------------..__|\n'
          '  user blocking script\n')


if __name__ == '__main__':
    # print_banner()
    plan = HuntingPlan()

    hunter = Hunter()
    test_user = hunter.observe(user_id=hunter.id)
    trace = hunter.listen_tweeting(query='from:{}'.format(test_user.id))
    print(trace)

# TODO 命令行传入用户过滤参数和配置文件，忽略配置中的用户过滤，实现与其他工具的自动化配合。
