import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

install_requires = ['PyYAML>=3.10', 'outbox>=0.1.5', 'hammock>=0.2.4', 'six']
if sys.version_info[:1] < (2, 7):
    install_requires.append('ordereddict')

setup(
    name='redmine-alerts',
    version='0.1dev',
    packages=['redmine_alerts'],
    url='http://github.com/coagulant/redmine-alerts',
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryhsev@gmail.com',
    description='Notify developers and managers when spent time reached estimate on task in Redmine.',
    long_description=open('README.rst').read() + '\n\n' + open('CHANGELOG.rst').read(),
    entry_points={
        'console_scripts': [
            'redmine-alerts = redmine_alerts.cli:main',
        ],
    },
    dependency_links=(
       'https://github.com/gabrielfalcao/HTTPretty/archive/master.zip#egg=httpretty-0.6',
    ),
    install_requires=install_requires,
    tests_require=['mock', 'pytest', 'pytest-capturelog', 'httpretty==0.6.0', 'coverage'],
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)