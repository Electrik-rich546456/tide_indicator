#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime


class Reading( object ):
    # date: Date of reading, as a string.
    # time: Time of reading, as a string.
    # location: Name of port or place.
    # level: The tide level, as a string.
    # isHigh: True if the tide is high; false otherwise.
    # url: The URL used to source the tide information.
    def __init__( self, date, time, location, isHigh, level, url ):
        self.date = date
        self.time = time
        self.location = location
        self._isHigh = isHigh
        self.level = level
        self.url = url


    def getDate( self ):
        return self.date


    def getTime( self ):
        return self.time


    def getLocation( self ):
        return self.location


    # Returns true if tide is high; false otherwise.
    def isHigh( self ):
        return self._isHigh


    # Returns the level of this tide.
    def getLevel( self ):
        return self.level


    def getURL( self ):
        return self.url


    def __str__( self ):
        return \
            self.date + " | " + \
            self.time + " | " + \
            self.location + " | " + \
            str( self._isHigh ) + " | " + \
            str( self.level ) + " | " + \
            self.url


    def __repr__( self ):
        return self.__str__()


    def __eq__( self, other ):
        return \
            self.__class__ == other.__class__ and \
            self.getDate() == other.getDate() and \
            self.getTime() == other.getTime() and \
            self.getLocation() == other.getLocation() and \
            self.isHigh() == other.isHigh() and \
            self.getLevel() == other.getLevel() and \
            self.getURL() == other.getURL()