import re
import urllib.request
import FitstCrawler
import urllib.parse
import urllib.robotparser
import lxml.html
import Throttle

def link_crawler(seed_url, link_regex=None, delay=5, max_depth=-1, max_urls=-1, headers=None, user_agent='wswp',
                 proxy=None, num_retries=1, scrape_callback=None):


    crawl_queue = [seed_url]
    seen = {seed_url:0}

    num_urls = 0
    rp = get_robots(seed_url)
    throttle = Throttle.Throttle(delay)
    headers = headers or {}
    if user_agent:
        headers['User-agent'] = user_agent

    while crawl_queue:
        url = crawl_queue.pop()

        depth = seen[url]

        if rp.can_fetch(user_agent, url):
            throttle.wait(url)
            html = download(url, headers, proxy=proxy, num_retries=num_retries)
            links =[]
            if scrape_callback:
                links.extend(scrape_callback(url, html) or [])

            if depth != max_depth:
                if link_regex:
                    links.extend(link for link in get_links(html) if re.match(link_regex, link))

                for link in links:
                    link = normalize(seed_url, link)

                    if link not in seen:
                        seen[link] = depth + 1
                        if same_domain(seed_url, link):
                            crawl_queue.append(link)
                            # check whether have reached downloaded maximum
        num_urls += 1
        if num_urls == max_urls:
            break
    else:
        print('Blocked by robots.txt:' + url)
def get_robots(url):
    """Initialize robots parser for this domain
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urllib.parse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp

def get_links(html):
    """Return a list of links from html
    """
    # a regular expression to extract all links from the webpage
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    # list of all links from the webpage
    return webpage_regex.findall(html)

def lxml_scraper(html):
    FIELDS = {'ares', 'population', 'iso', 'country', 'capital',
              'continent', 'tld', 'currency_code', 'currency_name', 'phone'
              'postal_code_format', 'postal_code_regex', 'languages', 'neighbours'}

    tree = lxml.html.fromstring(html)
    result = {}
    for field in FIELDS :
        result[field] = tree.cssselect('table > tr#places_%s__row > td.w2p_fw'  % field)[0].text_content()

    return  result

def download(url, headers, proxy, num_retries, data=None):
    print ('Downloading:' +  url)
    request = urllib.request.Request(url, data, headers)
    opener = urllib.request.build_opener()
    if proxy:
        proxy_params = {urllib.parse.urlparse(url).scheme: proxy}
        opener.add_handler(urllib.request.ProxyHandler(proxy_params))
    try:
        response = opener.open(request)
        html = response.read().decode('utf-8')
        code = response.code
    except urllib.request.URLError as e:
        print('Download error:' + e.reason)
        html = ''
        if hasattr(e, 'code'):
            code = e.code
            if num_retries > 0 and 500 <= code < 600:
                # retry 5XX HTTP errors
                html = download(url, headers, proxy, num_retries - 1, data)
        else:
            code = None
    return html

def normalize(seed_url, link):
    """Normalize this URL by removing hash and adding domain
    """
    link, _ = urllib.parse.urldefrag(link)  # remove hash to avoid duplicates
    return urllib.parse.urljoin(seed_url, link)


def same_domain(url1, url2):
    """Return True if both URL's belong to same domain
    """
    return urllib.parse.urlparse(url1).netloc == urllib.parse.urlparse(url2).netloc

