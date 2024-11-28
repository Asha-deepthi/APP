import tkinter as tk
from tkinter import ttk
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import numpy as np
import matplotlib.dates as mdates


# Function to fetch available currencies from the API
def fetch_currencies():
    url = 'https://api.frankfurter.app/currencies'
    response = requests.get(url)
    currencies = response.json()
    return list(currencies.keys())


# Function to fetch current exchange rate
def fetch_exchange_rate(base_currency, target_currency):
    url = f'https://api.frankfurter.app/latest?from={base_currency}&to={target_currency}'
    response = requests.get(url)
    
    try:
        data = response.json()
        return float(data['rates'][target_currency])
    except Exception as e:
        print("Error:") 
        return None


# Function to fetch historical exchange rates for various durations
def fetch_historical_rates(base_currency, target_currency, amount, duration):
    end_date = datetime.now()
    
    if duration == "10 days":
        start_date = end_date - timedelta(days=10)
        frequency = '1D'  # Every day for 10 days
    elif duration == "1 month":
        start_date = end_date - timedelta(days=30)
        frequency = '1W'  # Every week for 1 month
    elif duration == "1 year":
        start_date = end_date - timedelta(days=365)
        frequency = '1M'  # Every month for 1 year
    elif duration == "10 years":
        start_date = end_date - timedelta(days=365 * 10)
        frequency = '1Y'  # Every year for 10 years

    url = f'https://api.frankfurter.app/{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}?from={base_currency}&to={target_currency}'
    response = requests.get(url)
    
    dates, rates = [], []
    try:
        historical_data = response.json().get('rates', {})
        for date, rate_dict in sorted(historical_data.items()):
            if target_currency in rate_dict:
                dates.append(date)
                rates.append(rate_dict[target_currency] * amount)
    except Exception as e:
        print("Error fetching historical rates:", e)
    
    return dates, rates


# Function to handle currency conversion
def convert_currency():
    global amount
    amount = float(amount_entry.get())
    from_currency = from_currency_combobox.get()
    selected_targets = [combo.get() for combo in target_currency_comboboxes if combo.get()]

    for idx, target_currency in enumerate(selected_targets):
        rate = fetch_exchange_rate(from_currency, target_currency)
        if rate:
            result = f"{amount} {from_currency} = {amount * rate:.2f} {target_currency}"
            result_label = tk.Label(result_frame, text=result, fg="teal", font=("Times New Roman", 18))
            result_label.grid(row=idx, column=0, sticky="w", padx=10, pady=5)
        else:
            error_label = tk.Label(result_frame, text=f"Conversion unavailable for {target_currency}", fg="red", font=("Times New Roman", 18))
            error_label.grid(row=idx, column=0, sticky="w", padx=10, pady=5)


# Function to plot historical exchange rates with multiple graph options
def plot_historical_rates():
    from_currency = from_currency_combobox.get()
    target_currencies = [target_currency_comboboxes[i].get() for i in range(5) if target_currency_comboboxes[i].get()]
    graph_type = graph_type_combobox.get()
    duration = duration_combobox.get()

    if not target_currencies:
        result_label.config(text="Please select at least one target currency.")
        return

    amount = float(amount_entry.get())

    fig, ax = plt.subplots(figsize=(9, 6))

    rates_data = []
    dates = None
    for target_currency in target_currencies:
        target_dates, target_rates = fetch_historical_rates(from_currency, target_currency, amount, duration)
        if target_dates and target_rates:
            if not dates:
                dates = [datetime.strptime(date, "%Y-%m-%d") for date in target_dates]  # Parse dates correctly
            rates_data.append(target_rates)
    
    currency_colors = {
        'EUR': 'blue',
        'USD': 'green',
        'CAD': 'red',
        'GBP': 'orange',
        'AUD': 'purple',
    }
    if graph_type == "Area Graph":
        for i, rates in enumerate(rates_data):
            ax.fill_between(dates, rates, alpha=0.3, label=f'{from_currency} to {target_currencies[i]}')
    elif graph_type == "Line Graph":
        for i, rates in enumerate(rates_data):
            ax.plot(dates, rates, marker='o', label=f'{from_currency} to {target_currencies[i]}')
    elif graph_type == "Bar Graph":
        bar_width = 0.15
        for i, rates in enumerate(rates_data):
            ax.bar([date for date in dates], rates, width=bar_width, label=f'{from_currency} to {target_currencies[i]}', alpha=0.6, align='center')
    elif graph_type == "Stacked Area Graph":
        ax.stackplot(dates, rates_data, labels=target_currencies, alpha=0.5)
    elif graph_type == "Scatter Plot":
        for i, rates in enumerate(rates_data):
            color = currency_colors.get(target_currencies[i], 'black')  # Default to 'black' if currency is not in the dict
            ax.scatter(dates, rates, label=f'{from_currency} to {target_currencies[i]}', color=color)
    elif graph_type == "Heatmap":
        matrix = np.array(rates_data)
        sns.heatmap(matrix, xticklabels=dates, yticklabels=target_currencies, cmap="YlGnBu")

    ax.set_title(f'Historical Exchange Rates for {from_currency}', fontsize=18)
    ax.set_xlabel('Date', fontsize=16)
    ax.set_ylabel(f'Amount in {from_currency} (x{amount})', fontsize=16)

    if duration == "1 year":
         ax.xaxis.set_major_locator(mdates.MonthLocator())
         ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    elif duration == "10 years":
        start_year = int(dates[0].year)
        ax.set_xticks([datetime(start_year + i, 1, 1) for i in range(10)])
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  # Show years as 2014, 2015, etc.

    ax.tick_params(axis='x', rotation=45)
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=right_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=2, column=0, padx=20, pady=10)


# Setting up the main application window
root = tk.Tk()
root.geometry("1600x1100")
root.title("Currency Converter")

root.configure(bg="#F0F8FF")

header = tk.Label(root, text="  Multi-Currency Converter  ", font=("Times New Roman", 36, "bold"), bg="#008080", fg="white")
header.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
header.config(anchor="center")

currencies = fetch_currencies()

style = {"font": ("Times New Roman", 18), "bg": "#F0F8FF", "fg": "#008080"}

left_frame = tk.Frame(root, bg="#F0F8FF")
left_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

amount_label = tk.Label(left_frame, text="Amount:", **style)
amount_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
amount_entry = tk.Entry(left_frame, width=20, font=("Times New Roman", 18))
amount_entry.grid(row=1, column=1, padx=10, pady=5)

from_currency_label = tk.Label(left_frame, text="From Currency:", **style)
from_currency_label.grid(row=2, column=0, padx=10, pady=5)
from_currency_combobox = ttk.Combobox(left_frame, values=currencies, width=18, font=("Times New Roman", 18), state="normal")
from_currency_combobox.grid(row=2, column=1, padx=10, pady=5)
from_currency_combobox.set('INR')

target_currency_labels = []
target_currency_comboboxes = []
for i in range(5):
    target_currency_label1 = tk.Label(left_frame, text=f"To Currency {i + 1}:", **style)
    target_currency_label1.grid(row=6 + i, column=0, padx=10, pady=5)
    target_currency_combobox1 = ttk.Combobox(left_frame, values=currencies, width=18, font=("Times New Roman", 18), state="normal")
    target_currency_combobox1.grid(row=6 + i, column=1, padx=10, pady=5)

    if i == 0:
        target_currency_combobox1.set('EUR')
    elif i == 1:
        target_currency_combobox1.set('USD')
    elif i == 2:
        target_currency_combobox1.set('CAD')
    elif i == 3:
        target_currency_combobox1.set('GBP')
    elif i == 4:
        target_currency_combobox1.set('AUD')

    target_currency_labels.append(target_currency_label1)
    target_currency_comboboxes.append(target_currency_combobox1)

graph_type_label = tk.Label(left_frame, text="Select Graph Type:", **style)
graph_type_label.grid(row=11, column=0, padx=10, pady=5)
graph_type_combobox = ttk.Combobox(left_frame, values=["Area Graph", "Line Graph", "Bar Graph", "Stacked Area Graph", "Scatter Plot", "Heatmap"], width=18, font=("Times New Roman", 18), state="normal")
graph_type_combobox.grid(row=11, column=1, padx=10, pady=5)
graph_type_combobox.set('Line Graph')

duration_label = tk.Label(left_frame, text="Select Duration:", **style)
duration_label.grid(row=12, column=0, padx=10, pady=5)
duration_combobox = ttk.Combobox(left_frame, values=["10 days", "1 month", "1 year", "10 years"], width=18, font=("Times New Roman", 18), state="normal")
duration_combobox.grid(row=12, column=1, padx=10, pady=5)
duration_combobox.set('1 month')

result_frame = tk.Frame(left_frame, bg="#F0F8FF")
result_frame.grid(row=13, column=0, columnspan=4, padx=10, pady=10, sticky="w")

convert_button = tk.Button(left_frame, text="Convert", command=convert_currency, bg="#008080", fg="white", font=("Times New Roman", 18, "bold"))
convert_button.grid(row=14, column=0, columnspan=4, pady=10)

right_frame = tk.Frame(root, bg="#F0F8FF")
right_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

plot_button = tk.Button(right_frame, text="Plot Historical Rates", command=plot_historical_rates, bg="#008080", fg="white", font=("Times New Roman", 18, "bold"))
plot_button.grid(row=1, column=0, pady=10)

result_label = tk.Label(right_frame, text="", **style)
result_label.grid(row=2, column=0, pady=10)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(1, weight=1)

root.mainloop()