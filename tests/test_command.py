from unittest.mock import MagicMock

import pytest

from command import Command, Gen
from conf.encrypto import generate_private_key


@pytest.fixture
def capture_config_reload_call(monkeypatch):
    def captor(**kwargs):
        nonlocal actual_args
        actual_args = kwargs

    actual_args = {}
    monkeypatch.setattr('conf.config.reload_config_files', captor)

    def wrapper():
        return actual_args

    return wrapper


def test_fire(monkeypatch, capture_config_reload_call):
    # just don't really start working
    mock_runner_start_func = MagicMock()
    monkeypatch.setattr('runner.start', mock_runner_start_func)

    Command.fire(config_path='cp', plan_file='pf', settings_file='stf',
                 private_key_file='pkf', secrets_file='scf', report_file='rf')

    mock_runner_start_func.assert_called_once()
    assert {'config_path': 'cp', 'plan_file': 'pf', 'settings_file': 'stf',
            'pri_key_file': 'pkf', 'secrets_file': 'scf', 'report_file': 'rf'
            } == capture_config_reload_call()


def test_gen_secrets(monkeypatch, tmp_path):
    output_file = tmp_path.joinpath('o.yml')
    monkeypatch.setattr('conf.encrypto.load_or_generate_private_key', lambda: generate_private_key())
    monkeypatch.setattr('conf.secret.load_or_request_all_secrets', lambda _: {'a': '1', 'b': '2'})

    Gen.secrets(output_file=output_file)
    # TODO unfinished
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.readlines())
