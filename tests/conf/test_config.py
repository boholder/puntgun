import datetime
from pathlib import Path

from puntgun.conf import config


def test_reload_config_files(monkeypatch, tmp_path):
    # prepare a config file for testing config reloading
    # after indicating config file paths through command args.
    custom_config_file = tmp_path.joinpath("c.yml")
    with open(custom_config_file, "w", encoding="utf-8") as f:
        f.write("a: 123")

    # and... prepare another two files that will be loaded by dynaconf
    # so dynaconf can successfully reload custom config files
    custom_plan_file = tmp_path.joinpath("pf.yml")
    with open(custom_plan_file, "w", encoding="utf-8") as f:
        f.write("b: hello")
    custom_secrets_file = tmp_path.joinpath("scf.yml")
    with open(custom_secrets_file, "w", encoding="utf-8") as f:
        f.write("c: 2022-01-01 01:01:01")

    config.reload_important_files(
        config_path="cf",
        plan_file=str(custom_plan_file),
        settings_file=str(custom_config_file),
        pri_key_file="pkf",
        secrets_file=str(custom_secrets_file),
        report_file="rf",
    )

    # expect the real runner can use updated config file paths
    for actual, expect in [
        (config.config_path, "cf"),
        (config.plan_file, str(custom_plan_file)),
        (config.settings_file, str(custom_config_file)),
        (config.pri_key_file, "pkf"),
        (config.secrets_file, str(custom_secrets_file)),
        (config.report_file, "rf"),
    ]:
        assert actual == Path(expect)

    # the config is really reloaded
    assert config.settings.get("a") == 123
    assert config.settings.get("b") == "hello"
    assert config.settings.get("c") == datetime.datetime(2022, 1, 1, 1, 1, 1)
