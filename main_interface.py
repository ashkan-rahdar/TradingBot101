import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import json
import time
import sys

class TradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TradingBot101 Interface")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # Store user credentials and settings
        self.username = tk.StringVar(None, "admin", "username")
        self.password = tk.StringVar(None, "password", "password")
        self.authenticated = False
        self.bot_process = None
        self.bot_running = False
        
        # Load config from JSON file
        self.config_file_path = "d:/Trade/Bot/TradingBot101/config.json"
        self.config = self.load_config()
        
        # Create variables for config settings
        self.create_config_variables()
        
        # Initialize GUI components
        self.create_header()
        self.create_content_frame()
        
        # Start with welcome screen
        self.show_welcome()
    
    def create_header(self):
        """Creates the header with application title and description"""
        self.header_frame = tk.Frame(self.root, bg="#2c3e50")
        self.header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            self.header_frame, 
            text="TradingBot101", 
            font=("Arial", 18, "bold"), 
            bg="#2c3e50", 
            fg="white"
        )
        title_label.pack(pady=10)
        
        desc_label = tk.Label(
            self.header_frame, 
            text="An automated trading system for financial markets analysis and execution", 
            font=("Arial", 10), 
            bg="#2c3e50", 
            fg="white"
        )
        desc_label.pack(pady=(0, 10))
    
    def create_content_frame(self):
        """Creates the main content frame that will hold different screens"""
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Back button (initially hidden)
        self.back_btn_frame = tk.Frame(self.content_frame)
        self.back_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.back_button = tk.Button(
            self.back_btn_frame,
            text="← Back",
            command=self.go_back,
            font=("Arial", 10),
            width=10
        )
        # Only show back button when needed
        
    def create_config_variables(self):
        """Create tkinter variables for config settings"""
        # Account info variables
        self.login = tk.StringVar(value=self.config.get("account_info", {}).get("login", ""))
        self.account_password = tk.StringVar(value=self.config.get("account_info", {}).get("password", ""))
        self.server = tk.StringVar(value=self.config.get("account_info", {}).get("server", ""))
        self.commission = tk.DoubleVar(value=self.config.get("account_info", {}).get("commision", 0))
        self.spread = tk.DoubleVar(value=self.config.get("account_info", {}).get("spread", 0))
        
        # Trading config variables
        trading_cfg = self.config.get("trading_configs", {})
        # For multiselect timeframes
        self.available_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        self.selected_timeframes = trading_cfg.get("timeframes", ["M1", "M5", "M15"])
        self.asset = tk.StringVar(value=trading_cfg.get("asset", "EURUSD"))
        
        # Risk management variables
        risk_mgmt = trading_cfg.get("risk_management", {})
        self.risk_r = tk.DoubleVar(value=risk_mgmt.get("R", 0.1))
        self.max_weight = tk.DoubleVar(value=risk_mgmt.get("max_wieght", 4))
        
        # Runtime variables
        runtime = self.config.get("runtime", {})
        emergency_mode = runtime.get("emergency_mode", {})
        self.emergency_status = tk.BooleanVar(value=emergency_mode.get("status", True))
        self.emergency_password = tk.StringVar(value=emergency_mode.get("password", ""))
        self.another_function = tk.StringVar(value=runtime.get("Another_function_syntax", ""))
        
        # Navigation and workflow state
        self.current_screen = "welcome"
        self.screen_history = []
    
    def load_config(self):
        """Load config from file or return default if file doesn't exist"""
        try:
            with open(self.config_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return a default config structure if file doesn't exist
            return {
                "account_info": {
                    "login": "",
                    "password": "",
                    "server": "",
                    "commision": 4,
                    "spread": 0
                },
                "trading_configs": {
                    "timeframes": ["M1", "M15", "M5"],
                    "asset": "EURUSD",
                    "risk_management": {
                        "R": 0.1,
                        "max_wieght": 4
                    }
                },
                "runtime": {
                    "emergency_mode": {
                        "status": True,
                        "password": ""
                    },
                    "Another_function_syntax": ""
                }
            }
    
    def save_config(self):
        """Save the current config to the JSON file"""
        updated_config = {
            "account_info": {
                "login": self.login.get(),
                "password": self.account_password.get(),
                "server": self.server.get(),
                "commision": self.commission.get(),
                "spread": self.spread.get()
            },
            "trading_configs": {
                "timeframes": self.selected_timeframes,
                "asset": self.asset.get(),
                "risk_management": {
                    "R": self.risk_r.get(),
                    "max_wieght": self.max_weight.get()
                }
            },
            "runtime": {
                "emergency_mode": {
                    "status": self.emergency_status.get(),
                    "password": self.emergency_password.get()
                },
                "Another_function_syntax": self.another_function.get()
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
        
        # Write the config file
        with open(self.config_file_path, "w") as f:
            json.dump(updated_config, f, indent=4)
        
        # Update the config object
        self.config = updated_config
        messagebox.showinfo("Success", "Configuration saved successfully")
    
    def clear_content(self):
        """Clear the content frame to prepare for a new screen"""
        # Save current screen to history before clearing
        if self.current_screen:
            self.screen_history.append(self.current_screen)
        
        # Destroy all widgets in the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.back_btn_frame:  # Preserve back button frame
                widget.destroy()
    
    def go_back(self):
        """Navigate to the previous screen"""
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            
            # Don't add the current screen to history when going back
            temp = self.current_screen
            self.current_screen = ""
            
            # Show the previous screen
            if previous_screen == "welcome":
                self.show_welcome()
            elif previous_screen == "login":
                self.show_login()
            elif previous_screen == "config":
                self.show_config()
            
            # If we're back at the first screen, hide the back button
            if not self.screen_history:
                self.back_button.pack_forget()
    
    def show_welcome(self):
        """Display the welcome screen"""
        self.clear_content()
        self.current_screen = "welcome"
        
        # Hide back button on welcome screen
        self.back_button.pack_forget()
        
        welcome_frame = tk.Frame(self.content_frame, padx=40, pady=40)
        welcome_frame.pack(expand=True)
        
        # Welcome header
        welcome_label = tk.Label(
            welcome_frame,
            text="Welcome to TradingBot101",
            font=("Arial", 22, "bold")
        )
        welcome_label.pack(pady=(0, 30))
        
        # Welcome message
        message = """
        TradingBot101 is your advanced trading companion for financial markets.
        
        This application provides a user-friendly interface to:
        • Configure your trading parameters
        • Execute automated trading strategies
        • Monitor real-time trading activities
        • Analyze trading performance
        
        Ready to start trading? Click the button below to begin.
        """
        
        message_label = tk.Label(
            welcome_frame,
            text=message,
            font=("Arial", 12),
            justify="center",
            wraplength=600
        )
        message_label.pack(pady=(0, 40))
        
        # Start button
        start_button = tk.Button(
            welcome_frame,
            text="Let's Start",
            command=self.show_login,
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            width=15,
            height=1
        )
        start_button.pack()
        
        # Version info
        version_label = tk.Label(
            welcome_frame,
            text="Version 1.0.1",
            font=("Arial", 9)
        )
        version_label.pack(side=tk.BOTTOM, pady=20)
    
    def show_login(self):
        """Display the login screen"""
        self.clear_content()
        self.current_screen = "login"
        
        # Show back button
        self.back_button.pack(side=tk.LEFT, anchor=tk.NW)
        
        login_frame = tk.Frame(self.content_frame, padx=40, pady=40)
        login_frame.pack(expand=True)
        
        # Login header
        tk.Label(
            login_frame,
            text="User Authentication",
            font=("Arial", 18, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        tk.Label(
            login_frame,
            text="Username:",
            font=("Arial", 12)
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        username_entry = tk.Entry(
            login_frame,
            textvariable=self.username,
            font=("Arial", 12),
            width=25
        )
        username_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Password
        tk.Label(
            login_frame,
            text="Password:",
            font=("Arial", 12)
        ).grid(row=2, column=0, sticky="w", pady=10)
        
        password_entry = tk.Entry(
            login_frame,
            textvariable=self.password,
            font=("Arial", 12),
            width=25,
            show="*"
        )
        password_entry.grid(row=2, column=1, pady=10, padx=10)
        
        # Login button
        login_button = tk.Button(
            login_frame,
            text="Login",
            command=self.authenticate_user,
            font=("Arial", 12),
            bg="#2980b9",
            fg="white",
            width=15,
            height=1
        )
        login_button.grid(row=3, column=0, columnspan=2, pady=30)
    
    def authenticate_user(self):
        """Authenticate user credentials"""
        # In a real application, you would validate against a secure database
        # This is a simplified example
        valid_username = "admin"
        valid_password = "password"
        
        if self.username.get() == valid_username and self.password.get() == valid_password:
            self.authenticated = True
            messagebox.showinfo("Success", "Login successful")
            self.show_config()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def show_config(self):
        """Display the configuration screen"""
        self.clear_content()
        self.current_screen = "config"
        
        # Show back button
        self.back_button.pack(side=tk.LEFT, anchor=tk.NW)
        
        # Create a frame with a notebook for different config sections
        config_frame = tk.Frame(self.content_frame, padx=20, pady=20)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            config_frame,
            text="Trading Bot Configuration",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Create notebook for config sections
        config_notebook = ttk.Notebook(config_frame)
        config_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Account Info tab
        account_tab = ttk.Frame(config_notebook)
        config_notebook.add(account_tab, text="Account Information")
        self.setup_account_tab(account_tab)
        
        # Trading Settings tab
        trading_tab = ttk.Frame(config_notebook)
        config_notebook.add(trading_tab, text="Trading Settings")
        self.setup_trading_tab(trading_tab)
        
        # Runtime Settings tab
        runtime_tab = ttk.Frame(config_notebook)
        config_notebook.add(runtime_tab, text="Runtime Settings")
        self.setup_runtime_tab(runtime_tab)
        
        # Save and Continue button
        button_frame = tk.Frame(config_frame)
        button_frame.pack(pady=15)
        
        save_button = tk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            font=("Arial", 11),
            bg="#27ae60",
            fg="white",
            width=18,
            height=1
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        continue_button = tk.Button(
            button_frame,
            text="Continue to Trading Bot",
            command=self.show_bot,
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            width=18,
            height=1
        )
        continue_button.pack(side=tk.LEFT, padx=5)
    
    def setup_account_tab(self, parent):
        """Setup the account info configuration tab"""
        frame = tk.Frame(parent, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Login ID
        tk.Label(
            frame,
            text="Login ID:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.login,
            font=("Arial", 11),
            width=30
        ).grid(row=0, column=1, pady=10, padx=5, sticky="w")
        
        # Password
        tk.Label(
            frame,
            text="Password:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.account_password,
            font=("Arial", 11),
            width=30,
            show="*"
        ).grid(row=1, column=1, pady=10, padx=5, sticky="w")
        
        # Server
        tk.Label(
            frame,
            text="Server:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=2, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.server,
            font=("Arial", 11),
            width=30
        ).grid(row=2, column=1, pady=10, padx=5, sticky="w")
        
        # Commission
        tk.Label(
            frame,
            text="Commission:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=3, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.commission,
            font=("Arial", 11),
            width=30
        ).grid(row=3, column=1, pady=10, padx=5, sticky="w")
        
        # Spread
        tk.Label(
            frame,
            text="Spread:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=4, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.spread,
            font=("Arial", 11),
            width=30
        ).grid(row=4, column=1, pady=10, padx=5, sticky="w")
    
    def setup_trading_tab(self, parent):
        """Setup the trading settings configuration tab"""
        frame = tk.Frame(parent, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Asset
        tk.Label(
            frame,
            text="Trading Asset:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=10)
        
        assets = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
        asset_dropdown = ttk.Combobox(
            frame,
            textvariable=self.asset,
            values=assets,
            font=("Arial", 11),
            width=28,
            state="readonly"
        )
        asset_dropdown.grid(row=0, column=1, pady=10, padx=5, sticky="w")
        
        # Timeframes
        tk.Label(
            frame,
            text="Timeframes:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        # Frame for timeframe checkboxes
        tf_frame = tk.Frame(frame)
        tf_frame.grid(row=1, column=1, pady=10, padx=5, sticky="w")
        
        # Create timeframe checkbuttons
        self.timeframe_vars = {}
        for i, tf in enumerate(self.available_timeframes):
            var = tk.BooleanVar(value=tf in self.selected_timeframes)
            self.timeframe_vars[tf] = var
            cb = tk.Checkbutton(
                tf_frame,
                text=tf,
                variable=var,
                font=("Arial", 10),
                command=self.update_timeframes
            )
            cb.grid(row=0, column=i, padx=5)
        
        # Risk section
        risk_frame = tk.LabelFrame(frame, text="Risk Management", padx=10, pady=10, font=("Arial", 11))
        risk_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=20)
        
        # Risk R
        tk.Label(
            risk_frame,
            text="Risk (R):",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        tk.Entry(
            risk_frame,
            textvariable=self.risk_r,
            font=("Arial", 11),
            width=10
        ).grid(row=0, column=1, pady=5, padx=5, sticky="w")
        
        # Description label for R
        tk.Label(
            risk_frame,
            text="(Risk ratio 0.0-1.0)",
            font=("Arial", 9),
            fg="gray"
        ).grid(row=0, column=2, sticky="w", pady=5, padx=5)
        
        # Max Weight
        tk.Label(
            risk_frame,
            text="Max Weight:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        tk.Entry(
            risk_frame,
            textvariable=self.max_weight,
            font=("Arial", 11),
            width=10
        ).grid(row=1, column=1, pady=5, padx=5, sticky="w")
        
        # Description label for Max Weight
        tk.Label(
            risk_frame,
            text="(Maximum position weight)",
            font=("Arial", 9),
            fg="gray"
        ).grid(row=1, column=2, sticky="w", pady=5, padx=5)
    
    def update_timeframes(self):
        """Update the selected timeframes list based on checkbox values"""
        self.selected_timeframes = [tf for tf, var in self.timeframe_vars.items() if var.get()]
    
    def setup_runtime_tab(self, parent):
        """Setup the runtime settings configuration tab"""
        frame = tk.Frame(parent, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Emergency mode section
        emergency_frame = tk.LabelFrame(frame, text="Emergency Mode", padx=10, pady=10, font=("Arial", 11))
        emergency_frame.pack(fill=tk.X, pady=10)
        
        # Status checkbox
        status_cb = tk.Checkbutton(
            emergency_frame,
            text="Enable Emergency Mode",
            variable=self.emergency_status,
            font=("Arial", 11)
        )
        status_cb.grid(row=0, column=0, sticky="w", pady=5)
        
        # Emergency password
        tk.Label(
            emergency_frame,
            text="Emergency Password:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        tk.Entry(
            emergency_frame,
            textvariable=self.emergency_password,
            font=("Arial", 11),
            width=25,
            show="*"
        ).grid(row=1, column=1, pady=5, padx=5, sticky="w")
        
        # Additional settings
        additional_frame = tk.LabelFrame(frame, text="Additional Settings", padx=10, pady=10, font=("Arial", 11))
        additional_frame.pack(fill=tk.X, pady=20)
        
        # Another function syntax
        tk.Label(
            additional_frame,
            text="Another Function Syntax:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        tk.Entry(
            additional_frame,
            textvariable=self.another_function,
            font=("Arial", 11),
            width=25
        ).grid(row=0, column=1, pady=5, padx=5, sticky="w")
    
    def show_bot(self):
        """Display the trading bot screen with all components"""
        self.clear_content()
        self.current_screen = "bot"
        
        # If this is the final destination, we could hide the back button
        # or keep it to let users go back to config
        self.back_button.pack(side=tk.LEFT, anchor=tk.NW)
        
        bot_frame = tk.Frame(self.content_frame, padx=20, pady=20)
        bot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Trading Bot header
        tk.Label(
            bot_frame,
            text="Trading Bot Control Center",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Create a horizontal split with control panel on the left and data on the right
        split_frame = tk.PanedWindow(bot_frame, orient=tk.HORIZONTAL)
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame for controls
        left_frame = tk.Frame(split_frame, width=300)
        split_frame.add(left_frame)
        
        # Right frame for data
        right_frame = tk.Frame(split_frame, width=600)
        split_frame.add(right_frame)
        
        # Add components to left frame
        self.create_control_panel(left_frame)
        self.create_command_interface(left_frame)
        
        # Add components to right frame
        self.create_dashboard(right_frame)
        self.create_positions_table(right_frame)
        
        # Terminal output at the bottom of the right frame
        self.create_terminal(right_frame)
        
        # Initialize IPC for communication with the bot
        self.setup_ipc()

    def create_control_panel(self, parent_frame):
        """Create control panel with start/stop buttons and status indicator"""
        controls_frame = tk.LabelFrame(parent_frame, text="Bot Controls", padx=10, pady=10, font=("Arial", 11))
        controls_frame.pack(fill=tk.X, pady=10)
        
        # Button frame
        button_frame = tk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Start button
        self.start_button = tk.Button(
            button_frame,
            text="Start Bot",
            command=self.start_bot,
            font=("Arial", 11),
            bg="#27ae60",
            fg="white",
            width=12,
            height=1
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Stop button
        self.stop_button = tk.Button(
            button_frame,
            text="Stop Bot",
            command=self.stop_bot,
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=12,
            height=1,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Restart button
        restart_button = tk.Button(
            button_frame,
            text="Restart Bot",
            command=self.restart_bot,
            font=("Arial", 11),
            bg="#f39c12",
            fg="white",
            width=12,
            height=1,
            state=tk.DISABLED
        )
        restart_button.grid(row=1, column=0, padx=5, pady=5)
        self.restart_button = restart_button
        
        # Settings button
        settings_button = tk.Button(
            button_frame,
            text="Bot Settings",
            command=self.show_config,
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            width=12,
            height=1
        )
        settings_button.grid(row=1, column=1, padx=5, pady=5)
        
        # Status indicator
        status_frame = tk.Frame(controls_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            status_frame,
            text="Bot Status:",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.status_var = tk.StringVar(value="Not Running")
        self.status_indicator = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 11),
            fg="#e74c3c"
        )
        self.status_indicator.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Run time indicator
        tk.Label(
            status_frame,
            text="Run Time:",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.runtime_var = tk.StringVar(value="00:00:00")
        runtime_label = tk.Label(
            status_frame,
            textvariable=self.runtime_var,
            font=("Arial", 11)
        )
        runtime_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def create_terminal(self, parent_frame):
        """Creates the terminal for bot output"""
        terminal_frame = tk.LabelFrame(parent_frame, text="Bot Terminal Output", padx=5, pady=5, font=("Arial", 11))
        terminal_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add terminal control buttons
        terminal_controls = tk.Frame(terminal_frame)
        terminal_controls.pack(fill=tk.X)
        
        clear_button = tk.Button(
            terminal_controls,
            text="Clear Terminal",
            command=self.clear_terminal,
            font=("Arial", 9)
        )
        clear_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = tk.Checkbutton(
            terminal_controls,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            font=("Arial", 9)
        )
        auto_scroll_cb.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Terminal text widget
        self.terminal = scrolledtext.ScrolledText(
            terminal_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#f8f8f8",
            wrap=tk.WORD
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)
        self.terminal.config(state=tk.DISABLED)

    def clear_terminal(self):
        """Clear the terminal output"""
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete(1.0, tk.END)
        self.terminal.config(state=tk.DISABLED)

    def restart_bot(self):
        """Restart the trading bot"""
        if self.bot_running:
            self.stop_bot()
            # Wait a moment for the bot to fully stop
            self.root.after(1000, self.start_bot)
        else:
            self.start_bot()

    def start_bot(self):
        """Start the trading bot and capture its output"""
        if not self.bot_running:
            self.append_to_terminal("Starting trading bot...\n")
            self.status_var.set("Starting...")
            self.status_indicator.config(fg="#f39c12")  # Yellow for starting
            
            # Run the bot in a separate thread
            self.bot_thread = threading.Thread(target=self.run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            # Update button states
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
    
    def run_bot(self):
        """Run the main.py script and capture its output in real-time"""
        try:
            # Ensure the script exists
            script_path = "d:/Trade/Bot/TradingBot101/main.py"
            if not os.path.exists(script_path):
                self.append_to_terminal(f"Error: Script not found at {script_path}\n")
                self.status_var.set("Error")
                self.status_indicator.config(fg="#e74c3c")  # Red for error
                self.reset_buttons()
                return
            
            # Create the directory structure if it doesn't exist
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            
            # Start the process with Python to ensure colors are preserved
            # The universal_newlines=True ensures that output is returned as strings
            # bufsize=1 ensures line buffering
            self.bot_process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # This prevents a console window from appearing
            )
            
            self.bot_running = True
            self.status_var.set("Running")
            self.status_indicator.config(fg="#27ae60")  # Green for running
            
            # Start a separate thread to read the output
            output_thread = threading.Thread(target=self.read_output)
            output_thread.daemon = True
            output_thread.start()
            
        except Exception as e:
            self.append_to_terminal(f"Error: {str(e)}\n")
            self.status_var.set("Error")
            self.status_indicator.config(fg="#e74c3c")  # Red for error
            self.reset_buttons()
            self.bot_running = False

    def read_output(self):
        """Read output from the bot process and display it in the terminal"""
        try:
            while self.bot_running and self.bot_process and self.bot_process.poll() is None:
                line = self.bot_process.stdout.readline()
                if line:
                    self.append_to_terminal(line)
                else:
                    # Small sleep to prevent CPU hogging
                    time.sleep(0.1)
                    
            # Process ended, check return code
            if self.bot_process:
                return_code = self.bot_process.poll()
                self.append_to_terminal(f"\nBot exited with code {return_code}\n")
                self.status_var.set(f"Stopped (exit code {return_code})")
                self.status_indicator.config(fg="#e74c3c")  # Red for stopped
                self.reset_buttons()
                self.bot_running = False
                
        except Exception as e:
            self.append_to_terminal(f"Error in reading output: {str(e)}\n")
            self.bot_running = False
            self.reset_buttons()

    def stop_bot(self):
        """Stop the running bot"""
        if self.bot_running and self.bot_process:
            self.append_to_terminal("Stopping trading bot...\n")
            
            # Set the flag first to prevent further processing
            self.bot_running = False
            
            # Terminate the process
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
            
            self.status_var.set("Stopped")
            self.status_indicator.config(fg="#e74c3c")  # Red for stopped
            self.reset_buttons()

    def reset_buttons(self):
        """Reset buttons to their default state"""
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
        
        # Reset the process reference
        self.bot_process = None

    def append_to_terminal(self, text, add_timestamp=False):
        """Append text to the terminal widget with optional timestamp"""
        def _append():
            self.terminal.config(state=tk.NORMAL)
            
            # Add timestamp if requested
            if add_timestamp:
                timestamp = time.strftime("[%H:%M:%S] ", time.localtime())
                self.terminal.insert(tk.END, timestamp)
            
            # Insert the text
            self.terminal.insert(tk.END, text)
            
            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.terminal.see(tk.END)
                
            self.terminal.config(state=tk.DISABLED)
        
        # Schedule the update on the main thread
        self.root.after(0, _append)

    def start_runtime_timer(self):
        """Start a timer to track bot runtime"""
        self.start_time = time.time()
        self.update_runtime()

    def update_runtime(self):
        """Update the runtime display"""
        if self.bot_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.runtime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Schedule the next update
            self.root.after(1000, self.update_runtime)
    def create_positions_table(self, parent_frame):
        """Create a table to display and manage open positions"""
        positions_frame = tk.LabelFrame(parent_frame, text="Open Positions", padx=10, pady=10, font=("Arial", 11))
        positions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a frame for the table
        table_frame = tk.Frame(positions_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview widget
        columns = ("id", "symbol", "type", "volume", "open_price", "current_price", "profit", "open_time")
        self.positions_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Define column headings
        self.positions_tree.heading("id", text="ID")
        self.positions_tree.heading("symbol", text="Symbol")
        self.positions_tree.heading("type", text="Type")
        self.positions_tree.heading("volume", text="Volume")
        self.positions_tree.heading("open_price", text="Open Price")
        self.positions_tree.heading("current_price", text="Current Price")
        self.positions_tree.heading("profit", text="Profit")
        self.positions_tree.heading("open_time", text="Open Time")
        
        # Define column widths
        self.positions_tree.column("id", width=50)
        self.positions_tree.column("symbol", width=80)
        self.positions_tree.column("type", width=70)
        self.positions_tree.column("volume", width=70)
        self.positions_tree.column("open_price", width=100)
        self.positions_tree.column("current_price", width=100)
        self.positions_tree.column("profit", width=80)
        self.positions_tree.column("open_time", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add right-click menu for position management
        self.create_position_context_menu()

    def create_position_context_menu(self):
        """Create a context menu for position management"""
        self.position_menu = tk.Menu(self.positions_tree, tearoff=0)
        self.position_menu.add_command(label="Close Position", command=self.close_selected_position)
        self.position_menu.add_command(label="Modify Position", command=self.modify_selected_position)
        self.position_menu.add_command(label="Position Details", command=self.show_position_details)
        
        # Bind right-click event
        self.positions_tree.bind("<Button-3>", self.show_position_menu)

    def show_position_menu(self, event):
        """Show the position context menu on right-click"""
        # Select row under mouse
        iid = self.positions_tree.identify_row(event.y)
        if iid:
            self.positions_tree.selection_set(iid)
            self.position_menu.post(event.x_root, event.y_root)

    def close_selected_position(self):
        """Close the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        position_id = self.positions_tree.item(selection[0], "values")[0]
        self.send_command(f"close_position {position_id}")

    def modify_selected_position(self):
        """Open dialog to modify the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        position_id = self.positions_tree.item(selection[0], "values")[0]
        # Open a dialog to modify position parameters
        # ...

    def show_position_details(self):
        """Show detailed information about the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        position_id = self.positions_tree.item(selection[0], "values")[0]
        self.send_command(f"position_details {position_id}")

    def setup_ipc(self):
        """Set up inter-process communication with the bot"""
        # Create a directory for IPC files if it doesn't exist
        self.ipc_dir = "d:/Trade/Bot/TradingBot101/ipc"
        os.makedirs(self.ipc_dir, exist_ok=True)
        
        # Define IPC file paths
        self.command_file = os.path.join(self.ipc_dir, "command.txt")
        self.status_file = os.path.join(self.ipc_dir, "status.json")
        
        # Start IPC monitoring thread
        self.start_ipc_monitor()

    def start_ipc_monitor(self):
        """Start a thread to monitor IPC files for updates from the bot"""
        self.ipc_running = True
        self.ipc_thread = threading.Thread(target=self.monitor_ipc)
        self.ipc_thread.daemon = True
        self.ipc_thread.start()

    def monitor_ipc(self):
        """Monitor IPC files for updates from the bot"""
        last_modified = 0
        
        while self.ipc_running:
            try:
                # Check for status updates from the bot
                if os.path.exists(self.status_file):
                    mod_time = os.path.getmtime(self.status_file)
                    
                    if mod_time > last_modified:
                        last_modified = mod_time
                        self.update_status_from_file()
                
                # Sleep to prevent excessive CPU usage
                time.sleep(0.5)
                
            except Exception as e:
                self.append_to_terminal(f"IPC error: {str(e)}\n")
        
    def update_status_from_file(self):
        """Update UI with status information from the bot"""
        try:
            with open(self.status_file, "r") as f:
                status_data = json.load(f)
                
                # Update UI elements with status data
                self.root.after(0, lambda: self.update_ui_with_status(status_data))
                
        except Exception as e:
            self.append_to_terminal(f"Error reading status: {str(e)}\n")

    def update_ui_with_status(self, status_data):
        """Update UI elements with status data from the bot"""
        try:
            # Update account metrics
            if "account" in status_data:
                acc = status_data["account"]
                self.balance_var.set(f"${acc.get('balance', 0):.2f}")
                self.equity_var.set(f"${acc.get('equity', 0):.2f}")
                
                profit = acc.get('profit', 0)
                self.profit_var.set(f"${profit:.2f}")
                # Color profit based on value
                if profit > 0:
                    self.profit_label.config(fg="#27ae60")  # Green for profit
                elif profit < 0:
                    self.profit_label.config(fg="#e74c3c")  # Red for loss
                else:
                    self.profit_label.config(fg="black")
                    
                self.positions_var.set(str(acc.get('positions', 0)))
            
            # Additional status updates as needed
            if "status" in status_data:
                status = status_data["status"]
                if status.get("message"):
                    self.append_to_terminal(f"[BOT] {status['message']}\n")
                    
        except Exception as e:
            self.append_to_terminal(f"Error updating UI: {str(e)}\n")

    def create_command_interface(self, parent_frame):
        """Create an interface for sending commands to the bot"""
        cmd_frame = tk.LabelFrame(parent_frame, text="Command Center", padx=10, pady=10, font=("Arial", 11))
        cmd_frame.pack(fill=tk.X, pady=10)
        
        # Command entry and execution
        cmd_entry_frame = tk.Frame(cmd_frame)
        cmd_entry_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cmd_entry_frame, text="Command:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.cmd_var = tk.StringVar()
        cmd_entry = tk.Entry(cmd_entry_frame, textvariable=self.cmd_var, font=("Arial", 11), width=40)
        cmd_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        send_btn = tk.Button(
            cmd_entry_frame, 
            text="Send", 
            command=self.send_command, 
            font=("Arial", 11),
            bg="#3498db", 
            fg="white", 
            width=10
        )
        send_btn.pack(side=tk.LEFT, padx=5)
        
        # Predefined commands section
        predef_frame = tk.Frame(cmd_frame)
        predef_frame.pack(fill=tk.X, pady=5)
        
        common_commands = [
            ("Close All Positions", "close_all"),
            ("Emergency Stop", "emergency_stop"),
            ("Show Statistics", "show_stats"),
            ("Update Config", "update_config")
        ]
        
        tk.Label(predef_frame, text="Quick Commands:", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        for i, (label, cmd) in enumerate(common_commands):
            cmd_btn = tk.Button(
                predef_frame,
                text=label,
                command=lambda c=cmd: self.send_command(c),
                font=("Arial", 10),
                bg="#ecf0f1",
                width=15
            )
            cmd_btn.grid(row=0, column=i+1, padx=5, pady=5)

    def send_command(self, command=None):
        """Send a command to the running bot process"""
        if not self.bot_running or not self.bot_process:
            messagebox.showerror("Error", "Bot is not running")
            return
        
        # Get the command from entry or parameter
        cmd = command if command else self.cmd_var.get()
        if not cmd:
            return
        
        # Log the command
        self.append_to_terminal(f"\n> Executing command: {cmd}\n")
        
        try:
            # There are multiple ways to send commands to the running process:
            
            # Option 1: Write to stdin if the bot supports it
            # self.bot_process.stdin.write(f"{cmd}\n")
            # self.bot_process.stdin.flush()
            
            # Option 2: Use a socket or named pipe for IPC
            
            # Option 3: Use a command file that the bot checks periodically
            command_file = "d:/Trade/Bot/TradingBot101/command.txt"
            with open(command_file, "w") as f:
                f.write(cmd)
            
            # Clear the command entry
            self.cmd_var.set("")
            
        except Exception as e:
            self.append_to_terminal(f"Error sending command: {str(e)}\n")

    def create_dashboard(self, parent_frame):
        """Create a dashboard to visualize trading data"""
        dashboard_frame = tk.LabelFrame(parent_frame, text="Trading Dashboard", padx=10, pady=10, font=("Arial", 11))
        dashboard_frame.pack(fill=tk.X, pady=10)
        
        # Create a frame for key metrics
        metrics_frame = tk.Frame(dashboard_frame)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        # Create labels for key metrics with placeholders
        self.balance_var = tk.StringVar(value="$0.00")
        self.equity_var = tk.StringVar(value="$0.00")
        self.profit_var = tk.StringVar(value="$0.00")
        self.positions_var = tk.StringVar(value="0")
        
        # Balance
        tk.Label(metrics_frame, text="Balance:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Label(metrics_frame, textvariable=self.balance_var, font=("Arial", 11)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Equity
        tk.Label(metrics_frame, text="Equity:", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        tk.Label(metrics_frame, textvariable=self.equity_var, font=("Arial", 11)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Profit
        tk.Label(metrics_frame, text="Profit:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.profit_label = tk.Label(metrics_frame, textvariable=self.profit_var, font=("Arial", 11))
        self.profit_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Open Positions
        tk.Label(metrics_frame, text="Open Positions:", font=("Arial", 11, "bold")).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        tk.Label(metrics_frame, textvariable=self.positions_var, font=("Arial", 11)).grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.mainloop()