"""Unfriendly.

A tool for unfollowing inactive friends on Twitter.
"""

import unfriendly.app

__author__ = 'Ryan Porter'
__version__ = '1.0.0'

APP_NAME = 'Unfriendly'


def main():
    """Application entry point."""

    unfriendly.app.main(APP_NAME, __version__)


if __name__ == '__main__':
    main()
