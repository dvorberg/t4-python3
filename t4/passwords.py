#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2011–21 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
##  I have added a copy of the GPL in the file COPYING

import sys, os, os.path as op, types, subprocess, threading, random, itertools
from string import *
from types import *

def apple_style_random_password(groupnum=4, grouplength=3):
    letters = "ABCDEFGHJKLMNPQRSTUVWYXZabcdefghijkmnpqrstuvwyxz"
    digits = "0123456789"
    characters = letters + digits

    def groups():
        while True:
            yield "".join(random.sample(characters, grouplength))

    groups = itertools.islice(groups(), groupnum)
    return "-".join(groups)
    

password_specials = "+-/*!&;$,@"
def random_password(length=8, use_specials=True):
    letters = "ABCDEFGHJKLMNPQRSTUVWYXZabcdefghijkmnpqrstuvwyxz"
    digits = "0123456789"
    characters = letters + digits

    ret = []
    ret.append(random.choice(letters))
    for a in range(length-1):
        ret.append(random.choice(characters))

    if use_specials and length > 2:
        ret = ret[:-1]
        idx = random.randint(1, length-2)
        ret.insert(idx, random.choice(password_specials))
            
    return "".join(ret)

def password_good_enough(password):
    if len(password) < 8:
        return False
        
    def contains_one_of(s):
        for a in s:
            if a in password:
                return True
        else:
            return False

    return contains_one_of("ABCDEFGHJKLMNPQRSTUVWYXZ") and \
        contains_one_of("abcdefghijkmnpqrstuvwyxz") and \
        contains_one_of("0123456789") and \
        contains_one_of(password_specials) 

def slug(length=10):
    return random_password(length, False)
