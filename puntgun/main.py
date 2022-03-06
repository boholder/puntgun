from twitter_wrapper import Hunter


def print_banner():
    print('Punt Gun - Twitter user blocker based on configuration\n')


if __name__ == '__main__':
    print_banner()
    hunter = Hunter()
    test_user = hunter.observe(user_id=hunter.id)
    trace = hunter.trace(test_user.id)
    print(trace)

# valid
# twitter.client.block(test_user.data.get('id'))

# gun loaded
