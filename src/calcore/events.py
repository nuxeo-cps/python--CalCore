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

from zope.interface import implements

from interfaces import IEventEvent, IEventCreatedEvent, IEventDeletedEvent, \
     IEventModifiedEvent, IEventParticipationChangeEvent

class EventEvent(object):
    
    implements(IEventEvent)
    
    def __init__(self, event):
        self.event = event


class EventCreatedEvent(EventEvent):

    implements(IEventCreatedEvent)


class EventModifiedEvent(EventEvent):

    implements(IEventModifiedEvent)


class EventDeletedEvent(EventEvent):
    
    implements(IEventDeletedEvent)
    

class EventParticipationChangeEvent(EventModifiedEvent):
    
    implements(IEventParticipationChangeEvent)

    def __init__(self, event, attendee, old_status, new_status):
        self.event = event
        self.attendee = attendee
        self.old_status = old_status
        self.new_status = new_status
