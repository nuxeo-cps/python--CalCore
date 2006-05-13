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

"""Some utility functions"""

def removeOverlaps(sequence):
    """Remove any overlapping tuples from sequence of start, end tuples.

    Returns list of non-overlapping tuples, having merged overlapping
    tuples.
    """
    # first deal with empty sequences
    if not sequence:
        return sequence
    sequence.sort()
    # removing overlaps
    last_start, last_end = sequence[0]
    result = []
    for i in range(1, len(sequence)):
        start, end = sequence[i]
        if start <= last_end:
            if end <= last_end:
                # complete overlap, skip this one
                continue
            # half overlap, so extend last one
            last_end = end
            continue
        # no overlap with last, so last is okay
        result.append((last_start, last_end))
        last_start = start
        last_end = end
    # add last one
    result.append((last_start, last_end))
    return result
