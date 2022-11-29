import os
from pathlib import Path
from unittest.mock import MagicMock

from puntgun import commands
from puntgun.commands import Gen
from puntgun.conf import config, encrypto, secret


def test_fire(monkeypatch):
    # just don't really start
    mock_runner_start_func = MagicMock()
    monkeypatch.setattr("puntgun.runner.start", mock_runner_start_func)
    monkeypatch.setattr("puntgun.client.Client.singleton", lambda: 1)
    mock_reload_important_files_func = MagicMock()
    monkeypatch.setattr("puntgun.conf.config.reload_important_files", mock_reload_important_files_func)

    input_args = {
        config.CommandArg.CONFIG_PATH: "cf",
        config.CommandArg.PLAN_FILE: "pf",
        config.CommandArg.SETTINGS_FILE: "sf",
        config.CommandArg.PRIVATE_KEY_FILE: "pkf",
        config.CommandArg.SECRETS_FILE: "scf",
        config.CommandArg.REPORT_FILE: "rf",
    }
    commands.fire(input_args)

    mock_runner_start_func.assert_called_once()

    # expect the real runner can use updated config file paths
    assert input_args == mock_reload_important_files_func.call_args[0][0]


def test_gen_plaintext_secrets_and_backup_original_file(monkeypatch, tmp_path, mock_input):
    monkeypatch.setattr("puntgun.conf.encrypto.load_or_generate_private_key", lambda: "whatever a value")
    monkeypatch.setattr("puntgun.conf.secret.load_or_request_all_secrets", lambda _: {"a": "1", "b": "2"})
    # manually confirm secrets dumping
    mock_input("secrets", "y")

    output_file = tmp_path.joinpath("o.yml")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("123")

    Gen.plain_secrets(
        output_file=str(output_file),
        args={config.CommandArg.PRIVATE_KEY_FILE: "", config.CommandArg.SECRETS_FILE: ""},
    )

    assert output_file.read_text(encoding="utf-8") == "a: 1\nb: 2\n"
    assert Path(str(output_file) + ".bak").read_text(encoding="utf-8") == "123"


def test_gen_example_config_files(tmp_path):
    Gen.config(str(tmp_path))
    # will generate two config files
    generated_files = os.listdir(tmp_path)
    assert len(generated_files) == 2
    for file in generated_files:
        assert file.endswith(".yml")
        file = tmp_path.joinpath(file)
        assert file.is_file()


def test_gen_new_password(mock_secrets_config_file, mock_input):
    # this command requires both private key file and secrets file already exist
    mock_secrets_config_file(ak="ak", aks="aks", at="at", ats="ats")
    # old password | new password, oops! second new password is wrong | new password * 2 again
    mock_input("pwd", "y", "new_pwd", "y", "wrong_new_pwd", "y", "new_pwd", "y", "new_pwd", "y")
    Gen.new_password(
        {config.CommandArg.PRIVATE_KEY_FILE: config.pri_key_file, config.CommandArg.SECRETS_FILE: config.secrets_file}
    )
    # try to decrypt test secret with new password
    mock_input("new_pwd", "y")
    actual = secret.load_or_request_all_secrets(encrypto.load_or_generate_private_key())
    assert actual == {"ak": "ak", "aks": "aks", "at": "at", "ats": "ats"}
