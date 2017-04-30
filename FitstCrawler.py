import urllib.request
def download(url, user_agent='wswp', num_retries=2):
    print("Downloading " + url)

    headers = {'User-Agent':user_agent}

    request = urllib.request.Request(url=url, headers=headers)

    try:
        html = urllib.request.urlopen(request).read().decode("utf-8")
    except urllib.request.HTTPError as e :
        html = None
        if num_retries > 0 :
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, user_agent=user_agent, num_retries=num_retries-1)

    return html

