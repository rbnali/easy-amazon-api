from mws import mws
import pandas as pd
import time
import json
import argparse

### AMAZON API FUNCTIONS ###

def get_clean_order_list(order_list):
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
        shipping_fields = ['AddressLine1', 'AddressLine2', 'City', 'CountryCode', 'Name', 'PostalCode']
        for f in shipping_fields:
            if f in order.keys():
                o[f] = order['ShippingAddress'][f]['value']

        clean_list += [o]
    return clean_list

def get_mws_orders(orders_api, marketplace, created_after, created_before):
    
    # INITIALIZE
    mws_orders = list()
    pagination = True
    p = 1
    try:
        orders = orders_api.list_orders(marketplaceids=[marketplace], created_after=created_after, created_before=created_before)
    except: # To prevent against throttled requests
        print('Throttled requests - Waiting 1 min before trying again.')
        time.sleep(61)
        orders = orders_api.list_orders(marketplaceids=[marketplace], created_after=created_after, created_before=created_before)
    
    # ITERATE
    while pagination:
        print('API call on MWS #', str(p))
        order_list = orders.parsed['Orders']['Order']
        mws_orders += get_clean_order_list(order_list)
        
        if 'NextToken' in orders.parsed.keys():
            next_token = orders.parsed['NextToken']['value']
            
            # To prevent against throttled requests
            try:
                orders = orders_api.list_orders_by_next_token(token=next_token)
            except: 
                print('Throttled requests - Waiting 1 min before trying again.')
                time.sleep(61)
                try:
                    orders = orders_api.list_orders_by_next_token(token=next_token)
                except:
                    print('Throttled requests - Waiting an aditionnal 2 min before trying again.')
                    time.sleep(121)
                    try:
                        orders = orders_api.list_orders_by_next_token(token=next_token)
                    except:
                        pagination = False
            p+=1
        else:
            pagination = False
    
    # TO PANDAS
    amazon = pd.DataFrame(mws_orders)
    sel_cols = [
        'AmazonOrderId','MarketplaceId','PurchaseDate','BuyerEmail', 
        'BuyerName', 'ShipmentServiceLevelCategory','OrderStatus', 
        'NumberOfItemsShipped', 'OrderTotal_amount' , 'OrderTotal_currency'
    ]
    return amazon[sel_cols]


### UPDATE ###

def run(mws_credentials, start_date, end_date):
    
    # PREPARE
    orders_api = mws.Orders(
        access_key=mws_credentials['MWS_ACCESS_KEY'], 
        secret_key=mws_credentials['MWS_SECRET_KEY'], 
        account_id=mws_credentials['MWS_ACCOUNT_ID'],
        region='FR',
    )
    
    # RETRIEVE
    orders = get_mws_orders(
        orders_api=orders_api,
        marketplace=mws_credentials['MWS_MARKETPLACE'],
        created_after=start_date,
        created_before=end_date
    )
    
    return orders

### RUN ###

if __name__ == '__main__':
    ### MWS CREDENTIALS ###
    amazon_path = 'amazon_credentials.json'
    with open(amazon_path) as f:
        mws_credentials = json.load(f)

    ### PARSING ARGS ###
    parser = argparse.ArgumentParser()
    parser.add_argument('-start', action='store', dest='start', type=str, help='Start date of the order import in the following format: YYYY-mm-dd')
    parser.add_argument('-end', action='store', dest='end', type=str, help='End date of the order import in the following format: YYYY-mm-dd')
    args = parser.parse_args()

    ### RUN ### 
    amazon = run(mws_credentials, args.start, args.end)
    amazon.to_excel('amazon_' + args.start + '_to_' + args.end + '.xlsx', index=False)