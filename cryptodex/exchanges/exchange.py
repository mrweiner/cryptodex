from abc import ABC, abstractmethod


class Exchange(ABC):
    @abstractmethod
    def get_usd_balance(self):
        """
        Fetch the available USD balance from the exchange account.
        This should return the balance in USD or 0 if the balance is unavailable.
        """
        pass

    @abstractmethod
    def get_symbol(self, symbol):
        """
        given an asset symbol from coingecko, return the asset symbol in the exchange
        this method is used to normalize assets naming across exchanges as some
        of them use slightly different rules for asset symbols names,
        for example bitcoin is "btc" on coingecko but "xxbt" on kraken
        """
        pass

    @abstractmethod
    def get_available_assets(self, currency):
        """
        given a fiat currency, returns a list of asset symbols which are
        tradeable using that currency
        """
        pass

    @abstractmethod
    def get_owned_assets(self):
        """
        returns the assets owned in the exchange in the form of a dictionary of
        mapping their symbols to the amount of units owned
        """
        pass

    @abstractmethod
    def get_assets_data(self, assets, currency):
        """
        given a list of assets symbols and a fiat currency, returns a list of dictionaries
        contains the data for each asset. Each must contain the following fields:

        [symbol]: the symbol of the asset
        [minimum_order]: the minimum amount of units that can be traded for the assets
        [price]: the price of a unit of the asset
        [fee]: the % fee for a market order trade

        additionally, you can return a generic dictionary in a [exchange_data] field which
        will be passed to the order objects created when sending a buy / sell command
        """
        pass

    @abstractmethod
    def process_order(self, order, mock=True):
        """
        given a order object, send the order to the exchange for processing.
        Order objects are created by the buy / sell methods and contain the fields:

        symbol: the symbol of the asset being traded
        currency: the fiat currency used for trading
        units: the units of the asset to buy / sell
        cost: the cost / revenue of the order in fiat currency units
            (negative units means purchase order, positive means sell order)
        buy_or_sell: a string which is "buy" or "sell" based on the order type
        minimum_order: the minimum amount of units that can be traded for the assets
        exchange_data: the [exchange_data] data field returned from get_assets_data()

        if the 'mock' flag is False, only run orders validations / simulations
        """
        pass
