#! /usr/bin/env python3
from getpass import getpass
from bitshares.price import Price
from bitshares.market import Market
from bitshares.account import Account
from bitsharesbase import memo as BtsMemo

from bitshares.account import Account
from bitsharesbase.account import PrivateKey, PublicKey

import json
# import re
# import pendulum
import requests

account_b20 = Account("bittwenty.feed")
account_history_b20 = account_b20.history(0,10,20)

# `announce`-user memo privkey to decypher memo msgs: 5KJJNfiSyzsbHoVb81WkHHjaX2vZVQ1Fqq5wE5ro8HWXe6qNFyQ

wifkey_announce = "5KJJNfiSyzsbHoVb81WkHHjaX2vZVQ1Fqq5wE5ro8HWXe6qNFyQ"

def is_valid_bit20_publication(trx):
    """
    check that the transaction is a valid one, ie:
      - it contains a single operation
      - it is a transfer from 'bittwenty' (1.2.111226) to 'bittwenty.feed' (1.2.126782)
    note: this does not check the contents of the transaction, it only
          authenticates it
    """
    try:
        # we only want a single operation
        if len(trx['op']) != 2:  # (trx_id, content)
            return False

        # authenticates sender and receiver
        trx_metadata = trx['op'][1]
        if trx_metadata['from'] != '1.2.111226':  # 'bittwenty'
            print('invalid sender for bit20 publication: {}'.format(json.dumps(trx, indent=4)))
            return False
        if trx_metadata['to'] != '1.2.126782':  # 'bittwenty.feed'
            print('invalid receiver for bit20 publication: {}'.format(json.dumps(trx, indent=4)))
            return False

        return True

    except KeyError:
        # trying to access a non-existent field -> probably looking at something we don't want
        print('invalid transaction for bit20 publication: {}'.format(json.dumps(trx, indent=4)))
        return False



for f in account_history_b20:

    if not is_valid_bit20_publication(f):
        print('Hijacking attempt of the bit20 feed? trx: {}'.format(json.dumps(f, indent=4)))
        continue

    memo = f['op'][1]['memo']

    privkey = PrivateKey(wifkey_announce)
    pubkey  = PublicKey(Account(f['op'][1]['from'])['options']['memo_key'])
    memomsg = BtsMemo.decode_memo(privkey, pubkey, memo["nonce"], memo["message"])

    #print(memomsg)
    if memomsg.startswith('COMPOSITION'):
        # last_updated = re.search('\((.*)\)', memomsg)
        # if last_updated:
        #     last_updated = pendulum.from_format(last_updated.group(1), '%Y/%m/%d')
        #     #print(last_updated)
        bit20 = json.loads(memomsg.split(')', maxsplit=1)[1])
        break

else:
    print("Did not find any bit20 composition in the last {} messages to account bittwenty.feed".format(len(bit20feed)))


if len(bit20['data']) < 3:
    print("Not enough assets in bit20 data: {}".format(bit20['data']))
    exit()

#print(bit20['data'])

# getting COINMARKETCAP prices.
cmcurl = "https://api.coinmarketcap.com/v1/ticker/"
cmcparams = {
    "start": 0,
    "limit": 1000,
}

cmcresp = requests.get(url=cmcurl, params=cmcparams)
cmcdata = json.loads(cmcresp.text)

# morphing COINMARKETCAP prices.
coinmarketcapassets = {}
for coin in cmcdata:
    coinsymbol = coin["symbol"]
    coinmarketcapassets[coinsymbol] = coin["price_usd"]

# getting COINCAP prices.
ccurl = "http://coincap.io/front"

ccresp = requests.get(url=ccurl)
ccdata = json.loads(ccresp.text)

# morphing COINCAP prices.
coincapassets = {}
for coin in ccdata:
    coinsymbol = coin["short"].replace('IOT','MIOTA')
    coincapassets[coinsymbol] = coin["price"]

bit20_value_cmc = 0
cmc_missing_assets = []
bit20_value_cc = 0
coincap_missing_assets = []

# looping thru bit20assets finding prices in both sources.
for bit20asset, qty in bit20['data']:
    print(bit20asset , qty)

    try:
        if coincapassets[bit20asset]:
            bit20_value_cc += float(coincapassets[bit20asset]) * qty
    except:
        coincap_missing_assets.append(bit20asset)

    try:
        if coinmarketcapassets[bit20asset]:
            bit20_value_cmc += float(coinmarketcapassets[bit20asset]) * qty
    except:
        cmc_missing_assets.append(bit20asset)


print(len(coincap_missing_assets))
print(len(cmc_missing_assets))

# compile final feedprice
feeds = []
if len(coincap_missing_assets) == 0:
    feeds.append(bit20_value_cc)
if len(cmc_missing_assets) == 0:
    feeds.append(bit20_value_cmc)

if len(feeds) > 0:
    average = 0
    for feed in feeds:
        average += feed

    price_to_publish_in_usd = average/len(feeds)

    # GETTING USD BTS PRICE USD:BTS price
    market = Market("BTS:USD")
    price = market.ticker()['baseSettlement_price']
    print(price)
    price.invert()  # invert to allow easier multiplication

    # BTS:USD price
    one_usd_bts = price

    priceinbts = price_to_publish_in_usd * one_usd_bts['price']
    pricempa = Price("{} BTS/BTWTY".format(priceinbts))

    print(pricempa)

    #unlock wallet...
    market.bitshares.wallet.unlock("YOUR UPTICK WALLET UNLOCK CODE")

    (market.bitshares.publish_price_feed(
        symbol = "BTWTY",
        settlement_price = pricempa,
        cer = pricempa * (1/1.2),
        mcr = 175,
        account="roelandp",

    ))

else:
    print('NOT PUBLISHING, NO COMPLETE FEEDS AVAIL.')
