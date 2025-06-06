#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import mmap
import struct
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from data_bridge import TradingDataBridge

class DataViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Data Viewer")
        self.root.geometry("1200x800")
        
        self.current_data = None
        self.shared_memory = TradingDataBridge()
        self.update_thread = None
        self.running = False
        
        self.setup_ui()
        self.setup_shared_memory()
        
    def setup_ui(self):
        # Create main frames
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        data_frame = ttk.Frame(self.root)
        data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control buttons
        ttk.Button(control_frame, text="Load CSV Data", command=self.load_csv).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Refresh Data", command=self.refresh_data).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export Selection", command=self.export_data).pack(side='left', padx=5)
        
        # Data directory path
        ttk.Label(control_frame, text="Data Dir:").pack(side='left', padx=5)
        self.data_dir_var = tk.StringVar(value="./market_data")
        dir_entry = ttk.Entry(control_frame, textvariable=self.data_dir_var, width=30)
        dir_entry.pack(side='left', padx=5)
        ttk.Button(control_frame, text="Browse", command=self.browse_directory).pack(side='left', padx=5)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(data_frame)
        notebook.pack(fill='both', expand=True)
        
        # CSV Data tab
        csv_frame = ttk.Frame(notebook)
        notebook.add(csv_frame, text="CSV Data")
        self.setup_csv_tab(csv_frame)
        
        # Real-time tab
        realtime_frame = ttk.Frame(notebook)
        notebook.add(realtime_frame, text="Real-time Data")
        self.setup_realtime_tab(realtime_frame)
        
        # Charts tab
        chart_frame = ttk.Frame(notebook)
        notebook.add(chart_frame, text="Charts")
        self.setup_chart_tab(chart_frame)
    
    def setup_csv_tab(self, parent):
        # File selector
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="Select Symbol:").pack(side='left')
        self.symbol_var = tk.StringVar()
        self.symbol_combo = ttk.Combobox(file_frame, textvariable=self.symbol_var, width=15)
        self.symbol_combo.pack(side='left', padx=5)
        self.symbol_combo.bind('<<ComboboxSelected>>', self.load_symbol_data)
        
        # Search and filter
        ttk.Label(file_frame, text="Search:").pack(side='left', padx=(20,5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(file_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', self.filter_data)
        
        # Data table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview with scrollbars
        self.tree = ttk.Treeview(table_frame)
        v_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        
        # Stats frame
        stats_frame = ttk.LabelFrame(parent, text="Statistics")
        stats_frame.pack(fill='x', padx=5, pady=5)
        self.stats_text = tk.Text(stats_frame, height=4, wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
    
    def setup_realtime_tab(self, parent):
        # Real-time data display
        info_frame = ttk.LabelFrame(parent, text="Shared Memory Data")
        info_frame.pack(fill='x', padx=5, pady=5)
        
        self.realtime_text = tk.Text(info_frame, height=8, wrap='word')
        self.realtime_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring)
        self.stop_button.pack(side='left', padx=5)
        self.stop_button.config(state='disabled')
    
    def setup_chart_tab(self, parent):
        # Chart controls
        chart_control = ttk.Frame(parent)
        chart_control.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(chart_control, text="Plot Price", command=self.plot_price).pack(side='left', padx=5)
        ttk.Button(chart_control, text="Plot Volume", command=self.plot_volume).pack(side='left', padx=5)
        ttk.Button(chart_control, text="Clear Chart", command=self.clear_chart).pack(side='left', padx=5)
        
        # Chart area
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
    
    def setup_shared_memory(self):
        if self.shared_memory.connect():
            self.realtime_text.insert('end', "✓ Connected to shared memory\n")
        else:
            self.realtime_text.insert('end', "✗ Failed to connect to shared memory\n")
    
    def refresh_data(self):
        data_dir = self.data_dir_var.get()
        if not os.path.exists(data_dir):
            messagebox.showerror("Error", f"Directory not found: {data_dir}")
            return
            
        symbols = []
        for subdir in ['stocks', 'forex', 'crypto']:
            subdir_path = os.path.join(data_dir, subdir)
            if os.path.exists(subdir_path):
                for file in os.listdir(subdir_path):
                    if file.endswith('.csv'):
                        symbols.append(file[:-4])  # Remove .csv extension
        
        self.symbol_combo['values'] = sorted(symbols)
        if symbols:
            self.symbol_combo.set(symbols[0])
            self.load_symbol_data()
    
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.data_dir_var.get())
        if directory:
            self.data_dir_var.set(directory)
            self.refresh_data()
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.load_csv_file(file_path)
    
    def load_symbol_data(self, event=None):
        from data_bridge import DataManager
        symbol = self.symbol_var.get()
        if not symbol:
            return
            
        data_manager = DataManager(self.data_dir_var.get())
        df = data_manager.load_symbol_data(symbol)
        
        if df is not None:
            self.current_data = df
            self.display_data(df)
            self.update_stats(df)
        else:
            messagebox.showerror("Error", f"No data file found for {symbol}")
    
    def load_csv_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            self.current_data = df
            self.display_data(df)
            self.update_stats(df)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
    
    def display_data(self, df):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if df.empty:
            return
        
        # Set up columns
        self.tree['columns'] = list(df.columns)
        self.tree['show'] = 'headings'
        
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Insert data
        for index, row in df.iterrows():
            values = [str(row[col]) for col in df.columns]
            self.tree.insert('', 'end', values=values)
    
    def update_stats(self, df):
        if df.empty:
            return
        
        stats = []
        stats.append(f"Total Records: {len(df)}")
        
        if 'price' in df.columns:
            stats.append(f"Price - Min: ${df['price'].min():.2f}, Max: ${df['price'].max():.2f}, Avg: ${df['price'].mean():.2f}")
        
        if 'volume' in df.columns:
            stats.append(f"Volume - Min: {df['volume'].min():,.0f}, Max: {df['volume'].max():,.0f}, Avg: {df['volume'].mean():,.0f}")
        
        if 'timestamp' in df.columns:
            start_time = pd.to_datetime(df['timestamp'].min(), unit='s')
            end_time = pd.to_datetime(df['timestamp'].max(), unit='s')
            stats.append(f"Time Range: {start_time} to {end_time}")
        
        self.stats_text.delete(1.0, 'end')
        self.stats_text.insert('end', '\n'.join(stats))
    
    def filter_data(self, event=None):
        if self.current_data is None:
            return
        
        search_term = self.search_var.get().lower()
        if not search_term:
            self.display_data(self.current_data)
            return
        
        # Filter data based on search term
        filtered_df = self.current_data[
            self.current_data.astype(str).apply(
                lambda x: x.str.lower().str.contains(search_term, na=False)
            ).any(axis=1)
        ]
        self.display_data(filtered_df)
    
    def export_data(self):
        if self.current_data is None:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.current_data.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Data exported to {file_path}")
    
    def start_monitoring(self):
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self.monitor_shared_memory, daemon=True)
            self.update_thread.start()
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
    
    def stop_monitoring(self):
        self.running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def monitor_shared_memory(self):
        while self.running:
            data = self.shared_memory.read_data()
            if data:
                timestamp = datetime.now().strftime("%H:%M:%S")
                info = f"[{timestamp}] Price: ${data['price']:.2f}, Volume: {data['volume']:,}, "
                info += f"Timestamp: {data['timestamp']}, Valid: {data['valid']}\n"
                
                self.root.after(0, lambda: self.realtime_text.insert('end', info))
                self.root.after(0, lambda: self.realtime_text.see('end'))
            
            time.sleep(1)
    
    def plot_price(self):
        if self.current_data is None or 'price' not in self.current_data.columns:
            messagebox.showwarning("Warning", "No price data available")
            return
        
        self.ax.clear()
        if 'timestamp' in self.current_data.columns:
            timestamps = pd.to_datetime(self.current_data['timestamp'], unit='s')
            self.ax.plot(timestamps, self.current_data['price'])
            self.ax.set_xlabel('Time')
        else:
            self.ax.plot(self.current_data['price'])
            self.ax.set_xlabel('Index')
        
        self.ax.set_ylabel('Price ($)')
        self.ax.set_title('Price Chart')
        self.ax.grid(True)
        self.canvas.draw()
    
    def plot_volume(self):
        if self.current_data is None or 'volume' not in self.current_data.columns:
            messagebox.showwarning("Warning", "No volume data available")
            return
        
        self.ax.clear()
        if 'timestamp' in self.current_data.columns:
            timestamps = pd.to_datetime(self.current_data['timestamp'], unit='s')
            self.ax.bar(timestamps, self.current_data['volume'])
            self.ax.set_xlabel('Time')
        else:
            self.ax.bar(range(len(self.current_data)), self.current_data['volume'])
            self.ax.set_xlabel('Index')
        
        self.ax.set_ylabel('Volume')
        self.ax.set_title('Volume Chart')
        self.ax.grid(True)
        self.canvas.draw()
    
    def clear_chart(self):
        self.ax.clear()
        self.canvas.draw()
    
    def on_closing(self):
        self.stop_monitoring()
        self.shared_memory.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DataViewer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()