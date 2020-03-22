# coding=utf-8
from mws import mws
import pandas as pd
import time
import json
import argparse
import os


MWD_CREDENTIALS = {
    "MWS_ACCOUNT_ID": os.environ.get("MWS_ACCOUNT_ID"),
    "MWS_ACCESS_KEY" : os.environ.get("MWS_ACCESS_KEY"),
    "MWS_SECRET_KEY": os.environ.get("MWS_SECRET_KEY"),
    "MWS_MARKETPLACE_IDS": os.environ.get("MWS_MARKETPLACE_IDS").split(",")
}
SELECTED_COLS = [
    'AmazonOrderId','MarketplaceId','PurchaseDate','BuyerEmail', 
    'BuyerName', 'ShipmentServiceLevelCategory','OrderStatus', 
    'NumberOfItemsShipped', 'OrderTotal_amount' , 'OrderTotal_currency'
]
SHIPPING_FIELDS = ['AddressLine1', 'AddressLine2', 'City', 'CountryCode', 'Name', 'PostalCode']
THROTTLED_WAITING_TIME = 60


def get_clean_order_list(order_list):
    """Reducing the number of levels in JSON raw orders to 1."""
    clean_list = list()
    for order in order_list:
        o = dict()

        # Currency fields
        if 'OrderTotal' in order.keys():
            o['OrderTotal_amount'] = float(order['OrderTotal']['Amount']['value'])
            o['OrderTotal_currency'] = order['OrderTotal']['CurrencyCode']['value']

        # General fields
        general_fields = order.keys()
        for f in general_fields:
            if f in order.keys():
                if 'value' in order[f]:
                    o[f] = order[f]['value']

        # Shipping fields
        for f in SHIPPING_FIELDS:
            if f in order.keys():
                o[f] = order['ShippingAddress'][f]['value']

        clean_list += [o]
    return clean_list


def get_mws_orders(orders_api, marketplace, created_after, created_before):
    """
    Get MWS orders from Orders API in marketplace between created_after and created_before.

    Args:
        :order_api: class Orders(MWS)
        :marketplace: list of MWS marketplacess
        :created_after: min date for orders in the format %Y-%m-%d
        :created_before: max date for orders in the format %Y-%m-%d
    """
    
    # Initialize
    mws_orders = list()
    pagination = True
    p = 1
    try:
        orders = orders_api.list_orders(marketplaceids=marketplace, created_after=created_after, created_before=created_before)
    except: # To prevent against throttled requests
        print('Throttled requests - Waiting 1 min before trying again.')
        time.sleep(THROTTLED_WAITING_TIME+1)
        orders = orders_api.list_orders(marketplaceid=marketplace, created_after=created_after, created_before=created_before)
    
    # Iterate
    while pagination:
        print('API call on MWS #', str(p))
        order_list = orders.parsed['Orders']['Order']
        mws_orders += get_clean_order_list(order_list)
        
        if 'NextToken' in orders.parsed.keys():
            next_token = orders.parsed['NextToken']['value']
            try:
                orders = orders_api.list_orders_by_next_token(token=next_token)
            except: 
                print('Throttled requests - Waiting 1 min before trying again.')
                time.sleep(THROTTLED_WAITING_TIME+1)
                try:
                    orders = orders_api.list_orders_by_next_token(token=next_token)
                except:
                    print('Throttled requests - Waiting an aditionnal 2 min before trying again.')
                    time.sleep(2*THROTTLED_WAITING_TIME+1)
                    try:
                        orders = orders_api.list_orders_by_next_token(token=next_token)
                    except:
                        pagination = False
            p+=1
        else:
            pagination = False
    
    amazon = pd.DataFrame(mws_orders)[SELECTED_COLS]
    return amazon


def run(mws_credentials, start_date, end_date):
    """Connect to MWS API and retrieve orders between start_date and end_date."""
    # Connect to API
    orders_api = mws.Orders(
        access_key=mws_credentials['MWS_ACCESS_KEY'], 
        secret_key=mws_credentials['MWS_SECRET_KEY'], 
        account_id=mws_credentials['MWS_ACCOUNT_ID'],
        region='FR',
    )
    # Get MWS Orders
    orders = get_mws_orders(
        orders_api=orders_api,
        marketplace=mws_credentials['MWS_MARKETPLACE_IDS'],
        created_after=start_date,
        created_before=end_date
    )
    return orders


if __name__ == '__main__':
    # Parsing args
    parser = argparse.ArgumentParser()
    parser.add_argument('-start', action='store', dest='start', type=str, help='Start date of the order import in the following format: YYYY-mm-dd')
    parser.add_argument('-end', action='store', dest='end', type=str, help='End date of the order import in the following format: YYYY-mm-dd')
    args = parser.parse_args()

    # Retrieve data
    amazon = run(MWD_CREDENTIALS, args.start, args.end)

    # Store data
    amazon.to_excel('data/amazon_' + args.start + '_to_' + args.end + '.xlsx', index=False, encoding='utf-8')
    amazon.to_csv('data/amazon_' + args.start + '_to_' + args.end + '.csv', index=False, encoding='utf-8')
