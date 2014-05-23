from distutils.core import setup

setup(
    name='PETRARCH',
    entry_points={
        'console_scripts': ['petrarch = petrarch.petrarch:main']},
    version='0.01a',
    author='Philip Schrodt, John Beieler',
    author_email='openeventdata@gmail.com',
    packages=['PETRARCH'],
    url='openeventdata.org',
    license='LICENSE.txt',
    description='PETRARCH parser for event data.',
    long_description=open('README.md').read())
