import json
import os

from prettytable import PrettyTable
import yfinance as yf
from colorama import Fore, Style
import pandas as pd
import statsmodels.api as sm

class StockManager:
    def __init__(self):
        self.stock = {}

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.stock, file)

    def load_from_file(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as file:
                    self.stock = json.load(file)
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {filename}. Starting with an empty stock.")
        else:
            print(f"File not found: {filename}. Creating a new file.")
            self.save_to_file(filename)

    def add_stock(self, item, quantity, price):
            if item in self.stock:
                existing_quantity = self.stock[item]['quantity']
                existing_price = self.stock[item]['price']
                total_quantity = existing_quantity + quantity
                weighted_average_price = (existing_quantity * existing_price + quantity * price) / total_quantity

                self.stock[item]['quantity'] = total_quantity
                self.stock[item]['price'] = weighted_average_price
                print(f"{quantity} units of {item} added to stock at Rp{price} per unit. Total: {total_quantity} units. Weighted Average Price: Rp{weighted_average_price:.2f}")

            else:
                self.stock[item] = {'quantity': quantity, 'price': price}
                print(f"{quantity} units of {item} added to stock at Rp{price} per unit. Total: {quantity} units.")

    def remove_stock(self, item, quantity):
        if item in self.stock:
            if self.stock[item]['quantity'] >= quantity:
                self.stock[item]['quantity'] -= quantity
                print(f"{quantity} units of {item} removed from stock. Remaining: {self.stock[item]['quantity']} units.")
            else:
                print(f"Error: Insufficient stock for {item}.")
                return False
        else:
            print(f"Error: {item} not found in stock.")
            return False
        return True

    def update_stock(self, item, new_quantity, new_price):
        if item in self.stock:
            self.stock[item]['quantity'] = new_quantity
            self.stock[item]['price'] = new_price
            print(f"Stock information for {item} updated to {new_quantity} units at Rp{new_price} per unit.")
        else:
            print(f"Error: {item} not found in stock.")

    def delete_stock(self, item):
        if item in self.stock:
            del self.stock[item]
            print(f"{item} removed from stock.")
        else:
            print(f"Error: {item} not found in stock.")

    def display_stock(self):
        if not self.stock:
            print("No stock found.")
            return

        table = PrettyTable()
        table.field_names = ["Stock Code", "Quantity", "Price Bought (Rp)", "Market Price", "Market Value (Rp)", "Profit/Loss (Rp)", "Percentage Change (%)"]

        for item, info in self.stock.items():
            stock_data = yf.Ticker(f"{item}.JK")
            market_price = stock_data.history(period="1d")["Close"][0]
            market_value = market_price * info['quantity'] * 100
            profit_loss = market_value - (info['price'] * info['quantity'] * 100)
            percentage_change = ((market_price - info['price']) / info['price']) * 100 if info['price'] != 0 else 0

            color = Fore.GREEN if profit_loss >= 0 else Fore.RED

            table.add_row([item, info['quantity'], f"{info['price']:.2f}", f"{market_price:.2f}", f"{market_value:.2f}",
                        f"{color}{profit_loss:.2f}{Style.RESET_ALL}", f"{color}{percentage_change:.2f}%{Style.RESET_ALL}"])

        print("\nCurrent Stock:")
        print(table)
        print( f"Last updated: {stock_data.history(period='1d').index[-1].strftime('%Y-%m-%d')}")
    
    def overall_portfolio_performance(self):
        if not self.stock:
            print("No stock found.")
            return

        table = PrettyTable()
        table.field_names = ["Metric", "Value"]

        total_investment = 0
        total_market_value = 0

        for item, info in self.stock.items():
            stock_data = yf.Ticker(f"{item}.JK")
            market_price = stock_data.history(period="1d")["Close"][0]
            market_value = market_price * info['quantity'] * 100
            total_investment += info['price'] * info['quantity'] * 100
            total_market_value += market_value

        total_profit_loss = total_market_value - total_investment
        total_percentage_change = ((total_market_value - total_investment) / total_investment) * 100 if total_investment != 0 else 0

        color = Fore.GREEN if total_profit_loss >= 0 else Fore.RED

        table.add_row(["Total Investment (Rp)", f"{total_investment:.2f}{Style.RESET_ALL}"])
        table.add_row(["Total Market Value (Rp)", f"{color}{total_market_value:.2f}{Style.RESET_ALL}"])
        table.add_row(["Total Profit/Loss (Rp)", f"{color}{total_profit_loss:.2f}{Style.RESET_ALL}"])
        table.add_row(["Total Percentage Change (%)", f"{color}{total_percentage_change:.2f}%{Style.RESET_ALL}"])

        print("\nOverall Portfolio Performance:")
        print(table)
        print( f"Last updated: {stock_data.history(period='1d').index[-1].strftime('%Y-%m-%d')}")

    def calculate_volatility(self, item):
        lookback_period=252
        stock_data = yf.Ticker(f"{item}.JK")
        historical_prices = stock_data.history(period=f"{lookback_period}d")["Close"]
        daily_returns = historical_prices.pct_change().dropna()

        volatility = daily_returns.std() * (252 ** 0.5) 
        return volatility

    def calculate_beta(self, item):
        stock_data = yf.Ticker(f"{item}.JK")
        historical_prices = stock_data.history(period="1y")["Close"]
        daily_returns = historical_prices.pct_change().dropna()

        idx_data = yf.Ticker("^JKSE")
        idx_historical_prices = idx_data.history(period="1y")["Close"]
        idx_daily_returns = idx_historical_prices.pct_change().dropna()

        covariance = daily_returns.cov(idx_daily_returns)
        variance = idx_daily_returns.var()
        beta = covariance / variance
        return beta

    def calculate_alpha(self, item):
        stock_data = yf.Ticker(f"{item}.JK")
        historical_prices = stock_data.history(period="1y")["Close"]
        
        idx_data = yf.Ticker('^JKSE')
        idx_historical_prices = idx_data.history(period="1y")["Close"]
        
        data = pd.concat([historical_prices, idx_historical_prices], axis=1, keys=['Stock', 'Market'])
        data['StockReturns'] = data['Stock'].pct_change()
        data['MarketReturns'] = data['Market'].pct_change()
        data = data.dropna()
        
        df = pd.DataFrame({'Returns': data['StockReturns'], 'MarketReturns': data['MarketReturns']})
        df = sm.add_constant(df)
        
        model = sm.OLS(df['Returns'], df[['const', 'MarketReturns']])
        results = model.fit()

        alpha = round(results.params['const'], 2)
        return alpha

    def display_risk_metrics(self):
        if not self.stock:
            print("No stock found.")
            return

        table = PrettyTable()
        table.field_names = ["Stock", "Volatility (Annualized)", "Alpha (Relative to IHSG)", "Beta (Relative to IHSG)"]

        color_volatility = lambda x: Fore.GREEN if x <= 0.33 else Fore.YELLOW if x <= 0.66 else Fore.RED
        color_alpha = lambda x: Fore.GREEN if x > 0 else Fore.YELLOW if x == 0 else Fore.RED
        color_beta = lambda x: Fore.GREEN if x == 1 else Fore.YELLOW if x <= 1 else Fore.RED

        for item, info in self.stock.items():
            volatility = self.calculate_volatility(item)
            alpha = self.calculate_alpha(item)
            beta = self.calculate_beta(item)

            table.add_row([item, f"{color_volatility(volatility)}{volatility:.2f}{Style.RESET_ALL}", f"{color_alpha(alpha)}{alpha:.2f}{Style.RESET_ALL}", f"{color_beta(beta)}{beta:.2f}{Style.RESET_ALL}"])

        print("\nRisk Metrics:")
        print(table)

def main():
    stock_manager = StockManager()
    data_file = "stock_data.json"
    stock_manager.load_from_file(data_file)

    while True:
        os.system('cls' or 'clear')
        print("==============================================================================")
        print(" $$$$$$\                                $$$$$$\ $$$$$$$\  $$\   $$\  $$$$$$\  ")
        print("$$  __$$\                               \_$$  _|$$  __$$\ $$ |  $$ |$$  __$$\ ")
        print("$$ /  $$ | $$$$$$\   $$$$$$\  $$$$$$$\    $$ |  $$ |  $$ |\$$\ $$  |\__/  $$ |")
        print("$$ |  $$ |$$  __$$\ $$  __$$\ $$  __$$\   $$ |  $$ |  $$ | \$$$$  /  $$$$$$  |")
        print("$$ |  $$ |$$ /  $$ |$$$$$$$$ |$$ |  $$ |  $$ |  $$ |  $$ | $$  $$<  $$  ____/ ")
        print("$$ |  $$ |$$ |  $$ |$$   ____|$$ |  $$ |  $$ |  $$ |  $$ |$$  /\$$\ $$ |      ")
        print(" $$$$$$  |$$$$$$$  |\$$$$$$$\ $$ |  $$ |$$$$$$\ $$$$$$$  |$$ /  $$ |$$$$$$$$\ ")
        print(" \______/ $$  ____/  \_______|\__|  \__|\______|\_______/ \__|  \__|\________|")
        print("          $$ |                                                                ")
        print("          $$ |                                                                ")
        print("          \__|                                                                ")
        print("--------- Indonesia Stock Exchange Stock Portfolio Management System ---------")
        print("------------------- Made by kangwijen, 2023. Version 1.0.2 -------------------")
        print("==============================================================================")
        print("\n1. Portfolio\n2. Analysis\n3. Save and Quit")
        choice = input("Enter your choice (1/2/3): ")

        if choice == "1":
            quit = False

            while not quit:
                print("\n1. Add stock\n2. Remove stock\n3. Update stock\n4. Delete stock\n5. Display portfolio\n6. Return")
                choice = input("Enter your choice (1/2/3/4/5/6): ")

                if choice == "1":
                    try:
                        item = str(input("Enter stock code: ").upper().strip())
                        quantity = int(input("Enter quantity in lots to add: "))
                        price = float(input("Enter price per unit: "))
                        stock_manager.add_stock(item, quantity, price)
                    except ValueError:
                        print("Invalid input. Quantity and price must be numeric values.")

                elif choice == "2":
                    try:
                        item = str(input("Enter stock code: ").upper().strip())
                        quantity = int(input("Enter quantity to remove: "))
                        stock_manager.remove_stock(item, quantity)
                    except ValueError:
                        print("Invalid input. Quantity must be a numeric value.")

                elif choice == "3":
                    try:
                        item = str(input("Enter stock code: ").upper().strip())
                        new_quantity = int(input("Enter new quantity in lots: "))
                        new_price = float(input("Enter new price per unit: "))
                        stock_manager.update_stock(item, new_quantity, new_price)
                    except ValueError:
                        print("Invalid input. New quantity and price must be numeric values.")

                elif choice == "4":
                    item = str(input("Enter stock code: ").upper().strip())
                    stock_manager.delete_stock(item)

                elif choice == "5":
                    stock_manager.display_stock()

                elif choice == "6":
                    quit = True

                else:
                    print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

                stock_manager.save_to_file(data_file)

        elif choice == "2":
            quit = False

            while not quit:
                print("\n1. Portfolio Performance\n2. Portfolio Risk Metrics\n3. Return")
                choice = input("Enter your choice (1/2/3): ")

                if choice == "1":
                    stock_manager.overall_portfolio_performance()

                elif choice == "2":
                    stock_manager.display_risk_metrics()
                
                elif choice == "3":
                    quit = True
        
        elif choice == "3":
            stock_manager.save_to_file(data_file)
            break

if __name__ == "__main__":
    main()