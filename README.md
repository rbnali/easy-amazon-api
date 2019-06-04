# easy-amazon-api
Python script to retrieve orders information from Amazon MWS API to Pandas or Excel

# Requirements

Please install all the necesssary requirements with the following command:

```
pip install -r requirements.txt
```

You will also need to create a json file with your MWS API credentials called `amazon_credentials.json` in the same folder as `amazon.py`.

```
{
	"MWS_ACCOUNT_ID": "YOUR_MWS_ACCOUNT_ID",
	"MWS_ACCESS_KEY" : "YOUR_MWS_ACCESS_KEY",
	"MWS_SECRET_KEY": "YOUR_MWS_SECRET_KEY",
	"MWS_MARKETPLACE_ID": "YOUR_MWS_MARKETPLACE_ID"
}
```

If you don't have MWS API credentials, connect to Amazon Sellercentral and make a request here: https://sellercentral.amazon.fr/gp/account-manager/home.html/

You will find documentations on marketplace IDs here: https://docs.developer.amazonservices.com/en_US/dev_guide/DG_Endpoints.html

# Arguments

Arguments       | Help
-------------   | -------------
-start          | Start date of the order import in the following format: YYYY-mm-dd
-end            | End date of the order import in the following format: YYYY-mm-dd

# Example

```
python amazon.py -start 2019-05-01 -end 2019-05-31
```

# Output description

Excel & CSV file with the following columns:

Column                        | Description
-------------                 | -------------
AmazonOrderId                 | Amazon order identifier
MarketplaceId                 | Marketplace ID. The code can be modified if you want multiple marketplaces.
PurchaseDate                  | Purchase date
BuyerEmail                    | Encrypted buyer email (Amazon email)
BuyerName                     | Buyer first name and last name
ShipmentServiceLevelCategory  | Expedited = Prime orders
OrderStatus                   | Order Status
NumberOfItemsShipped          | Number of items shipped
OrderTotal_amount             | Total purchase amount of the order
OrderTotal_currency           | Currency
