import json, urllib.parse

def js_string_literal(s):
    return json.dumps(s)

def add_url_param(url, params={}):
    params = urllib.parse.urlencode(params)
    if "?" in url:
        return url + "&" + params
    else:
        return url + "?" + params

def set_url_param(url, params={}):
    tpl = url.split("?", 1)
    if len(tpl) == 2:
        url, query = tpl
        query = urllib.parse.parse_qs(query)
    else:
        query = {}
    
    for key, value in query.items():
        if len(value) == 1:
            query[key] = value[0]
    query.update(params)
    
    for key, value in params.items():
        if value is None:
            del query[key]
            
    return "%s?%s" % (url, urllib.parse.urlencode(query),)

