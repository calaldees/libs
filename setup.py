from os import path
from setuptools import setup, find_packages

_here = path.dirname(path.abspath(__file__))

setup(
    name='calaldees',
    description='A collection of low level python3 utils for files, network, animation, cryptography',
    version='0.0.1',
    package_dir={'': 'python3'},
    packages=find_packages(
        'python3',
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    include_package_data=True,
    long_description=open(path.join(_here, 'README.md')).read(),
    install_requires=[
    ],
    url='https://github.com/calaldees/libs',
    author='Allan Callaghan',
    author_email='calaldees@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=[
    ],
)
