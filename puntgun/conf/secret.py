from pathlib import Path


def save_secrets_to_configuration_file(file_path: Path, **kwargs):
    """will overwrite the file if it already exists"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(f'{key}={value}' for key, value in kwargs.items())
