import os
from pathlib import Path
from unittest.mock import MagicMock

from command import Command, Gen
from conf import config


def test_fire(monkeypatch, tmp_path):
    """Sort of, implement specific"""
    # just don't really start working
    mock_runner_start_func = MagicMock()
    monkeypatch.setattr('runner.start', mock_runner_start_func)

    # prepare a config file for testing config reloading
    # after indicating config file paths through command args.
    custom_config_file = tmp_path.joinpath('c.yml')
    with open(custom_config_file, 'w', encoding='utf-8') as f:
        f.write('a: 123')

    # and... prepare another two files that will be loaded by dynaconf
    # so dynaconf can successfully reload custom config files
    custom_plan_file = tmp_path.joinpath('pf.yml')
    custom_plan_file.touch()
    custom_secrets_file = tmp_path.joinpath('scf.yml')
    custom_secrets_file.touch()

    Command.fire(config_path='cf', plan_file=str(custom_plan_file), settings_file=str(custom_config_file),
                 private_key_file='pkf', secrets_file=str(custom_secrets_file), report_file='rf')

    mock_runner_start_func.assert_called_once()

    # expect the real runner can use updated config file paths
    for actual, expect in [(config.config_path, 'cf'),
                           (config.plan_file, str(custom_plan_file)),
                           (config.settings_file, str(custom_config_file)),
                           (config.pri_key_file, 'pkf'),
                           (config.secrets_file, str(custom_secrets_file)),
                           (config.report_file, 'rf')]:
        assert actual == Path(expect)

    # the config is really reloaded
    assert config.settings.get('a') == 123


def test_gen_secrets_and_backup_original_file(monkeypatch, tmp_path):
    monkeypatch.setattr('command.load_or_generate_private_key', lambda: 'whatever a value')
    monkeypatch.setattr('command.load_or_request_all_secrets', lambda _: {'a': '1', 'b': '2'})

    output_file = tmp_path.joinpath('o.yml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('123')

    Gen.secrets(output_file=output_file)

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
