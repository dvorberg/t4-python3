import datetime, re

opening_quote_re = re.compile(r'(\s+|^)"([0-9a-zA-Z])')
closing_quote_re = re.compile(r'(\S+)"(\s+|$|[,\.;!])')
opening_single_quote_re = re.compile(r"(\s+|^)'([0-9a-zA-Z])")
closing_single_quote_re = re.compile(r"([^\s']+)'(\s+|$|[,\.;!])")
date_until_re = re.compile(r'(\d+)\.-(\d+)\.')

def improve_typography(content, lang="de"):
    if lang == "de":
        # "gerade" und ,,typografische'' Anführungszeichen    
        content = re.sub(opening_quote_re, u"\\1„\\2", content)
        content = re.sub(closing_quote_re, u"\\1“\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‚\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1‘\\2", content)
    elif lang == "en":
        content = re.sub(opening_quote_re, u"\\1“\\2", content)
        content = re.sub(closing_quote_re, u"\\1”\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‘\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1’\\2", content)
    elif lang == "fr":
        content = re.sub(opening_quote_re, u"\\1«\\2", content)
        content = re.sub(closing_quote_re, u"\\1»\\2", content)
        content = re.sub(opening_single_quote_re, u"\\1‹\\2", content)
        content = re.sub(closing_single_quote_re, u"\\1›\\2", content)
    else:
        pass

    # Converts 1.-2. into 1.–2. (with a proper 'until' dash)
    content = re.sub(date_until_re, r"\1.–\2.", content)

    # Put long dashes where they (might) belog
    content = content.replace(u" - ", u" — ")

    # Ellipsis
    content = content.replace(" ...", " …")
    content = content.replace("...", "…")
    
    return content



def pretty_bytes(bytes):
    if bytes < 1024:
        return str(bytes) + " Bytes"
    if bytes < 1024*1024:
        return "%i KB" % (bytes/1024)
    if bytes < 1024*1024*1024:
        return "%.1f MB" % ( float(bytes) / (1024*1024) )
    if bytes < 1024*1024*1024*1024:
        return "%.1f GB" % ( float(bytes) / (1024*1024*1024) )
    else:
        return "%.1f TB" % ( float(bytes) / (1024*1024*1024*1024) )

def parse_duration(s):
    parts = s.split(":")
    parts = list(map(float, parts))

    ret = 0.0
    counter = 0
    while parts:
        ret += parts.pop() * (60.0**counter)
        counter += 1

    return ret

def pretty_duration(f):
    if f is None:
        return "–"
    elif f == "":
        return "xx:xx"
    else:
        f = int(f)
        seconds = f % 60
        minutes = (f / 60) % 60
        hours = int(f / 3600)

        if hours > 0:
            return "%02i:%02i:%02i" % ( hours, minutes, seconds, )
        else:
            return "%02i:%02i" % ( minutes, seconds, )

monat = [ None, "Januar", "Februar", "März", "April", "Mai",
          "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember", ]

def pretty_german_date(pit, with_time=False, with_timezone=False,
                       monthname=False):
    """
    Return a pretty representation of this date.
    """
    if pit is None:
        return ""

    if with_time:
        r = "%s.%s.%s %02i:%02i Uhr" % ( pit.day, pit.month, pit.year,
                                         pit.hour, pit.minute, )
    else:
        if monthname:
            r = "%s. %s %s" % ( pit.day, monat[pit.month], pit.year, )
        else:
            r = "%s.%s.%s" % ( pit.day, pit.month, pit.year, )

    if with_timezone:
        r += " (%s)" % pit.timezone

    return r

german_date_re = re.compile(r"(\d+)\.(\d+)\.(\d{4})")
def parse_german_date(s):
    match = german_date_re.match(s)
    if match is None:
        raise ValueError(s)
    else:
        day, month, year = [ int(n) for n in match.groups() ]
        return datetime.date(year, month, day)

    
