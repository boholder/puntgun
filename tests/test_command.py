import importlib
import os
from pathlib import Path
from unittest.mock import MagicMock

from command import Command, Gen
from conf import config


def test_fire(monkeypatch):
    # just don't really start
    mock_runner_start_func = MagicMock()
    monkeypatch.setattr('runner.start', mock_runner_start_func)
    monkeypatch.setattr('client.Client.singleton', lambda: 1)

    Command.fire(config_path='cf', plan_file='pf', settings_file='sf',
                 private_key_file='pkf', secrets_file='scf', report_file='rf')

    mock_runner_start_func.assert_called_once()

    # expect the real runner can use updated config file paths
    for actual, expect in [(config.config_path, 'cf'),
                           (config.plan_file, 'pf'),
                           (config.settings_file, 'sf'),
                           (config.pri_key_file, 'pkf'),
                           (config.secrets_file, 'scf'),
                           (config.report_file, 'rf')]:
        assert actual == Path(expect)

    # fix corrupted paths
    importlib.reload(config)


def test_gen_secrets_and_backup_original_file(monkeypatch, tmp_path):
    monkeypatch.setattr('command.load_or_generate_private_key', lambda: 'whatever a value')
    monkeypatch.setattr('command.load_or_request_all_secrets', lambda _: {'a': '1', 'b': '2'})

    output_file = tmp_path.joinpath('o.yml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('123')

    Gen.plain_secrets(output_file=output_file)

    assert output_file.read_text(encoding='utf-8') == 'a: 1\nb: 2\n'
    assert Path(str(output_file) + '.bak').read_text(encoding='utf-8') == '123'


def test_gen_example_config_files(tmp_path):
    Gen.config(tmp_path)
    # will generate two config files
    generated_files = os.listdir(tmp_path)
    assert len(generated_files) == 2
    for file in generated_files:
        assert file.endswith('.yml')
        file = tmp_path.joinpath(file)
        assert file.is_file()
