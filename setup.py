from setuptools import setup

with open('requirements.txt', 'r') as f:
        required = f.read().splitlines()

setup(
    name='petrarch2',
    install_requires=required,
    entry_points={
        'console_scripts': ['petrarch2 = petrarch2.petrarch2:main']},
    version='1.0.0',
    author='Philip Schrodt, John Beieler, Clayton Norris',
    author_email='openeventdata@gmail.com',
    packages=['petrarch2'],
    package_dir={'petrarch2': 'petrarch2'},
    package_data={'petrarch2': ['data/dictionaries/*', 'data/text/*',
                               'data/config/*']},
    url='openeventdata.org',
    license='LICENSE.txt',
    description='PETRARCH 2 parser for event data.',
    long_description=open('README.md').read())
