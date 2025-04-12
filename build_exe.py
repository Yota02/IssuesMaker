import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'main.py',
    '--name=IssuesMaker',
    '--onefile',
    '--windowed',
    '--icon=assets/logo.ico',
    '--add-data=assets/logo.ico;assets',
    '--clean',
    '--noconfirm'
])