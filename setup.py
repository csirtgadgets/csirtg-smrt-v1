import os
from setuptools import setup, find_packages
import versioneer
import sys

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

# https://www.pydanny.com/python-dot-py-tricks.html
if sys.argv[-1] == 'test':
    test_requirements = [
        'pytest',
        'coverage',
        'pytest_cov',
    ]
    try:
        modules = map(__import__, test_requirements)
    except ImportError as e:
        err_msg = e.message.replace("No module named ", "")
        msg = "%s is not installed. Install your test requirements." % err_msg
        raise ImportError(msg)
    r = os.system('py.test test -v --cov=csirtg_smrt --cov-fail-under=45')
    if r == 0:
        sys.exit()
    else:
        raise RuntimeError('tests failed')

package_data = {}
if sys.platform == 'nt':
    package_data['csirtg_smrt'] = os.path.join('tools', 'magic1.dll')

setup(
    name="csirtg_smrt",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    package_data=package_data,
    description="s.m.r.t",
    long_description="the fastest way to use data",
    url="https://github.com/csirtgadgets/csirtg-smrt-py",
    license='MPL2',
    classifiers=[
               "Topic :: System :: Networking",
               "Environment :: Other Environment",
               "Intended Audience :: Developers",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.org",
    packages=find_packages(exclude=['test']),
    install_requires=[
        'ipaddress>=1.0.16',
        'feedparser>=5.2.1',
        'nltk>=3.2,<3.3',
        'requests>=2.6.0',
        'arrow>=0.6.0',
        'python-magic>=0.4.6',
        'pyaml>=15.8.2',
        'chardet>=2.3.0',
        'csirtg_indicator>=0.0.0b18',
        'csirtg_mail>=0.0.0a1,<1.0',
        'SQLAlchemy>=1.0.14',
        'tornado>=4.4',
        'apwgsdk',
        'docker==2.2.1',
    ],
    entry_points={
        'console_scripts': [
            'csirtg-smrt=csirtg_smrt.smrt:main',
            'csirtg-ufw=csirtg_smrt.parser.ufw:main',
            'csirtg-cef=csirtg_smrt.parser.cef:main',
            'csirtg-bro=csirtg_smrt.parser.bro:main',
            'csirtg-smtpd=csirtg_smrt.parser.zsmtpd:main',
        ]
    },
)
