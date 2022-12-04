import datetime, re, html, decimal

from .sql import normalize_whitespace

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

def add_web_paragraphs(s, use_ps=True):
    """
    Make a text appear in plain HTML circa what one would expect when using
    <ENTER> in a <textarea>. When use_ps= is true, paragraphs split by two
    newlines will be wrapped in <p>s. Otherwise the input text will be treated
    as a single paragraph. The input must not contain html, because it will
    be quoted.
    """
    s = html.escape(s)

    s = s.replace("\r\n", "\n")
    s = s.replace("\r", "\n")
    ps = s.split("\n\n")

    ps = [p.replace("\n", "<br />\n") for p in ps]

    if use_ps:
        ps = ["<p>" + p + "</p>" for p in ps]

    return "\n\n".join(ps)

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

    if monthname:
        r = "%s. %s %s" % ( pit.day, monat[pit.month], pit.year, )
    else:
        r = "%s.%s.%s" % ( pit.day, pit.month, pit.year, )

    if with_time:
        r += ", %02i.%02i Uhr" % ( pit.hour, pit.minute, )

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


def parse_german_float(s):
    """
    Parse a string containing a German float-point number (.s separate
    1000s, and decimal comma) into a float.
    """
    if type(s) is str:
        # Replace , with .
        s = s.replace(",", ".")

        # Remove all .s except the last one.
        parts = s.split(".")
        if len(parts) > 2:
            s = ".".join(parts[:-1]) + "." + parts[-1]

    return float(s)

def pretty_german_float(f, decimals=2, form=False):
    """
    Return a German representation of a float point number as a
    string.
    """
    if type(f) != float and not isinstance(f, decimal.Decimal):
        if form:
            if f is None:
                return ""
            else:
                try:
                    f = parse_german_float(f)
                except ValueError:
                    return f
        else:
            raise TypeError("Don’t know how to convert " + str(type(f)))

    # f = float(f) Don’t do that. If this is a decimal.Decimal, we’d loose
    # precision!

    if f < 0:
        negative = True
        f *= -1
    else:
        negative = False

    s = "%f" % f
    euros, cents = s.split(".")

    while cents.endswith("0"):
        cents = cents[:-1]

    if cents:
        s = euros + "," + cents
    else:
        s = euros

    if negative:
        return "-" + s
    else:
        return s
