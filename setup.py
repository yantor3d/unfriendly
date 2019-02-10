from setuptools import setup


setup(
    name='unfriendly',
    version='0.0.1',
    description='A tool for un-following inactive Twitter friends.',
    author='Ryan Porter',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Other Audience',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='twitter unfollow inactive',
    packages=['unfriendly'],
    package_data={'unfriendly': ['resources/icon.png']},
    include_package_data=True,
    install_requires=['tweepy', 'PySide'],
    entry_points={
        'gui_scripts': [
            'unfriendly=unfriendly:main'
        ]
    }
)
