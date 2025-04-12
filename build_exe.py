import PyInstaller.__main__

# Définition de la version
VERSION = "1.0.1"

PyInstaller.__main__.run([
    'main.py',
    f'--name=IssuesMaker-v{VERSION}',
    '--onefile',
    '--windowed',
    '--icon=assets/logo.ico',
    '--add-data=assets/logo.ico;assets',
    '--clean',
    '--noconfirm'
])