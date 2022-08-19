import os
from pathlib import Path
from unittest.mock import MagicMock

from puntgun.command import Command, Gen


def test_fire(monkeypatch):
    # just don't really start
    mock_runner_start_func = MagicMock()
    monkeypatch.setattr('puntgun.runner.start', mock_runner_start_func)
    monkeypatch.setattr('puntgun.client.Client.singleton', lambda: 1)
    mock_reload_important_files_func = MagicMock()
    monkeypatch.setattr('puntgun.conf.config.reload_important_files', mock_reload_important_files_func)

    Command.fire(config_path='cf', plan_file='pf', settings_file='sf',
                 private_key_file='pkf', secrets_file='scf', report_file='rf')

    mock_runner_start_func.assert_called_once()

    # expect the real runner can use updated config file paths
    input_args = mock_reload_important_files_func.call_args[1]
    for key, expect in [('config_path', 'cf'),
                        ('plan_file', 'pf'),
                        ('settings_file', 'sf'),
                        ('pri_key_file', 'pkf'),
                        ('secrets_file', 'scf'),
                        ('report_file', 'rf')]:
        assert input_args[key] == expect


def test_gen_secrets_and_backup_original_file(monkeypatch, tmp_path):
    monkeypatch.setattr('puntgun.conf.encrypto.load_or_generate_private_key', lambda: 'whatever a value')
    monkeypatch.setattr('puntgun.conf.secret.load_or_request_all_secrets', lambda _: {'a': '1', 'b': '2'})

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
