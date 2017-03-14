# coding: utf-8
from setuptools import setup, find_packages
setup(name='loopchat',
    description='Fast and scalable chat subsystem',
    version='0.1a0',
    license='MIT',
    author='Andrii Murisimov',
    author_email='murisimov@gmail.com',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Webmasters',
        'Programming Languages :: Python, Javascript',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    include_package_data = True,
    zip_safe=True,
    install_requires=[
        'setuptools',
        'tornado==4.4',
        'futures>=3.0.5',
        'redis==2.10.5',
        'tornadis==0.7.0',
        'TorMySQL==0.2.2',
    ],
    entry_points={
        'console_scripts': [
            'loopchat = loopchat.server:main',
            'loopchat-periodics = loopchat.periodics:main'
        ]
    },
)
