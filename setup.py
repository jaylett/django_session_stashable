#!/usr/bin/env python

from distutils.core import setup

setup(name='django-session-stashable',
      version='1.0',
      description='Django model mixin that makes it easy to manage a list of '
                  'objects associated with the current session.',
      author='James Aylett',
      url='https://github.com/jaylett/django_session_stashable',
      packages=['django_session_stashable']
    )
