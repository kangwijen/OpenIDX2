import json
from prettytable import PrettyTable
import yfinance as yf
from colorama import Fore, Style

class StockManager:
    def __init__(self):
        self.stock = {}

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.stock, file)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.stock = json.load(file)
        except FileNotFoundError:
            print("File not found. Starting with an empty stock.")

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
        table = PrettyTable()
        table.field_names = ["Stock Code", "Quantity", "Price Bought (Rp)", "Market Price", "Market Value (Rp)", "Profit/Loss (Rp)", "Percentage Change"]

        for item, info in self.stock.items():
            stock_data = yf.Ticker(f"{item}.JK")
            market_price = stock_data.history(period="1d")["Close"][0]
            market_value = market_price * info['quantity'] * 100
            profit_loss = market_value - (info['price'] * info['quantity'] * 100)
            percentage_change = ((market_price - info['price']) / info['price']) * 100 if info['price'] != 0 else 0

            color = Fore.GREEN if profit_loss >= 0 else Fore.RED

            table.add_row([item, info['quantity'], f"{info['price']:.2f}", f"{market_price:.2f}", f"{market_value:.2f}",
                           f"{color}{profit_loss:.2f}{Style.RESET_ALL}", f"{percentage_change:.2f}%"])

        print("\nCurrent Stock:")
        print(table)
        print(f"Last updated: {stock_data.history(period='1d').index[-1]}")  

def main():
    stock_manager = StockManager()
    data_file = "stock_data.json"  # Adjust the filename as needed

    # Load existing stock data from file
    stock_manager.load_from_file(data_file)

    while True:
        print("\n1. Add stock\n2. Remove stock\n3. Update stock\n4. Delete stock\n5. Display portofolio\n6. Save and Quit")
        choice = input("Enter your choice (1/2/3/4/5/6): ")

        if choice == "1":
            item = str(input("Enter stock code: ").upper())
            quantity = int(input("Enter quantity in lots to add: "))
            price = float(input("Enter price per unit: "))
            stock_manager.add_stock(item, quantity, price)

        elif choice == "2":
            item = str(input("Enter stock code: ").upper())
            quantity = int(input("Enter quantity to remove: "))
            stock_manager.remove_stock(item, quantity)

        elif choice == "3":
            item = str(input("Enter stock code: ").upper())
            new_quantity = int(input("Enter new quantity in lots: "))
            new_price = float(input("Enter new price per unit: "))
            stock_manager.update_stock(item, new_quantity, new_price)

        elif choice == "4":
            item = str(input("Enter stock code: ").upper())
            stock_manager.delete_stock(item)

        elif choice == "5":
            stock_manager.display_stock()

        elif choice == "6":
            stock_manager.save_to_file(data_file)
            print("Stock data saved. Exiting program.")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")


if __name__ == "__main__":
    main()