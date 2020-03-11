import random
import re
import requests

PROXY_LIST = []             # Current list of proxy servers to choose from
RECENT_PROXIES = []         # Recently used proxies (to avoid using too often)
BROKEN_PROXIES = []         # Known-bad proxies (we want to void choosing these)
RECENT_MAX = 30

# Proxy settings that can be conrolled via ENV variables
PROXY_TIMOUT_LIMIT = os.getenv('PROXY_TIMOUT_LIMIT', "2000")
proxy_list_env_var = os.getenv('PROXY_LIST', None)
if proxy_list_env_var:
    # Manually set PROXY_LIST from ENV variable (a ;-sparated list of proxies)
    PROXY_LIST = proxy_list_env_var.split(';')


def get_proxyscape_proxies():
    """Loads a list of `{ip_address}:{port}` for public proxy servers."""
    url = 'https://api.proxyscrape.com/?request=getproxies'
    url += '&proxytype=http&country=all&ssl=yes&anonymity=all'
    url += '&timeout=' + PROXY_TIMOUT_LIMIT
    r = requests.get(url)
    return r.text.split('\r\n')


def get_sslproxies_proxies():
    r = requests.get('https://sslproxies.org')
    matches = re.findall(r"<td>\d+\.\d+\.\d+\.\d+</td><td>\d+</td>", r.text)
    revised = [m.replace('<td>', '') for m in matches]
    proxies = [s.replace('</td>', ':')[:-1] for s in revised]
    return proxies


def get_proxies(refresh=False):
    global PROXY_LIST
    if len(PROXY_LIST) == 0 or refresh:
        PROXY_LIST = get_proxyscape_proxies()

    return PROXY_LIST


def choose_proxy():
    global RECENT_PROXIES

    proxies = get_proxies()

    chosen = False
    proxy = None
    max_attempts = 30
    retry_attempts = 10
    attempt = 0
    attempts_made = 0
    while not chosen:
        proxy = proxies[random.randint(0, len(proxies) - 1)]
        if not proxy in RECENT_PROXIES + BROKEN_PROXIES:
            chosen = True
            RECENT_PROXIES.append(proxy)
            if len(RECENT_PROXIES) > RECENT_MAX:
                RECENT_PROXIES.pop(0)
        else:
            attempt += 1
            attempts_made += 1
            if attempts_made > max_attempts:
                break

            # Some chefs can take hours or days, so our proxy list
            # may be stale. Try refreshing the proxy list.
            if attempt == retry_attempts:
                attempt = 0
                proxies = get_proxies(refresh=True)

    return proxy


def add_to_broken_proxy_list(proxy):
    global BROKEN_PROXIES
    if not proxy in BROKEN_PROXIES:
        BROKEN_PROXIES.append(proxy)


def reset_broken_proxy_list():
    global BROKEN_PROXIES
    BROKEN_PROXIES = []
