"""Main application code."""

import functools
import sys
import webbrowser

import unfriendly.model
import unfriendly.ui

from PySide import QtCore
from PySide import QtGui

_INSTANCE = None


class UnfriendlyApp(QtCore.QObject):
    """Main application."""

    def __init__(self, ui, model):
        """Initialize.

        Args:
            ui (unfriendly.ui.UnfriendlyWindow): UI for the app.
            model (unfriendly.model.UnfriendlyModel): Model for the app.
        """

        super(UnfriendlyApp, self).__init__()

        self.model = model

        self.ui = ui
        self.ui.ViewUserProfile.connect(self._view_user_profile)
        self.ui.UnfollowUser.connect(self._unfollow_user)

        self.ui.Shutdown.connect(self.model.shutdown)

        self._startup_timer = QtCore.QTimer()
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(self.model.startup)
        self._startup_timer.start(0)

        app = QtGui.QApplication.instance()

        self.ui.Shutdown.connect(functools.partial(app.quit))
        self.ui.show()

        self.model.startup()

    def _unfollow_user(self, user_id):
        """Unfollow the user with the given id.

        Args:
            user_id (int): A Twitter user id.
        """

        self.model.unfollow_user(user_id)

    def _view_user_profile(self, user_name):
        """Open the user's profile page in a web browser.

        Args:
            user_name (str): Name of a Twitter user.
        """

        webbrowser.open(self.model.twitter_url(user_name))


def main(app_name, version='unknown'):
    """Launch the application.

    Args:
        app_name (str): Display name of the application.
        version (str): Version of the application.
    """

    app = QtGui.QApplication(sys.argv)

    mod = unfriendly.model.UnfriendlyModel(app_name, version)
    win = unfriendly.ui.UnfriendlyWindow(mod)

    UnfriendlyApp(win, mod)

    sys.exit(app.exec_())
