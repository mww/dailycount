#!/usr/bin/env python
#
# Copyright 2010

import functools
import logging
import os.path
import tornado.locale
import tornado.web
import tornado.wsgi
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import db

class ItemType(db.Model):
  name = db.StringProperty(required=True)
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


class AdminHandler(BaseHandler):
  @administrator
  def get(self):
    self.render('admin.html')


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
    self.render('user.html')


if __name__ == "__main__":
  settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
  }

  application = tornado.wsgi.WSGIApplication([
    (r'/', MainHandler),
    (r'/admin', AdminHandler),
    (r'/user', UserHandler),
  ], **settings)

  wsgiref.handlers.CGIHandler().run(application)
