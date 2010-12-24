#!/usr/bin/env python
#
# Copyright 2010

import datetime
import functools
import logging
import os.path
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
  date = db.DateTimeProperty(auto_now_add=True)


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
        logging.error('error adding config_data to memcache.')
    else:
      """Set the default configuration data"""
      title = u'Daily Count'
      description = u'Track and graph all of your daily bodily functions. \
  Sign in to get started.'
      data = ConfigurationData(title=title, description=description)
    return data


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
  def get(self):
    type_name = self.get_argument('type', None)

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

    counted_item = CountedItem(item_type=item_type,
                               user=self.get_current_user())
    counted_item.put()

    q = db.Query(CountedItem)
    q.filter('user =', self.get_current_user())
    q.filter('item_type =', item_type)
    q.filter('date >', datetime.date.today())
    num = q.count()
    logging.info('added new item of type: %s, new total: %d' %
        (item_type.name, num))
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
    for item_type in active_types:
      q = db.Query(CountedItem)
      q.filter('user =', self.get_current_user())
      q.filter('item_type =', item_type)
      q.filter('date >=', datetime.date.today())
      num = q.count()
      count_data.append((item_type.name, num))
    self.render('user.html', data=count_data)


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
  ], **settings)

  wsgiref.handlers.CGIHandler().run(application)
