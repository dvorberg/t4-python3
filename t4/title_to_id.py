#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection.
##
##  Copyright 2011–22 by Diedrich Vorberg <diedrich@tux4web.de>
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

import sys, re, unicodedata, os.path as op

def asciify(string):
    '''
    "ASCIIfy" a Unicode string by stripping all umlauts, tildes, etc.

    This very cool function originates at
    http://www.physic.ut.ee/~kkannike/english/prog/python/index.html
    '''
    # Unfortunately, I don’t really understand, how this function works.
    # I have a hunch, this could be done better with a decomposed representation
    # of the string ("NFKD"), but I don’t have time to really test a function
    # as sensitive as this one right now.
    # To work reliably the way it is, strings must consist of composed
    # characters.
    string = unicodedata.normalize("NFC", string)

    temp = u''
    for char in string:
        decomp = unicodedata.decomposition(char)
        if decomp: # Not an empty string
            d = decomp.split()[0]
            try:
                temp += chr(int(d, 16))
            except ValueError:
                if d == "<super>":
                    temp += chr(int(decomp.split()[1], 16))
                else:
                    pass
                    #raise Exception("Can't handle this: " + repr(decomp))
        else:
            temp += char

    return temp


default_reserved_ids = ("image_slots edit set get download id fields "
                        "downloads image images fields slotinfo store "
                        "get_image has_image tag image_tag search translator"
                        ).split(" ")

def title_to_id(title, all_lowercase=True, reserved_ids=default_reserved_ids,
                separator="_"):
    """
    Convert a document title or menu entry to a filename.
    """
    title = str(title)

    if all_lowercase: title = title.lower()
    title = title.replace("ß", "ss")
    title = asciify(title)

    # Eigentlich nur für’s ELKG.
    title = title.replace("¹", "1")
    title = title.replace("²", "2")

    parts = [""]
    for char in title:
        if char in "abcdefghijklmnopqrstuvwxyz0123456789":
            parts[-1] += char
        else:
            if len(parts[-1]) > 0:
                parts.append("")

    if parts[-1] == "":
        parts = parts[:-1]

    id = separator.join(parts)
    id = id.encode("ascii", "ignore")

    if all_lowercase:
        id = id.lower()

    if id in reserved_ids:
        id = id.capitalize()

    return id.decode("ascii")



path_seps = { "/", "\\\\", ":", op.pathsep, op.altsep, }
if None in path_seps:
    path_seps.remove(None)

path_sep_re = re.compile("|".join(path_seps))

illegel_in_filename_re = re.compile(
    r"^\.|(\s*\.+\s+|/|\\|\.{2,}|:|!|#| |\"|'|\s)+")

def safe_filename(name, contains_dir=False, unicode_normalize_to="NFD"):
    if contains_dir:
        parts = path_sep_re.split(name)
        fn = parts[-1]
    else:
        fn = name

    ret = illegel_in_filename_re.sub(" ", name).strip()

    # The regular expression does not catch all cases in which someone
    # might try to inject a hidden file (starting with a .).
    while ret[0] == ".":
        ret = ret[1:]

    return unicodedata.normalize(unicode_normalize_to, ret)
