import logging
import math
import toml

from rich.console import Console
from rich.table import Table

from pycoingecko import CoinGeckoAPI

log = logging.getLogger(__name__)
console = Console()

# from dataclasses import dataclass

# @dataclass
# class Coin:
#     symbol: str
#     allocation: float

CURRENCIES = {"eur": "€", "usd": "$", "gbp": "£"}


class Portfolio:
    def connect(self, exchange):
        cg = CoinGeckoAPI()
        market_data = cg.get_coins_markets(self.model["currency"])
        available_assets = exchange.get_available_assets(self.model["currency"])
        for coin in market_data:
            if len(self.data) >= self.model["assets"]:
                break
            symbol = exchange.translate_symbol(coin["symbol"])
            if symbol in available_assets:
                self.data.append(
                    {
                        "symbol": symbol,
                        "name": coin["name"],
                        "market_cap": coin["market_cap"],
                    }
                )
            else:
                log.warning(
                    f"Coin {coin['name']} ({coin['symbol']}) not available for purchase with {self.model['currency']}"
                )
                continue
        self.allocate_by_sqrt_market_cap()

    def update(self, exchange):
        assets_list = [coin["symbol"] for coin in self.data]
        assets_data = exchange.get_assets_data(assets_list, self.model["currency"])
        owned_assets = exchange.get_owned_assets()
        for coin in self.data:
            for asset in assets_data:
                if asset["symbol"] == exchange.translate_symbol(coin["symbol"]):
                    coin["price"] = float(asset["price"])
                    coin["fee"] = float(asset["fee"])
                    coin["minimum_order"] = asset["minimum_order"]
            if coin["symbol"] in owned_assets.keys():
                coin["amount"] = float(owned_assets[coin["symbol"]])
            else:
                coin["amount"] = 0
        self.calculate_owned_allocation()

    def invest(self, exchange, deposit=0, rebalance=True, prioritize_targets=False):
        for coin in self.data:
            coin['drift'] = coin['allocation'] - coin['target']
        coins_above_target = [c for c in self.data if c['drift'] > 0]
        coins_below_target = [c for c in self.data if c['drift'] < 0]
            
        if rebalance:
            redistribution_funds = 0
            for coin in coins_above_target:
                coin_value = coin['price'] * coin['amount']
                coin['currency_order'] = (coin['drift'] * coin_value) / 100
                redistribution_funds += coin['currency_order']

            redistribution_total_allocation = sum(coin['target'] for coin in coins_below_target)
            for coin in coins_below_target:
                coin['currency_order'] = -(coin['target'] * redistribution_funds) / redistribution_total_allocation

        # if prioritize_targets:
        #     for coin in coins_below_target:
        #         rebalanced_amount = coin['value'] + coin['currency_order']
        #         rebalance_leftover = 
        
        for coin in self.data:
            coin['currency_order'] +=  -(coin['target'] * deposit) / 100
            coin['units_order'] =  coin['currency_order'] / coin['price']

    def allocate_by_sqrt_market_cap(self):
        total_sqrt_market_cap = sum([math.sqrt(coin["market_cap"]) for coin in self.data])
        for coin in self.data:
            coin["target"] = 100 * math.sqrt(coin["market_cap"]) / total_sqrt_market_cap

    def calculate_owned_allocation(self):
        total_value = sum([coin["price"] * coin["amount"] for coin in self.data])
        for coin in self.data:
            coin["allocation"] = (100 * coin["price"] * coin["amount"]) / total_value

    # def allocate_by_clamped_market_cap(self, max_value):
    #     total_market_cap = sum([coin["market_cap"] for coin in self.data])
    #     for coin in self.data:
    #         coin["market_cap_percent"] = 100 * coin["market_cap"] / total_market_cap
    #         coin["allocation"] = coin["market_cap_percent"]
    #     overflow = 0
    #     for i in range(0, len(self.data)):
    #         current_coin = self.data[i]
    #         if current_coin["allocation"] > max_value:
    #             overflow = current_coin["allocation"] - max_value
    #             self.data[i]["allocation"] = max_value
    #             redist_values = [
    #                 other_coin["allocation"]
    #                 for other_coin in self.data
    #                 if other_coin["allocation"] < max_value
    #             ]
    #             for j in range(0, len(self.data)):
    #                 other_coin = self.data[j]
    #                 if other_coin["allocation"] < max_value:
    #                     weighted_overflow = (
    #                         overflow * other_coin["allocation"] / sum(redist_values)
    #                     )
    #                     self.data[j]["allocation"] = (
    #                         other_coin["allocation"] + weighted_overflow
    #                     )

    def __init__(self, model):
        self.model = toml.load(model)
        self.data = []

    def format_currency(self, value):
        return f"{round(value, 2)} {CURRENCIES[self.model['currency']]}"

    def to_table(self):
        table = Table()
        table.add_column("Asset")
        table.add_column("Value")
        table.add_column("Allocation %")
        table.add_column("Target %")

        table.add_column("Drift %")
        table.add_column(f"Buy / Sell ({CURRENCIES[self.model['currency']]})")
        table.add_column(f"Buy / Sell (units)")
        # table.add_column("Min. Order")
        # table.add_column("Cost")
        # table.add_column("Units")
        # table.add_column("Fee")
        for coin in self.data:
            # day_change = round(coin["price_change_percentage_24h_in_currency"], 2)
            # day_color = "red" if day_change < 0 else "green"
            # month_change = round(coin["price_change_percentage_30d_in_currency"], 2)
            # month_color = "red" if month_change < 0 else "green"

            min_order_color = (
                "red"
                if float(abs(coin["units_order"])) < float(coin["minimum_order"])
                else "green"
            )
            min_order = (
                f"[{min_order_color}]{coin['minimum_order']}[/{min_order_color}]"
            )
            name = coin["name"] + f" [bold]({coin['symbol']})"
            amount = self.format_currency((coin['price'] * coin['amount']))
            allocation = f"{round(coin['allocation'], 2)}%"
            target = f"{round(coin['target'], 2)}%"
            drift = f"{round(coin['drift'], 2)}%"
            buy_sell = self.format_currency(coin.get('currency_order'))
            buy_sell_units = str(round(coin.get('units_order'), 4))
            table.add_row(
                name,
                amount,
                allocation,
                target,
                drift,
                buy_sell,
                # buy_sell_units,
                # min_order
                # str(coin["current_price"]),
                # f"[{day_color}]{day_change}[/{day_color}]%",
                # f"[{month_color}]{month_change}[/{month_color}]%",
                # str(round(coin["market_cap_percent"], 2)),
                # min_order,
                # f"{round(coin['price'], 2)}",
                # f"{round(coin['purchase_units'], 6)}",
                # f"{round((coin['price'] * coin['fee'])/100, 2) if float(coin['fee']) > 0 else '?'}",
            )
        return table
