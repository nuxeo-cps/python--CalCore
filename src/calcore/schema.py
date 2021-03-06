# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

# a bit of schema stuff not supported by Zope X3.0.0
# Zope 3 trunk schema does support this

from zope.interface import implements
from zope.schema._bootstrapfields import Field, Orderable
from datetime import timedelta, time

from zope.schema.interfaces import IMinMax, IField

class ITimedelta(IMinMax, IField):
    u"""Field containing a timedelta."""
    
class Timedelta(Orderable, Field):
    __doc__ = ITimedelta.__doc__
    implements(ITimedelta)
    _type = timedelta

class ITime(IMinMax, IField):
    u"""Field containing a timedelta."""
    
class Time(Orderable, Field):
    __doc__ = ITime.__doc__
    implements(ITime)
    _type = time

