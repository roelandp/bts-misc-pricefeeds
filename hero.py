#! /usr/bin/env python3
from getpass import getpass
from bitshares.price import Price
from bitshares.market import Market
from datetime import date

# USD:BTS price
market = Market("USD:BTS")
price = market.ticker()["quoteSettlement_price"]
price.invert()  # invert to allow easier multiplication

# HERO:USD price
hero_usd = (1.05 ** ((date.today() - date(1913, 12, 23)).days / 365.2425))
hero = Price(hero_usd, "USD/HERO")

# HERO:BTS price
hero_bts = price * hero

print("Price of HERO in USD: {}".format(hero))
print("Price of USD in BTS: {}".format(price))
print("Price of HERO in BTS: {}".format(hero_bts))

# unlock wallet
market.bitshares.wallet.unlock("YOUR UPTICK WALLET UNLOCK CODE")
print(market.bitshares.publish_price_feed(
    "HERO",
    hero_bts,
    account="roelandp"
))
