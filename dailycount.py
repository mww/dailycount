#!/usr/bin/env python
#
# Copyright 2010

import datetime
import functools
import logging
import os.path
import pytz
import tornado.locale
import tornado.web
import tornado.wsgi
import wsgiref.handlers

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db

class ConfigurationData(db.Model):
  title = db.StringProperty(unicode, required=True, multiline=False)
  description = db.TextProperty(required=True)
  ga_account_id = db.StringProperty(unicode, required=False, multiline=False)
  created = db.DateTimeProperty(auto_now_add=True)
  last_modified = db.DateTimeProperty(auto_now=True)
  last_modified_by = db.UserProperty()


class ItemType(db.Model):
  name = db.StringProperty(unicode, required=True, multiline=False)
  active = db.BooleanProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)


class CountedItem(db.Model):
  item_type = db.ReferenceProperty(ItemType)
  user = db.UserProperty(required=True)
  comment = db.StringProperty(unicode, required=False, multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  location = db.StringProperty(unicode, required=False, multiline=False)
  
  
class Location(db.Model):
  name = db.StringProperty(unicode, required=True, multiline=False)
  user = db.UserProperty(required=True)
  geo_pt = db.GeoPtProperty(required=True)
  active = db.BooleanProperty(required=True)


class UserOptions(db.Model):
  user = db.UserProperty(required=True)
  timezone = db.StringProperty(unicode, multiline=False)


def login_required(method):
  """Decorate with this method to restrict pages to logged in users."""
  @functools.wraps(method)
  def wrapper(self, *args, **kwargs):
    if not self.current_user:
      if self.request.method == 'GET':
        self.redirect(self.get_login_url())
        return
      raise tornado.web.HTTPError(403)
    else:
      return method(self, *args, **kwargs)
  return wrapper


def administrator(method):
  """Decorate with this method to restrict to site admins."""
  @functools.wraps(method)
  def wrapper(self, *args, **kwargs):
    if not self.current_user:
      if self.request.method == "GET":
        self.redirect(self.get_login_url())
        return
      raise tornado.web.HTTPError(403)
    elif not self.current_user.administrator:
      raise tornado.web.HTTPError(403)
    else:
      return method(self, *args, **kwargs)
  return wrapper


def get_current_config():
  """Get the current config, or return the defaults."""
  data = memcache.get('config_data')
  if data is not None:
    return data
  else:
    data = db.Query(ConfigurationData).order('-last_modified').get()
    if data:
      if not memcache.add('config_data', data, 30):
        logging.error('Error adding config_data to memcache.')
    else:
      """Set the default configuration data"""
      title = u'Daily Count'
      description = u'Track and graph all of your daily bodily functions. \
Sign in to get started.'
      data = ConfigurationData(title=title, description=description)
    return data


def get_user_options(user):
  """Get the UserOptions for the specified user.

  If there are no UserOptions for the user then create a default set.

  Arguments:
    user: The user to get the options for.

  Returns: The UserOptions for the specified user.
  """
  options = memcache.get('%s-options' % user.email())
  if options is not None:
    return options

  options = db.Query(UserOptions).filter('user =', user).get()
  if options is None:
    options = UserOptions(user=user)
    options.timezone = 'US/Pacific' # US/Pacific is the default timezone
    options.put()

  if not memcache.add('%s-options' % user.email(), options, 30):
    logging.error('Error adding user options to memcache for %s' % user.email())

  return options


def get_start_of_day_time(user):
  """Get the time, in UTC, of the start of the day of the user's timezone.

  Arguments:
    user: The user to get start of day time for.

  Returns: datetime of the start of the day for the user's timezone.
  """
  options = get_user_options(user)
  timezone = pytz.timezone(options.timezone)
  if timezone is None:
    logging.error('User %s has an invalid timezone: %s. Using US/Pacific.' %
        (user.nickname(), options.timezone))
    timezone = pytz.timezone('US/Pacific')
  current_time = datetime.datetime.now(tz=timezone)
  start_of_day = datetime.datetime.combine(current_time.date(),
      datetime.time(0, 0, 0, 0)).replace(tzinfo=timezone)
  return start_of_day.astimezone(pytz.utc)


class BaseHandler(tornado.web.RequestHandler):
  """Implement base functionality that most handles should have.

     This is almost entirely stolen from the tornado appengine example.
  """
  def get_current_user(self):
    user = users.get_current_user()
    if user:
      user.administrator = users.is_current_user_admin()
    return user

  def get_user_locale(self):
    # Let the user specify their locale using the hl parameter
    if 'hl' in self.request.arguments:
      hl = self.request.arguments['hl'][0]
      return tornado.locale.get(hl)
    return None

  def get_login_url(self):
    return users.create_login_url(self.request.uri)

  def get_logout_url(self):
    return users.create_logout_url('/')

  def render_string(self, template_name, **kwargs):
      data = get_current_config()
      return tornado.web.RequestHandler.render_string(
          self, template_name, config_data=data, **kwargs)


class AdminHandler(BaseHandler):
  @administrator
  def get(self):
    items = db.Query(ItemType).order('created').fetch(limit=100)
    self.render('admin.html', items=items)

  @administrator
  def post(self):
    # TODO(mww): error checking, change if an item is active or not
    title = self.get_argument('title', None)
    description = self.get_argument('description', None)
    ga_account_id = self.get_argument('ga_account_id', None)

    if title is None or description is None:
      logging.error('Both title and description are required params.')
      # TODO(mww): Find a more specific 500 to serve
      raise tornado.web.HTTPError(500)
      return

    data = get_current_config()
    data.title = title
    data.description = description
    data.ga_account_id = ga_account_id
    data.last_modified_by = self.get_current_user()

    data.put()
    memcache.replace('config_data', data, 30)
    self.redirect('/admin')


class CountItemHandler(BaseHandler):
  @login_required
  def post(self):
    type_name = self.get_argument('type', None)
    comment = self.get_argument('comment', None)
    location = self.get_argument('location', None)
    dbLoc = db.Query(Location).filter('name = ', location).get()
    locName = None
    if dbLoc:
      locName = dbLoc.name
    
    if type_name is None:
      logging.error('type pass to CountItemHandler is None')
      # TODO(mww): Find a more specific 500 to serve
      raise tornado.web.HTTPError(500)
      return

    q = db.Query(ItemType).filter('name = ', type_name)
    q.filter('active = ', True)
    item_type = q.get()
    if item_type is None:
      logging.error('No active type for name "%s" could be found.' % type_name)
      # TODO(mww): Find a more specific 500 to serve
      raise tornado.web.HTTPError(500)
      return

    user = self.get_current_user()
    counted_item = CountedItem(item_type=item_type,
                               user=user,
                               comment=comment,
                               location=locName)
    counted_item.put()

    q = db.Query(CountedItem)
    q.filter('user =', user)
    q.filter('item_type =', item_type)
    q.filter('date >', get_start_of_day_time(user))
    num = q.count()
    logging.info(
        'added new item of type: %s, comment: %s, loc: %s, new total: %d' %
        (item_type.name, comment, locName, num))
    self.write('%d' % num)


class CreateItemTypeHandler(BaseHandler):
  @administrator
  def post(self):
    name = self.get_argument("name", None)
    if name:
      name = tornado.escape.xhtml_escape(name.strip())
      item_type = ItemType(name=name, active=True)
      item_type.put()
      memcache.delete('active_types')
    self.write(name)


class DeleteItemHandler(BaseHandler):
  @login_required
  def post(self, id):
    item = CountedItem.get_by_id(int(id))
    if item.user != self.get_current_user():
      logging.error('User %s is not the owner for item %s - not deleting' %
          (self.get_current_user().email(), id))
      raise tornado.web.HTTPError(401)
      return
    item.delete()
    self.write('OK');


class MainHandler(BaseHandler):
  def get(self):
    if self.current_user:
      self.redirect('/user')
      return
    else:
      self.render('main.html')


class UserHandler(BaseHandler):
  @login_required
  def get(self):
    count_data = []
    active_types = memcache.get('active_types')
    if active_types is None:
      q = db.Query(ItemType).order('created').filter('active =', True)
      active_types = q.fetch(limit=5)
      if not memcache.add('active_types', active_types, 30):
        logging.error('Error adding active_types to memcache.')

    user = self.get_current_user()
    for item_type in active_types:
      q = db.Query(CountedItem)
      q.filter('user =', user)
      q.filter('item_type =', item_type)
      q.filter('date >=', get_start_of_day_time(user))
      num = q.count()
      count_data.append((item_type.name, num))
    self.render('user.html', data=count_data)


class LocationHandler(BaseHandler):
  @login_required
  def get(self):
    """Return all saved locations for this user and the one closest to
       the passed in coordinates.

    The results are returned in a JSON format that looks like:
    {
      "user_location": "Work Bathroom",
      "locations": ["Home Bathroom", "Work Bathroom", ...]
    }

    Returns: JSON formatted list of save locations, ant the name of
             the location closest to the passed in coordinates.
    """
    lat = self.get_argument('latitude', None)
    lon = self.get_argument('longitude', None)
    q = db.Query(Location)
    q.filter('user =', self.get_current_user())
    q.filter('active =', True)
    db_locs = q.fetch(100)
    locs = [];
    nearest_loc = None;
    best_compare = 10000000;
    if db_locs:
      for loc in db_locs:
        locs.append(loc.name)
        if lat and lon:
          compare = (abs(float(lat)-loc.geo_pt.lat) 
                     + abs(float(lon)-loc.geo_pt.lon))
          if compare < best_compare:
            best_compare = compare
            nearest_loc = loc.name
        
    locs_str = '[%s]' % ','.join('"%s"' %  x for x in locs)
    self.write('{"user_location": "%s", "locations": %s}' %
        (nearest_loc, locs_str))
    
  @login_required
  def post(self):
    name = self.get_argument('name', None)
    longitude = self.get_argument('longitude', None)
    latitude = self.get_argument('latitude', None)
    location = Location(name=name,
                        user=self.get_current_user(),
                        geo_pt=(latitude + ',' + longitude),
                        active=True)
    location.put()
    self.write('OK');


class ProfileHandler(BaseHandler):
  @login_required
  def get(self):
    q = db.Query(Location)
    q.filter('user =', self.get_current_user())
    q.filter('active =', True)
    db_locs = q.fetch(100)
    locs = [];
    if db_locs:
      for loc in db_locs:
        locs.append((loc.name, loc.geo_pt))
    options = get_user_options(self.get_current_user())
    self.render('profile.html', locations=locs, options=options)
    
  @login_required
  def post(self):
    user = self.get_current_user()
    timezone = self.get_argument('timezone', 'US/Pacific')
    logging.info('timezone for user %s set to %s' % (user.nickname(), timezone))
    options = get_user_options(user)
    options.timezone = timezone
    options.put()
    if not memcache.delete('%s-options' % user.email()):
      logging.error('Error deleting user options from memcache for user %s.' %
          user.email())
    self.redirect('/user/profile')


class UserHistoryHandler(BaseHandler):
  @login_required
  def get(self):
    user = self.get_current_user()
    options = get_user_options(user)
    timezone = pytz.timezone(options.timezone)
    q = db.Query(CountedItem).order('-date').filter('user =', user)
    history = q.fetch(limit=20)
    dates = []
    items = {}
    for item in history:
      datetime = item.date.replace(tzinfo=pytz.utc).astimezone(timezone)
      date_str = datetime.strftime('%A %B %d, %Y')
      time_str = datetime.strftime('%I:%M %p')
      if not date_str in items:
        dates.append(date_str)
        items[date_str] = []
      items[date_str].append({'time': time_str, 'id': item.key().id(),
          'type_name': item.item_type.name, 'comment': item.comment, 'location': item.location})
    self.render('history.html', dates=dates, history=items)


class UserTimeZonesHandler(BaseHandler):
  @login_required
  def get(self):
    """Return the supported time zones and the current users timezone.

    The results are returned in a JSON format that looks like:
    {
      "user_timezone": "US/Pacific",
      "timezones": ["Africa/Abidjan", "Africa/Accra", ...]
    }

    Returns: JSON formatted list of supported time zones, and the user's
             selection.
    """
    timezones = memcache.get('timezones')
    if timezones is None:
      timezones = '[%s]' % ','.join('"%s"' %  x for x in pytz.common_timezones)
      if not memcache.add('timezones', timezones, 60):
        logging.error('Error adding timezones to memcache.')

    options = get_user_options(self.get_current_user())
    self.write('{"user_timezone": "%s", "timezones": %s}' %
        (options.timezone, timezones))
    
    
if __name__ == "__main__":
  settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
  }

  application = tornado.wsgi.WSGIApplication([
    (r'/', MainHandler),
    (r'/admin', AdminHandler),
    (r'/admin/createitemtype', CreateItemTypeHandler),
    (r'/user', UserHandler),
    (r'/user/countitem', CountItemHandler),
    (r'/user/history/?', UserHistoryHandler),
    (r'/user/item/(\d+)/delete', DeleteItemHandler),
    (r'/user/location', LocationHandler),
    (r'/user/profile', ProfileHandler),
    (r'/user/profile/timezones/?', UserTimeZonesHandler),
  ], **settings)

  wsgiref.handlers.CGIHandler().run(application)