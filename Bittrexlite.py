import json
import hmac
import hashlib
import logging
import requests
from requests import ConnectionError
import time
import os

ENDPOINT = 'https://api.bittrex.com/v3'

#if the API id data is stored as enviroment variable (recommended method)

# APIid = {'key': os.environ.get('BITTREX_KEY'),
#          'secret': os.environ.get('BITTREX_SECRET')}

# if you want to hard code the API data directly (not recommended)

APIid = {'key': "YOUR_API_KEY_HERE",
         'secret': "YOUR_API_SECRET_HERE"}


# this module that allows to make public and private requests to the Bittrex v3 API


def request(method, path, params=None):
    try:
        resp = requests.request(method, ENDPOINT + path, params=params)
        data = resp.json()
        if "msg" in data:
            logging.error(data['msg'])
        return data
    except ConnectionError as e:
        logging.error(e)
        return {}

def signedRequest(method, path, params=None):
    """
    makes an authenticated request to Bittrex Rest API
    :param method: request method
    :param path: URL path
    :param params: request content
    """
    if "key" not in APIid or "secret" not in APIid:
        raise ValueError("Api key and secret must be set")

    timestamp = format(int(time.time() * 1000))
    secret = bytes(APIid["secret"].encode("utf-8"))
    content = json.dumps(params, separators=(",", ":")) if params else ''
    contenthash = hashlib.sha512(content.encode("utf-8")).hexdigest()
    presign = f'{timestamp}{ENDPOINT}{path}{method}{contenthash}'
    signature = hmac.new(secret, presign.encode("utf-8"), hashlib.sha512).hexdigest()
    resp = requests.request(method,
                            ENDPOINT + path, data=content,
                            headers={"Api-Key": APIid["key"],
                                     'Content-Type': 'application/json',
                                     "Api-Timestamp": timestamp,
                                     "Api-Content-Hash": contenthash,
                                     "Api-Signature": signature
                                     })
    try:
        data = resp.json()
    except Exception as e:
        print(f'Exception: {e}')
        data = e

    return data


def balances(symbol=''):
    """
    Get current balances for one or all symbols.
    :param symbol: currency symbol
    """
    method = 'GET'
    path = '/balances' if symbol == '' else f'/balances/{symbol}'
    data = signedRequest(method, path)
    return data

def tickers(symbol = ''):
    """
    Get latest prices for one or all symbols.
    :param symbol: currency symbol i.e.g RVN-BTC, if left empty returns last price for all symbols
    """
    symbol = str(symbol)
    symbol = symbol.replace(" ", '')
    method = 'GET'
    path = '/markets/tickers' if symbol == '' else f'/markets/{symbol}/ticker'
    data = request(method, path)
    if type(data) == list:
        return data
    else:
        if 'symbol' in data.keys():
            return data
        elif 'code' in data.keys():
            symbol = list(symbol)
            symbol.insert(-3, '-')
            symbol = ''.join(symbol)
            path = f'/markets/{symbol}/ticker'
            data = request(method, path)
            if 'symbol' in data.keys():
                return data
            elif 'code' in data.keys():
                symbol = list(symbol)
                symbol.pop(-4)
                symbol.insert(-4, '-')
                symbol = ''.join(symbol)
                path = f'/markets/{symbol}/ticker'
                data = request(method, path)
                if 'symbol' in data.keys():
                    return data
                elif 'code' in data.keys():
                    return data['code']

