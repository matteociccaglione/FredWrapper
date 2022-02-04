from setuptools import setup

setup(
    name='fredlib',
    version='0.1.0',
    description='A Python Package for statistical usage of FRED St. Louis API',
    url='https://github.com/matteociccaglione/FredWrapper',
    author='The walking thread 2.0',
    author_email='pepe.andmj@gmail.com',
    license='BSD 2-clause',
    packages=['fredlib'],
    install_requires=[
                      'numpy','matplotlib','networkx>=2.6.3', 'requests'
                      ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
)
