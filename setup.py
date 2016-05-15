import os
from setuptools import setup, find_packages
import versioneer

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
    name="csirtg_smrt",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="s.m.r.t",
    long_description="",
    url="https://github.com/csirtgadgets/csirtg-smrt-py",
    license='LGPL3',
    classifiers=[
               "Topic :: System :: Networking",
               "Environment :: Other Environment",
               "Intended Audience :: Developers",
               "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.org",
    packages=find_packages(),
    install_requires=[],
    scripts=[],
    entry_points={
        'console_scripts': [
            'csirtg-smrt=csirtg_smrt.smrt:main',
        ]
    },
)
