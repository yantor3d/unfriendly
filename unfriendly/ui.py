"""UI code."""

import os 

from PySide import QtCore
from PySide import QtGui
     

class UnfriendlyWindow(QtGui.QMainWindow):
    """App window."""

    ViewUserProfile = QtCore.Signal(str)
    """Request to view a user profile."""

    UnfollowUser = QtCore.Signal(int)
    """Request to unfollow a user."""

    Shutdown = QtCore.Signal()
    """Request to shutdown the application."""

    def __init__(self, model, parent=None):
        """Initialize.

        Args:
            model (unfriendly.model.UnfriendlyModel): Model for the app
            parent (QtGui.QWidget): Optional parent for this widget.
        """

        super(UnfriendlyWindow, self).__init__(parent)

        self.model = model
        self.model.Error.connect(self._handle_model_error)

        self.setWindowTitle(self.window_title)
        self.setWindowIcon(self.window_icon)

        layout = QtGui.QVBoxLayout()

        self.friends_view = QtGui.QTableView()
        self.friends_view.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.friends_view.doubleClicked.connect(self._handle_friend_doubleclicked)
        self.friends_view.setSelectionBehavior(QtGui.QTableView.SelectRows)
        self.friends_view.setSelectionMode(QtGui.QTableView.SingleSelection)
        self.friends_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.friends_view.setAlternatingRowColors(True)
        self.friends_view.setSortingEnabled(True)

        self.friends_view.setModel(self.model.friends_list)
        self.model.friends_list.dataChanged.connect(self._handle_data_changed)
        self.model.friends_list.layoutChanged.connect(self.friends_view.resizeColumnsToContents)
        
        button = QtGui.QPushButton('Unfollow')
        button.clicked.connect(self._handle_unfollow_clicked)

        layout.addWidget(self.friends_view)
        layout.addWidget(button)

        central_widget = QtGui.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.resize(256, 600)

    @property 
    def window_title(self):
        """Return the title for the app window.
        
        Returns:
            str
        """

        return '{} (v{})'.format(self.model.app_name, self.model.app_version)

    @property 
    def window_icon(self):
        """Return the icon for the app window.

        Returns:
            QtGui.QIcon
        """

        here = os.path.dirname(__file__)
        icon_path = os.path.join(here, 'resources', 'icon.png')

        return QtGui.QIcon(icon_path)

    def closeEvent(self, event):
        """Handle this widget closing.

        Args:
            event (QtGui.QCloseEvent): The close event
        """

        self.Shutdown.emit()

        super(UnfriendlyWindow, self).closeEvent(event)

    def _handle_model_error(self, error_msg):
        """Handle an error message from the model.

        Args:
            error_msg (str): Text of the error message
        """

        QtGui.QMessageBox.critical(self, 'Error', error_msg, QtGui.QMessageBox.Ok)

    def _handle_data_changed(self):
        """Handle the user's friends list changing."""

        self.friends_view.repaint()

    def _handle_unfollow_clicked(self):
        """Handle a click on the 'Unfollow' button."""

        selected_rows = self.friends_view.selectionModel().selectedRows()

        for each in selected_rows:
            index = self.model.friends_list.index(each.row(), 0)
            user_id = self.model.get_user_id(index)

            self.UnfollowUser.emit(user_id)
            QtGui.QApplication.processEvents()

    def _handle_friend_doubleclicked(self, index):
        """Handle a double click on a row in the user table.

        Args:
            index (QtCore.QModelIndex): Index of the item clicked on.
        """

        user_name = self.model.get_user_name(index)

        self.ViewUserProfile.emit(user_name)    
