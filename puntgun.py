from puntgun.spi.twitter_client.tweepy_hunter import TweepyHunter


def print_banner():
    print("""
,______________________________________
|______________________________ [____]  ""-,___..--=====
Punt Gun - a configurable Twitter\\_____/   ""         |
             user blocking script    [ ))"---------..__|
    """)


if __name__ == '__main__':
    # print_banner()
    # plan = HuntingPlan()

    hunter = TweepyHunter()
    test_user = hunter.observe(user_id=hunter.id)
    trace = hunter.listen_tweeting(query='from:{}'.format(test_user.id))
    print(trace)

# TODO 变成可发布的命令行工具：
#  命令行传入用户过滤参数和配置文件，忽略配置中的用户过滤，实现与其他工具的自动化配合。
