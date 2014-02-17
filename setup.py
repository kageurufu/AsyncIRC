from setuptools import setup
import asyncirc

setup(
    name='AsyncIRC',
    version='.'.join([str(c) for c in asyncirc.__version__]),
    description='Dependancy-free Asynchronous IRC Library',
    long_description=asyncirc.__doc__,
    author='Franklyn Tackitt',
    author_email='franklyn@tackitt.net',
    url='https://github.com/kageurufu/asyncirc',
    packages=['asyncirc'],
    classifiers=[
        'Topic :: System :: Networking'
    ]
)