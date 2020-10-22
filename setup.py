from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='pugdebug',
    version='1.1.0',
    description='A standalone debugging client for PHP applications',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Mte90/pugdebug',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Debuggers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
    ],
    python_requires='>=3.7',
    install_requires=['sip', 'PyQt5']
)
