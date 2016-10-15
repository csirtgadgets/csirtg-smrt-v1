# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_submodules
from glob import glob

name = 'csirtg-smrt'

block_cipher = None

submodules = [
    'csirtg_smrt.client',
    'csirtg_smrt.parser',
    'csirtg_smrt.utils'
]

hidden_imports = []
for s in submodules:
    hidden_imports.extend(collect_submodules(s))

data = [
    ('../_version', 'csirtg_smrt'),
]

for f in glob('../csirtg_smrt/client/*.py'):
    data.append((f, 'csirtg_smrt/client'))

for f in glob('../csirtg_smrt/parser/*.py'):
    data.append((f, 'csirtg_smrt/parser'))

a = Analysis(['csirtg_smrt/smrt.py'],
             binaries=None,
             datas=data,
             hiddenimports=hidden_imports,
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

coll = COLLECT(pyz,
               a.scripts,
               a.binaries,
               a.zipfiles,
               a.datas,
               name='test',
               debug=False,
               strip=None,
               upx=True,
               console=True)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=name,
          debug=False,
          strip=None,
          upx=True,
          console=True)