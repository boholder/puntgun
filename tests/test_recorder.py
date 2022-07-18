from datetime import datetime

from recorder import Record


class TestRecord:
    def test_to_yaml(self):
        yaml_lines = Record(type='user', data={'a': {'b': 'c'}, 'd': 123}).to_yaml().split('\n')
        assert len(yaml_lines) == 6
        assert yaml_lines[0] == ''
        assert yaml_lines[1] == '  - type: user'
        # yaml_lines[1] is time labeling line
        assert yaml_lines[3] == '    data:'
        assert yaml_lines[4] == "      - a: {'b': 'c'}"
        assert yaml_lines[5] == '      - d: 123'
