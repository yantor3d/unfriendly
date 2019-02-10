"""App model - local data and Twitter interaction."""

import datetime
import json
import os
import time

import tweepy
import tweepy.error 

from PySide import QtCore
from PySide import QtGui

_USER_NAME_ROLE = QtCore.Qt.UserRole + 1
_USER_ID_ROLE = QtCore.Qt.UserRole + 2
_SORT_ROLE = QtCore.Qt.UserRole + 3


class UnfriendlyModel(QtCore.QObject):
    """Data model for the application."""

    Error = QtCore.Signal(str)

    def __init__(self, app_name, app_version):
        """Initialize.

        Args:
            app_name (str): Name of the application.
            app_version (str): Version of the application.
        """

        super(UnfriendlyModel, self).__init__()

        self.app_name = app_name 
        self.app_version = app_version 

        self.friends_list = FriendsList()

        auth_keys = self._get_auth_keys()

        self._api = self._get_api(auth_keys)

        self._query = FriendsListQuery(self._api, auth_keys['user_name'])

        self._thread = QtCore.QThread()
        self._query.moveToThread(self._thread)
        self._query.Response.connect(self._handle_query_response)
        self._query.Timeout.connect(self._handle_query_timeout)

        self._thread.started.connect(self._query.start)
        self._thread.finished.connect(self._query.stop)
        self._thread.finished.connect(self._query.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

    def startup(self):
        """Run startup operations."""

        self._thread.start()

    def shutdown(self):
        """Run shutdown operations."""

        self._query.stop()

        self._thread.quit()
        self._thread.wait()

    def _handle_query_timeout(self, e):
        """Handle a query timeout error.
        
        Args:
            e (tweepy.error.RateLimitError): Timeout error exception
        """

        self.Error.emit(e.message[0]['message'])

    def _handle_query_response(self, user):
        """Add a user to the model.

        Args:
            user (tweepy.User): Model object for a Twitter user.
        """

        self.friends_list.add(user)

    @staticmethod
    def twitter_url(user_name):
        """Return the URL to the given user's profile page.

        Args:
            user_name (str): A twitter user's user name.
        
        Returns:
            str: A Twitter user's profile page URL
        """

        return os.path.join('https://twitter.com/', user_name)

    @staticmethod 
    def _get_auth_keys():
        """Return the auth keys dict.

        Returns:
            dict
        """

        here = os.path.abspath(os.path.dirname(__file__))

        with open(os.path.join(here, 'resources', '.twitter_keys.json'), 'r') as f:
            auth_keys = json.load(f)

        return auth_keys           
        
    @staticmethod
    def _get_api(auth_keys):
        """Return a Twitter API session.

        Args:
            auth_keys (dict): Twitter auth keys and access tokens.

        Returns:
            tweepy.API
        """

        auth = tweepy.OAuthHandler(
            auth_keys['consumer_key'],
            auth_keys['consumer_secret']
        )
        auth.set_access_token(
            auth_keys['access_token'],
            auth_keys['access_secret']
        )

        return tweepy.API(auth)    

    def unfollow_user(self, user_id):
        """Unfollow the user with the given id.

        Args:
            user_id (int): A Twitter user id.
        """

        try:
            self._api.destroy_friendship(user_id)
        except tweepy.error.TweepError as e:
            self.Error.emit(e.message[0]['message'])
        else:    
            self.friends_list.remove(user_id)

    def get_user_id(self, index):
        """Return the user id of the item at the given index.

        Args:
            index (QtCore.QModelIndex): Index of an item in the user view.
            
        Returns:
            int: A Twitter user id.
        """

        item = self.friends_list.item(index.row(), 0)
        user_id = item.data(_USER_ID_ROLE)

        return user_id 

    def get_user_name(self, index):
        """Return the user name of the item at the given index.

        Args:
            index (QtCore.QModelIndex): Index of an item in the user view.
            
        Returns:
            str: A Twitter user name.
        """

        item = self.friends_list.item(index.row(), 0)
        user_name = item.data(_USER_NAME_ROLE)

        return user_name 


class FriendsList(QtGui.QStandardItemModel):
    """Model for a user's friends list."""

    def __init__(self):
        """Initialize."""

        super(FriendsList, self).__init__()

        self.setSortRole(_SORT_ROLE)
        self.setHorizontalHeaderLabels(['Username', 'Last Tweet At'])

    def add(self, user):
        """Add a user to the model.

        Args:
            user (tweepy.User): Model object for a Twitter user.
        """
        
        timestamp = time.mktime(user.status.created_at.timetuple())
        last_tweet_at = datetime.datetime.fromtimestamp(timestamp)
        last_tweet_at = last_tweet_at.strftime('%m/%d/%Y %H:%M:%S')

        user_name_item = QtGui.QStandardItem(user.screen_name)
        last_tweet_item = QtGui.QStandardItem(last_tweet_at)

        user_name_item.setData(user.screen_name, _USER_NAME_ROLE)
        user_name_item.setData(user.screen_name, _SORT_ROLE)
        user_name_item.setData(user.id, _USER_ID_ROLE)

        last_tweet_item.setData(timestamp, _SORT_ROLE)        

        self.appendRow([user_name_item, last_tweet_item])

    def remove(self, user_id):
        """Remove the given user from the model.

        Args:
            user_id (int): A Twitter user id.
        """

        for row in range(self.rowCount()):
            item = self.item(row)

            if item.data(_USER_ID_ROLE) == user_id:
                self.takeRow(row)                
                print("You have unfollowed '{}'.".format(item.text()))
                break


class FriendsListQuery(QtCore.QObject):
    """Worker object. Queries the friends list of a user."""

    Response = QtCore.Signal(object)
    Timeout = QtCore.Signal(Exception)

    def __init__(self, api, user_name):
        """Initialize.

        Args:
            api (tweepy.API): Connection to the Twitter API
            user_name (str): Name of the user to query the friends of.
        """

        super(FriendsListQuery, self).__init__()

        self._api = api 
        self._user_name = user_name

        self._user_id = -1
        self._user_ids = []

        self._running = True 
        self._query_timer = None 

        self._query_func = None 
        self._query_arg = None

    def stop(self):
        """Stop the query."""

        self._running = False

    def start(self):
        """Start the query."""

        self._query_func = self._get_friends
        self._query_arg = self._user_name 

        self._query_timer = QtCore.QTimer()        
        self._query_timer.setSingleShot(True)
        self._query_timer.timeout.connect(self._query)

        self._query_timer.start(100)

    def _get_friends(self, user_name):
        """Get the friends of the given user.
        
        Args:
            user_name (str): A Twitter user name
        """

        try:
            self._user_ids = iter(self._api.friends_ids(user_name))
        except tweepy.error.RateLimitError as e:
            self.Timeout.emit(e)           
            self._retry(60)
        else:
            try:
                self._query_func = self._get_user
                self._query_arg = next(self._user_ids)
                self._query_timer.start(0)
            except StopIteration:
                pass     

    def _get_user(self, user_id):
        """Get the user with the given id.

        Args:
            user_id (int): A Twitter user id. 
        """

        try:
            user = self._api.get_user(user_id)
        except tweepy.error.RateLimitError as e:
            self.Timeout.emit(e)           
            self._retry(60)
        else:    
            self.Response.emit(user)

            try:
                self._query_arg = next(self._user_ids)
                self._query_timer.start(0)
            except StopIteration:
                pass

    def _query(self):
        """Perform the query."""

        if not self._running:
            return

        self._query_func(self._query_arg)

    def _retry(self, in_seconds):
        """Retry the last query in N seconds.

        Args:
            in_seconds (int): Number of seconds to wait before retrying.
        """   
        
        self._query_timer.start(in_seconds * 1000)
