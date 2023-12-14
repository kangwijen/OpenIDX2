import json
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from prettytable import PrettyTable
from colorama import Fore, Style
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX

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

    def calculate_sharpe_ratio(self, risk_free_rate=0):
        benchmark_data = yf.Ticker("^JKSE").history(period="1y")["Close"]

        individual_sharpe_ratios = {}

        for item, info in self.stock.items():
            stock_data = yf.Ticker(f"{item}.JK").history(period="1y")["Close"]
            stock_returns = (stock_data / stock_data.shift(1) - 1).dropna()
            avg_stock_return = stock_returns.mean()
            std_stock_return = stock_returns.std()
            sharpe_ratio = (avg_stock_return - risk_free_rate) / std_stock_return
            individual_sharpe_ratios[item] = sharpe_ratio

        return individual_sharpe_ratios

    def display_risk_metrics(self):
        if not self.stock:
            print("No stock found.")
            return

        table = PrettyTable()
        table.field_names = ["Stock", "Volatility", "Alpha", "Beta", "Sharpe Ratio"]
        table.min_width["Stock"] = 12
        table.min_width["Volatility"] = 12
        table.min_width["Alpha"] = 12
        table.min_width["Beta"] = 12
        table.min_width["Sharpe Ratio"] = 12

        color_volatility = lambda x: Fore.GREEN if x <= 0.33 else Fore.YELLOW if x <= 0.66 else Fore.RED
        color_alpha = lambda x: Fore.GREEN if x > 0 else Fore.YELLOW if x == 0 else Fore.RED
        color_beta = lambda x: Fore.GREEN if x == 1 else Fore.YELLOW if x <= 1 else Fore.RED
        color_sharpe = lambda x: Fore.GREEN if x >= 1 else Fore.YELLOW if x >= 0 else Fore.RED

        for item, info in self.stock.items():
            volatility = self.calculate_volatility(item)
            alpha = self.calculate_alpha(item)
            beta = self.calculate_beta(item)
            sharpe = self.calculate_sharpe_ratio()[item] 

            table.add_row([item, f"{color_volatility(volatility)}{volatility:.2f}{Style.RESET_ALL}", f"{color_alpha(alpha)}{alpha:.2f}{Style.RESET_ALL}", \
                f"{color_beta(beta)}{beta:.2f}{Style.RESET_ALL}", f"{color_sharpe(sharpe)}{sharpe:.2f}{Style.RESET_ALL}"])

        print("\nRisk Metrics:")
        print(table)
        print("All annualized, relative to IHSG.")

class QuantitativeAnalysis:
    def __init__(self, symbol):
        self.symbol = symbol
        self.stock_data = yf.download(f"{symbol}.JK", progress=False)

    def sarimax_forecast(self, order=(1, 1, 1), exog_order=(1, 0, 1), days=7):
        ts = self.stock_data['Close']
        exog = self.stock_data['Volume']

        model = SARIMAX(ts, order=order, exog=exog, exog_order=exog_order)
        model_fit = model.fit()
        predictions = model_fit.predict(start=len(ts), end=len(ts) + days - 1, exog=exog[-days:])

        plt.plot(ts, label='Actual')
        plt.xlim(ts.index[0], ts.index[-1] + pd.DateOffset(days=len(predictions)))
        prediction_dates = pd.date_range(start=ts.index[-1] + pd.DateOffset(days=1), periods=len(predictions))
        plt.plot(prediction_dates, predictions, label='Predicted')
        plt.xlabel('Date')
        plt.ylabel('Stock Price')
        plt.title(f'{self.symbol} Stock Price - Actual vs Predicted (SARIMAX)')
        plt.legend()
        plt.show()

def main():
    stock_manager = StockManager()
    data_file = "stock_data.json"
    stock_manager.load_from_file(data_file)

    while True:
        os.system('cls' or 'clear')
        print(f"==============================================================================")
        print(f" $$$$$$\                                $$$$$$\ $$$$$$$\  $$\   $$\  $$$$$$\  ")
        print(f"$$  __$$\                               \_$$  _|$$  __$$\ $$ |  $$ |$$  __$$\ ")
        print(f"$$ /  $$ | $$$$$$\   $$$$$$\  $$$$$$$\    $$ |  $$ |  $$ |\$$\ $$  |\__/  $$ |")
        print(f"$$ |  $$ |$$  __$$\ $$  __$$\ $$  __$$\   $$ |  $$ |  $$ | \$$$$  /  $$$$$$  |")
        print(f"$$ |  $$ |$$ /  $$ |$$$$$$$$ |$$ |  $$ |  $$ |  $$ |  $$ | $$  $$<  $$  ____/ ")
        print(f"$$ |  $$ |$$ |  $$ |$$   ____|$$ |  $$ |  $$ |  $$ |  $$ |$$  /\$$\ $$ |      ")
        print(f" $$$$$$  |$$$$$$$  |\$$$$$$$\ $$ |  $$ |$$$$$$\ $$$$$$$  |$$ /  $$ |$$$$$$$$\ ")
        print(f" \______/ $$  ____/  \_______|\__|  \__|\______|\_______/ \__|  \__|\________|")
        print(f"          $$ |                                                                ")
        print(f"          $$ |                                                                ")
        print(f"          \__|                                                                ")
        print(f"--------- Indonesia Stock Exchange Stock Portfolio Management System ---------")
        print(f"--------------------- and Quantitative Analysis Platform ---------------------")
        print(f"------------------- Made by kangwijen, 2023. Version 1.1.0 -------------------")
        print(f"==============================================================================")
        print(f"{Fore.RED}Disclaimer: The developer is not responsible for any financial decisions made\n              based on the information provided by the program.{Style.RESET_ALL}")
        print("\n1. Portfolio Management\n2. Portfolio Analysis\n3. Stock Analysis\n4. Save and Quit")
        choice = input("Enter your choice: ")

        if choice == "1":
            quit = False

            while not quit:
                print("\n1. Add stock\n2. Remove stock\n3. Update stock\n4. Delete stock\n5. Display portfolio\n6. Return")
                choice = input("Enter your choice: ")

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
                    print("Invalid choice.")

                stock_manager.save_to_file(data_file)

        elif choice == "2":
            quit = False

            while not quit:
                print("\n1. Portfolio Performance\n2. Portfolio Risk Metrics\n3. Return")
                choice = input("Enter your choice: ")

                if choice == "1":
                    stock_manager.overall_portfolio_performance()

                elif choice == "2":
                    stock_manager.display_risk_metrics()
                
                elif choice == "3":
                    quit = True

                else:
                    print("Invalid choice.")

        elif choice == "3":
            quit = False

            while not quit:
                print("\n1. SARIMAX Forecast\n3. Return")
                choice = input("Enter your choice: ")

                if choice == "1":
                    item = str(input("Enter stock code: ").upper().strip())
                    day = int(input("Enter number of days to forecast: "))
                    stock_forecast = QuantitativeAnalysis(symbol=item) 
                    stock_forecast.sarimax_forecast(days=day)

                elif choice == "2":
                    print("Coming Soon!")

                elif choice == "3":
                    quit = True

                else:
                    print("Invalid choice.")
        
        elif choice == "4":
            stock_manager.save_to_file(data_file)
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()