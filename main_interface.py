import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import json
import time
import typing
from datetime import datetime
import parameters

class TradingBotGUI_class:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TradingBot101 Interface")
        self.root.geometry("1500x750")
        self.root.minsize(800, 500)
        self.Is_fullscreen = True

        # Store user credentials and settings
        self.username = tk.StringVar(None, "admin", "username")
        self.password = tk.StringVar(None, "password", "password")
        self.authenticated = False
        self.bot_process = None
        self.Is_custom_notbook_created = False

        # Load config from JSON file
        self.config_file_path = "d:/Trade/Bot/TradingBot101/config.json"
        self.config = self.load_config_Function()
        
        # Create variables for config settings
        self.create_config_variables_Function()

        # Navigation and workflow state
        self.current_screen = "welcome"
        self.screen_history = []
        
        # Initialize GUI components
        self.create_header_Function()
        self.create_content_frame_Function()
        
        # Start with welcome screen
        self.show_welcome_Function()
    
    def create_header_Function(self):
        """Creates the header with application title and description"""
        self.header_frame = tk.Frame(self.root, bg="#2c3e50")
        self.header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            self.header_frame, 
            text="Trading Bot 101", 
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
    
    def create_content_frame_Function(self):
        """Creates the main content frame that will hold different screens"""
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Back button (initially hidden)
        self.back_btn_frame = tk.Frame(self.content_frame)
        self.back_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.back_button = tk.Button(
            self.back_btn_frame,
            text="← Back",
            command=self.go_back_Function,
            font=("Arial", 10),
            width=10
        )
        # Only show back button when needed
        
    def create_config_variables_Function(self):
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
    
    def load_config_Function(self):
        """Load config from file or return default if file doesn't exist"""
        try:
            with open(self.config_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return a default config structure if file doesn't exist
            return {
                "account_info": {
                    "login": 600011860,
                    "password": "!1T9219g",
                    "server": "Opogroup-Server1",
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
                        "password": "ashkan"
                    },
                    "Another_function_syntax": "ashkan"
                }
            }
    
    def save_config_Function(self):
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
    
    def clear_content_Function(self):
        """Clear the content frame to prepare for a new screen"""
        # Save current screen to history before clearing
        if self.current_screen:
            self.screen_history.append(self.current_screen)
        
        # Destroy all widgets in the content area
        for widget in self.content_frame.winfo_children():
            if widget != self.back_btn_frame:  # Preserve back button frame
                widget.destroy()
    
    def go_back_Function(self):
        """Navigate to the previous screen"""
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            
            # Don't add the current screen to history when going back
            # temp = self.current_screen
            self.current_screen = ""
            
            # Show the previous screen
            if previous_screen == "welcome":
                self.show_welcome_Function()
            elif previous_screen == "login":
                self.show_login_Function()
            elif previous_screen == "config":
                self.show_config_Function()
            
            # If we're back at the first screen, hide the back button
            if not self.screen_history:
                self.back_button.pack_forget()
    
    def show_welcome_Function(self):
        """Display the welcome screen"""
        self.clear_content_Function()
        self.current_screen = "welcome"
        
        # Hide back button on welcome screen
        self.back_button.pack_forget()
        
        welcome_frame = tk.Frame(self.content_frame, bg= "white", padx=40, pady=40)
        welcome_frame.pack(expand=True)
        welcome_frame.bind("<Shift-Return>", lambda event: self.show_login_Function())
        welcome_frame.focus_set()
        
        # Welcome header
        welcome_label = tk.Label(
            welcome_frame,
            text="Welcome to TradingBot101",
            font=("Arial", 22, "bold"), 
            bg= "white"
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
            font=("Segoe UI", 12),
            justify="center",
            wraplength=600, 
            bg= "white"
        )
        message_label.pack(pady=(0, 40))
        
        # Start button
        start_button = tk.Button(
            welcome_frame,
            text="Let's Start",
            command=self.show_login_Function,
            font=("Arial", 14, "bold"),
            bg="#4682B4",
            fg="white",
            relief= "ridge",
            padx=20,
            pady=10,
            width=15,
            height=1
        )
        start_button.bind("<Enter>", lambda e: self.on_enter_Function(e, "#003153", 14))
        start_button.bind("<Leave>", lambda e: self.on_leave_Function(e, "#4682B4", 10))
        start_button.pack()
        
        # Version info
        version_label = tk.Label(
            welcome_frame,
            text="Version 1.0.1",
            font=("Arial", 9), 
            bg= "white"
        )
        version_label.pack(side=tk.BOTTOM, pady=20)
    
    def show_login_Function(self, Is_valid_Input: bool = True):
        """Display the login screen"""
        if self.authenticated:
            self.screen_history = []
            self.show_config_Function()
            return
        self.clear_content_Function()
        self.current_screen = "login"
        
        # Show back button
        self.back_button.pack(side=tk.LEFT, anchor=tk.NW)
        
        login_frame = tk.Frame(self.content_frame,bg= "white", padx=40, pady=40)
        login_frame.pack(expand=True)
        login_frame.bind("<Shift-Return>", lambda event: self.authenticate_user_Function())
        login_frame.focus_set()
        
        # Login header
        tk.Label(
            login_frame,
            text="User Authentication",
            font=("Arial", 18, "bold"), 
            bg= "white"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        tk.Label(
            login_frame,
            text="Username:",
            font=("Arial", 12), 
            bg= "white"
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        username_entry = tk.Entry(
            login_frame,
            textvariable=self.username,
            font=("Arial", 12),
            width=25, 
            bg= "white"
        )
        username_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Password
        tk.Label(
            login_frame,
            text="Password:",
            font=("Arial", 12), 
            bg= "white"
        ).grid(row=2, column=0, sticky="w", pady=10)
        
        password_entry = tk.Entry(
            login_frame,
            textvariable=self.password,
            font=("Arial", 12),
            width=25,
            show="*", 
            bg= "white"
        )
        password_entry.grid(row=2, column=1, pady=10, padx=10)

        def on_enter_username(event, The_password_entry: tk.Entry):
            The_password_entry.focus_set()

        def on_enter_password(event):
            self.authenticate_user_Function()

        username_entry.bind('<Return>', lambda event: on_enter_username(event, password_entry))
        password_entry.bind('<Return>', lambda event: on_enter_password(event))

        def toggle_password(The_is_show_password: tk.BooleanVar):
            """Show or hide password based on checkbox state"""
            if The_is_show_password.get():
                password_entry.config(show="")  # Show password as text
            else:
                password_entry.config(show="*")  # Hide password

        Is_show_password= tk.BooleanVar(value=False) 
        showPassword_checkbox = tk.Checkbutton(
            login_frame,
            text= "show password",
            variable= Is_show_password,
            command= lambda: toggle_password(Is_show_password),
            font=("Arial", 8), 
            bg= "white"
        )
        showPassword_checkbox.grid(row=3, column=0,columnspan=2, padx=0 ,pady= 4)
        
        # Login button
        login_button = tk.Button(
            login_frame,
            text="Login",
            command=self.authenticate_user_Function,
            font=("Arial", 12),
            bg="#4682B4",
            fg="#F5F5F5",
            relief= "ridge",
            activebackground= "#003153",
            activeforeground="white",
            width=15,
            height=1
        )
        login_button.bind("<Enter>", lambda e: self.on_enter_Function(e, "#003153", 10))
        login_button.bind("<Leave>", lambda e: self.on_leave_Function(e, "#4682B4", 0))
        login_button.grid(row=4, column=0, columnspan=2, pady=30)

        if not Is_valid_Input:
            # Password
            tk.Label(
                login_frame,
                text="Error: Incorrect username or password",
                font=("Arial", 12),
                fg= "red"
            ).grid(row=4, column=0, columnspan=2, pady=(0, 30))
            
    def authenticate_user_Function(self):
        """Authenticate user credentials"""
        # In a real application, you would validate against a secure database
        # This is a simplified example
        valid_username = "admin"
        valid_password = "password"
        
        if self.username.get() == valid_username and self.password.get() == valid_password:
            self.authenticated = True
            self.screen_history = []
            self.show_config_Function()
        else:
            self.show_login_Function(False)

    def _create_custom_notebook_Function(self, parent: tk.Frame) -> ttk.Notebook:
        if self.Is_custom_notbook_created: 
            return ttk.Notebook(parent, style='Custom.TNotebook')
        # Create a custom class by inheriting from ttk.Notebook
        style = ttk.Style()
        
        # Try the 'clam' theme which is more customizable
        style.theme_use('clam')
        
        # Create an empty element to be used for active/selected tab
        style.element_create('Custom.Notebook.tab', 'from', 'default')
        
        # Define a new layout that uses your custom tab element
        style.layout('Custom.TNotebook.Tab', [
            ('Custom.Notebook.tab', {
                'sticky': 'nswe', 
                'children': [
                    ('Notebook.padding', {
                        'side': 'top', 
                        'sticky': 'nswe',
                        'children': [
                            ('Notebook.label', {'side': 'top', 'sticky': ''})
                        ]
                    })
                ]
            })
        ])
        
        # Configure the custom style for normal, selected, and active states
        style.configure('Custom.TNotebook', background='lightgrey', borderwidth=0)
        style.configure('Custom.TNotebook.Tab', 
                    background='lightgrey',  # Default tab background
                    foreground='black',      # Default tab text
                    padding=[10, 4],         # Tab padding
                    borderwidth=1)           # Tab border width
        
        # Map the styles for different states - this is the key part
        style.map('Custom.TNotebook.Tab',
                background=[('selected', '#4682B4'),   # Selected tab background
                            ('active', '#003153')],    # Hover tab background
                foreground=[('selected', '#EEEEEE'),     # Selected tab text color
                            ('active', 'white')])      # Hover tab text color
        
        # Create the notebook with our custom style
        notebook = ttk.Notebook(parent, style='Custom.TNotebook')
        self.Is_custom_notbook_created = True
        return notebook

    def on_enter_Function(self, e, color, The_padx):
        e.widget.config(bg=color, padx= The_padx)

    def on_leave_Function(self, e, color, The_padx):
        e.widget.config(bg=color, padx= The_padx) 

    def show_config_Function(self):
        """Display the configuration screen"""
        self.clear_content_Function()
        self.current_screen = "config"
   
        # Show back button
        # self.back_button.pack(side=tk.LEFT, anchor=tk.NW)

        self.back_button.pack_forget()
        # if len(self.screen_history) == 1:
            # self.back_button.pack_forget()
        
        # Create a frame with a notebook for different config section
        config_frame = self._create_custom_notebook_Function(self.content_frame)
        config_frame.pack(fill=tk.BOTH, expand=True, padx= 100, pady= 50)
        config_frame.bind("<Shift-Return>", lambda event: self.show_bot_Function())
        config_frame.focus_set()

        tk.Label(
            config_frame,
            text="Trading Bot Configuration",
            font=("Arial", 16, "bold"), 
            bg= "lightgrey"
        ).pack(pady=(10, 15))
         
        # Create notebook for config sections
        config_notebook = ttk.Notebook(config_frame, style="Custom.TNotebook")
        config_notebook.pack(fill=tk.BOTH,expand=True, padx=10, pady=10)
        # Account Info tab
        account_tab = ttk.Frame(config_notebook)
        config_notebook.add(account_tab, text="MT5 Account")
        self.setup_account_tab_Function(account_tab)
        
        # Trading Settings tab
        trading_tab = ttk.Frame(config_notebook)
        config_notebook.add(trading_tab, text="Trading Settings")
        self.setup_trading_tab_Function(trading_tab)
        
        # Runtime Settings tab
        runtime_tab = ttk.Frame(config_notebook)
        config_notebook.add(runtime_tab, text="Runtime Settings")
        self.setup_runtime_tab_Function(runtime_tab)
        
        # Save and Continue button
        button_frame = tk.Frame(config_frame, bg="lightgrey")
        button_frame.pack(fill="both", expand=True)
        
        save_button = tk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config_Function,
            font=("Segoe UI", 11, "bold"),
            bg="#4682B4",
            fg="#F5F5F5",
            activebackground= "#003153",
            activeforeground="white",
            borderwidth=1,
            relief= "ridge",
            width=25,
            height=2
        )
        save_button.bind("<Enter>", lambda e: self.on_enter_Function(e, "#003153", 20))
        save_button.bind("<Leave>", lambda e: self.on_leave_Function(e, "#4682B4", 10))
        save_button.place(relx=0.1, rely=0.5, anchor="sw")

        continue_button = tk.Button(
            button_frame,
            text="Continue to Trading Bot",
            command=self.show_bot_Function,
            font=("Segoe UI", 11, "bold"),
            bg="#1A252F",
            fg="#E0E0E0",
            activebackground="#003153",
            activeforeground="white",
            borderwidth=1,
            relief= "ridge",
            width=25,
            height=2
        )
        continue_button.bind("<Enter>", lambda e: self.on_enter_Function(e, "#003153", 20))
        continue_button.bind("<Leave>", lambda e: self.on_leave_Function(e, "#1A252F", 10))        
        continue_button.place(relx=0.9, rely=0.5, anchor="se")
    
    def setup_account_tab_Function(self, parent: ttk.Frame):
        """Setup the account info configuration tab"""
        frame = tk.Frame(parent, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            frame,
            text="Please, Enter your MT5 account infromation",
            font=("Arial", 16), 
            # fg= "darkgrey",
        ).grid(row=0, column=0, columnspan=4, pady=30)

        # Login ID
        tk.Label(
            frame,
            text="Login ID:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.login,
            font=("Arial", 11),
            width=30
        ).grid(row=1, column=1, pady=10, padx=5, sticky="w")
        
        # Password
        tk.Label(
            frame,
            text="Password:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=2, column=0, sticky="w", pady=10)
            
        account_password_entry = tk.Entry(
            frame,
            textvariable=self.account_password,
            font=("Arial", 11),
            width=30,
            show="*"
        )
        account_password_entry.grid(row=2, column=1, pady=10, padx=5, sticky="w")

        def show_password(The_is_show_password: tk.BooleanVar):
            if The_is_show_password.get():
                account_password_entry.config(show = "")
            else:
                account_password_entry.config(show= "*")

        Is_show_password = tk.BooleanVar(value= False)
        tk.Checkbutton(
            frame,
            text= "show password",
            variable= Is_show_password,
            command= lambda: show_password(Is_show_password)
        ).grid(row=2, column= 3, padx=4, pady=4)
        
        # Server
        tk.Label(
            frame,
            text="Server:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=3, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.server,
            font=("Arial", 11),
            width=30
        ).grid(row=3, column=1, pady=10, padx=5, sticky="w")
        
        # Commission
        tk.Label(
            frame,
            text="Commission:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=4, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.commission,
            font=("Arial", 11),
            width=30
        ).grid(row=4, column=1, pady=10, padx=5, sticky="w")
        
        # Spread
        tk.Label(
            frame,
            text="Spread:",
            font=("Arial", 11),
            anchor="w"
        ).grid(row=5, column=0, sticky="w", pady=10)
        
        tk.Entry(
            frame,
            textvariable=self.spread,
            font=("Arial", 11),
            width=30
        ).grid(row=5, column=1, pady=10, padx=5, sticky="w")
    
    def setup_trading_tab_Function(self, parent: ttk.Frame):
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
                command=self.update_timeframes_Function
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
    
    def update_timeframes_Function(self):
        """Update the selected timeframes list based on checkbox values"""
        self.selected_timeframes = [tf for tf, var in self.timeframe_vars.items() if var.get()]
    
    def setup_runtime_tab_Function(self, parent):
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
    
    def show_bot_Function(self):
        """Display the trading bot screen with all components"""
        self.clear_content_Function()
        self.current_screen = "bot"

        # If this is the final destination, we could hide the back button
        # or keep it to let users go back to config
        # self.back_button.pack(side=tk.LEFT, anchor=tk.NW)

        # Create bot_frame inside scrollable_frame
        bot_frame = self._create_custom_notebook_Function(self.content_frame)
        bot_frame.pack(fill=tk.BOTH, expand=True, padx= 100, pady= 50)

        # Trading Bot header
        tk.Label(
            bot_frame,
            text="Trading Bot Control Center",
            font=("Arial", 16, "bold"),
            bg="lightgrey"
        ).pack(pady=(5, 15))

        bot_nootbook = ttk.Notebook(bot_frame, style="Custom.TNotebook")
        bot_nootbook.pack(fill=tk.BOTH,expand=True, padx=10, pady=10)

        # Bot Dashboard Tab
        bot_Dashboard_Tab = ttk.Frame(bot_nootbook)
        bot_nootbook.add(bot_Dashboard_Tab, text="Bot Dashboard")
        self.bot_dashboard_tab_Function(bot_Dashboard_Tab)


        # Position Manager
        position_manager_tab = ttk.Frame(bot_nootbook)
        bot_nootbook.add(position_manager_tab, text="Position Manager")
        self.poistion_manager_tab_Function(position_manager_tab)

        # History
        history_trades_tab = ttk.Frame(bot_nootbook)
        bot_nootbook.add(history_trades_tab, text="History")
        self.history_trades_tab_Function(history_trades_tab)

    def bot_dashboard_tab_Function(self, parent: ttk.Frame):
        # Create a horizontal split for the upper and lower sections of the bot_frame
        upper_lower_split = tk.PanedWindow(parent, orient=tk.VERTICAL)
        upper_lower_split.pack(fill=tk.X, expand=True)

        # Upper section for the vertical split (same as before)
        upper_frame = tk.Frame(upper_lower_split, height=200)
        upper_frame.pack_propagate(False)  # Prevent the frame from shrinking
        upper_lower_split.add(upper_frame)

        # Create a vertical split in the upper section
        split_frame = tk.PanedWindow(upper_frame, orient=tk.HORIZONTAL)
        split_frame.pack(fill=tk.X, expand=True)

        # Left frame for controls
        left_frame = tk.Frame(split_frame,width=600)
        left_frame.pack_propagate(False)
        left_frame.pack(fill=tk.X, expand=True)
        split_frame.add(left_frame)
        
        # Add components to left frame
        self.create_control_panel_Function(left_frame)

        # Right frame for data
        right_frame = tk.Frame(split_frame)
        right_frame.pack(fill=tk.X, expand=True)
        split_frame.add(right_frame)

        #add command section to right frame 
        self.create_command_interface_Function(right_frame)

        # Lower section 
        lower_frame = tk.Frame(upper_lower_split)
        upper_lower_split.add(lower_frame)

        # Create a vertical split in the upper section
        split_frame = tk.PanedWindow(lower_frame, orient=tk.HORIZONTAL)
        split_frame.pack(fill=tk.X, expand=True)

        # Left frame for controls
        left_frame = tk.Frame(split_frame,width=700)
        left_frame.pack_propagate(False)
        left_frame.pack(fill=tk.X, expand=True)
        split_frame.add(left_frame)

        self.stop_monitoring = False
        # Add info terminal components to left frame
        self.info_terminal = self.create_terminal_Function(left_frame, "Info")
        self.monitor_info_thread = threading.Thread(
            target=self.monitor_logs_Function, 
            args=("d:/Trade/Bot/TradingBot101/logs/info.log", self.info_terminal),
            daemon=True
        )
        self.monitor_info_thread.start()

        # Right frame for data
        right_frame = tk.Frame(split_frame)
        right_frame.pack(fill=tk.X, expand=True)
        split_frame.add(right_frame)

        #add command section to right frame 
        self.error_terminal = self.create_terminal_Function(right_frame, "Error")
        self.monitor_error_thread = threading.Thread(
            target=self.monitor_logs_Function, 
            args=("d:/Trade/Bot/TradingBot101/logs/error.log", self.error_terminal),
            daemon=True
        )
        self.monitor_error_thread.start()

    def poistion_manager_tab_Function(self, parent: ttk.Frame):
        # Create a horizontal split for the upper and lower sections of the bot_frame
        split = tk.PanedWindow(parent, orient=tk.VERTICAL)
        split.pack(fill=tk.X, expand=True)

        # Upper section for the vertical split (same as before)
        upper_frame = tk.Frame(split, height=600)
        upper_frame.pack_propagate(False)  # Prevent the frame from shrinking
        split.add(upper_frame)
        self.create_positions_table_Function(upper_frame)

        # Lower section 
        lower_frame = tk.Frame(split, bg="lightgrey")
        split.add(lower_frame)

        # Terminal output at the bottom of the lower frame
        tk.Label(
            lower_frame, 
            text="Some buttons to manage positions manualy"
        ).pack()

    def history_trades_tab_Function(self, parent: ttk.Frame):
        # Create a horizontal split for the upper and lower sections of the bot_frame
        split = tk.PanedWindow(parent, orient=tk.VERTICAL)
        split.pack(fill=tk.X, expand=True)

        # Upper section for the vertical split (same as before)
        upper_frame = tk.Frame(split, height=600)
        upper_frame.pack_propagate(False)  # Prevent the frame from shrinking
        split.add(upper_frame)
        self.create_dashboard_Function(upper_frame)

        # Lower section 
        lower_frame = tk.Frame(split, bg="lightgrey")
        split.add(lower_frame)

        # Terminal output at the bottom of the lower frame
        tk.Label(
            lower_frame, 
            text="Some graphs to show the result"
        ).pack()

    def create_control_panel_Function(self, parent_frame:tk.Frame):
        """Create control panel with start/stop buttons and status indicator"""
        controls_frame = tk.LabelFrame(parent_frame, text="Bot Controls", padx=10, pady=10, font=("Arial", 11))
        controls_frame.pack(fill=tk.X, pady=10)
        
        # Button frame with grid layout
        button_frame = tk.Frame(controls_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Start button
        self.start_button = tk.Button(
            button_frame,
            text="Start Bot",
            command=self.start_bot_Function,
            font=("Arial", 9),
            bg="#002500",
            fg="white",
            width=12,
            height=1,
            relief="raised",
            cursor="hand2"
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Stop button
        self.stop_button = tk.Button(
            button_frame,
            text="Stop Bot",
            command=self.stop_bot_Function,
            font=("Arial", 9),
            bg="#660000",
            fg="white",
            width=12,
            height=1,
            state=tk.DISABLED,
            relief="flat",
            cursor="arrow"
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Restart button
        restart_button = tk.Button(
            button_frame,
            text="Restart Bot",
            command=self.restart_bot_Function,
            font=("Arial", 9),
            bg="#CC5801",
            fg="white",
            width=12,
            height=1,
            state=tk.DISABLED,
            relief="flat"
        )
        restart_button.grid(row=1, column=0, padx=5, pady=5)
        self.restart_button = restart_button
        
        # Settings button
        self.settings_button = tk.Button(
            button_frame,
            text="Bot Settings",
            command=self.show_config_Function,
            font=("Arial", 9),
            bg="#001540",
            fg="white",
            width=12,
            height=1,
            relief="raised",
            cursor="hand2"
        )
        self.settings_button.grid(row=1, column=1, padx=5, pady=5)
        
        # Status indicator
        tk.Label(
            button_frame,
            text="Bot Status:",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        self.status_var = tk.StringVar(value="Not Running")
        self.status_indicator = tk.Label(
            button_frame,
            textvariable=self.status_var,
            font=("Arial", 11),
            fg="#e74c3c"
        )
        self.status_indicator.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Run time indicator
        tk.Label(
            button_frame,
            text="Run Time:",
            font=("Arial", 11, "bold")
        ).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        self.runtime_var = tk.StringVar(value="00:00:00")
        runtime_label = tk.Label(
            button_frame,
            textvariable=self.runtime_var,
            font=("Arial", 11)
        )
        runtime_label.grid(row=1, column=3, padx=5, pady=5, sticky="w")

    def create_terminal_Function(self, parent_frame: tk.Frame, type_of_terminal:typing.Literal["Info", "Error"]) -> ScrolledText:
        """Creates the terminal for bot output"""
        color = "#660000" if type_of_terminal == "Error" else "#002500"
        terminal_frame = tk.LabelFrame(parent_frame, text=f" {type_of_terminal} Terminal ", padx=5, pady=5, font=("Arial", 11), fg=color)
        terminal_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Terminal text widget
        terminal = scrolledtext.ScrolledText(
            terminal_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#f8f8f8",
            wrap=tk.WORD
        )

        # Add terminal control buttons
        terminal_controls = tk.Frame(terminal_frame)
        terminal_controls.pack(fill=tk.X)
        
        clear_button = tk.Button(
            terminal_controls,
            text="Clear Terminal",
            command=lambda: self.clear_terminal_Function(terminal),
            font=("Arial", 9)
        )
        clear_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = tk.Checkbutton(
            terminal_controls,
            text="Auto-scroll",
            variable= auto_scroll_var,
            font=("Arial", 9)
        )
        auto_scroll_cb.pack(side=tk.RIGHT, padx=5, pady=2)

        # Store the auto-scroll variable with the terminal
        terminal.auto_scroll_var = auto_scroll_var # type: ignore
        
        terminal.pack(fill=tk.BOTH, expand=True)
        terminal.config(state=tk.DISABLED)

        return terminal

    def clear_terminal_Function(self, terminal: ScrolledText):
        """Clear the contents of the terminal"""
        terminal.config(state=tk.NORMAL)
        terminal.delete(1.0, tk.END)
        terminal.config(state=tk.DISABLED)

    def restart_bot_Function(self):
        """Restart the trading bot"""
        if parameters.bot_running:
            self.stop_bot_Function()
            # Wait a moment for the bot to fully stop
            self.root.after(1000, self.start_bot_Function)
        else:
            self.start_bot_Function()

    def start_bot_Function(self):
        """Start the trading bot and capture its output"""
        if not parameters.bot_running:
            self.append_to_terminal_Function(self.info_terminal,"Starting trading bot...", False)
            self.status_var.set("Starting...")
            self.status_indicator.config(fg="#f39c12")  # Yellow for starting
            self.start_time = time.time()
            
            # Run the bot in a separate thread
            self.bot_thread = threading.Thread(target=self.run_bot_Function)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            # Update button states
            self.start_button.config(state=tk.DISABLED, cursor="arrow", relief="flat")
            self.stop_button.config(state=tk.NORMAL, cursor="hand2", relief="raised")
            self.settings_button.config(state=tk.DISABLED, cursor="arrow", relief="flat")
            self.restart_button.config(state=tk.NORMAL, cursor="hand2", relief="raised")
            self.append_to_terminal_Function(self.info_terminal,"Started Trading bot!", False)
    
    def run_bot_Function(self):
        """Run the main_backend.py script and capture its output in real-time"""
        try:
            # Ensure the script exists
            script_path = "d:/Trade/Bot/TradingBot101/main_backend.py"
            if not os.path.exists(script_path):
                self.append_to_terminal_Function(self.info_terminal,f"Error: Script not found at {script_path}\n")
                self.status_var.set("Error")
                self.status_indicator.config(fg="#e74c3c")  # Red for error
                self.reset_buttons_Function()
                return
            
            # Create the directory structure if it doesn't exist
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            
            # Start the process with Python to ensure colors are preserved
            self.bot_process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1, # bufsize=1 ensures line buffering
                universal_newlines=True, # The universal_newlines=True ensures that output is returned as strings
                creationflags=subprocess.CREATE_NO_WINDOW  # This prevents a console window from appearing
            )
            
            parameters.bot_running = True
            self.status_var.set("Running")
            self.status_indicator.config(fg="#27ae60")  # Green for running
            
            # # Start a separate thread to read the output
            self.update_runtime_thread = threading.Thread(target=self.update_runtime_Function)
            self.update_runtime_thread.daemon = True
            self.update_runtime_thread.start()
            
        except Exception as e:
            self.append_to_terminal_Function(self.error_terminal,f"Error: {str(e)}\n")
            self.status_var.set("Error")
            self.status_indicator.config(fg="#e74c3c")  # Red for error
            self.reset_buttons_Function()
            parameters.bot_running = False

    def stop_bot_Function(self):
        """Stop the running bot"""
        if parameters.bot_running and self.bot_process:
            self.append_to_terminal_Function(terminal=self.info_terminal,text="Stopping trading bot...\n", timestamp=False)
            
            # Set the flag first to prevent further processing
            parameters.bot_running = False
            
            # Terminate the process
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
            
            self.status_var.set("Stopped")
            self.status_indicator.config(fg="#e74c3c")  # Red for stopped
            self.reset_buttons_Function()

            # Update button states
            self.stop_button.config(state=tk.DISABLED, cursor="arrow", relief="flat")
            self.restart_button.config(state=tk.DISABLED, cursor="arrow", relief="flat")
            self.start_button.config(state=tk.NORMAL, cursor="hand2", relief="raised")
            self.settings_button.config(state=tk.NORMAL, cursor="hand2", relief="raised")


            self.update_runtime_thread.join()
            self.append_to_terminal_Function(terminal=self.info_terminal,text="Bot Stopped\n", timestamp=False)

    def reset_buttons_Function(self):
        """Reset buttons to their default state"""
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
        
        # Reset the process reference
        self.bot_process = None

    def append_to_terminal_Function(self, terminal: ScrolledText, text: str, timestamp: bool = True):
        """Append text to the terminal with optional timestamp"""
        terminal.config(state=tk.NORMAL)
        
        if timestamp:
            current_time = datetime.now().strftime("%H:%M:%S")
            text = f"[{current_time}] {text}"
        
        terminal.insert(tk.END, text + "\n")
        
        # Auto-scroll if enabled
        if terminal.auto_scroll_var.get(): # type: ignore
            terminal.see(tk.END)
        
        terminal.config(state=tk.DISABLED)
    
    def monitor_logs_Function(self, log_file_path: str, terminal: ScrolledText):
        """Monitor a log file for changes and update the specified terminal"""
        # Make sure the log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Create the file if it doesn't exist
        if not os.path.exists(log_file_path):
            open(log_file_path, 'a').close()
            
        # Remember the last position we read from
        file_position = 0
        
        while not self.stop_monitoring:
            try:
                # Check if file exists and open it
                if os.path.exists(log_file_path):
                    with open(log_file_path, 'r') as file:
                        # Go to the last position we read
                        file.seek(file_position)
                        
                        # Read new content
                        new_content = file.read()
                        
                        # Update position for next time
                        file_position = file.tell()
                        
                        # If there's new content, update the terminal
                        if new_content:
                            # Remove trailing newlines to avoid extra blank lines
                            new_content = new_content.rstrip()
                            if new_content:
                                # Update in the main thread to avoid tkinter threading issues
                                self.root.after(0, lambda t=terminal, c=new_content: 
                                            self.append_to_terminal_Function(t, c, timestamp=False))
            except Exception as e:
                # If there's an error reading the log, show it in the terminal
                self.root.after(0, lambda t=terminal, e=str(e): 
                            self.append_to_terminal_Function(t, f"Error monitoring log: {e}"))
            
            # Wait before checking again (adjust as needed)
            time.sleep(0.5)

    def update_runtime_Function(self):
        """Update the runtime display"""
        if parameters.bot_running:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            self.runtime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Schedule the next update
            self.root.after(1000, self.update_runtime_Function)
    
    def create_positions_table_Function(self, parent_frame):
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
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add right-click menu for position management
        self.create_position_context_menu_Function()

    def create_position_context_menu_Function(self):
        """Create a context menu for position management"""
        self.position_menu = tk.Menu(self.positions_tree, tearoff=0)
        self.position_menu.add_command(label="Close Position", command=self.close_selected_position_Function)
        self.position_menu.add_command(label="Modify Position", command=self.modify_selected_position_Function)
        self.position_menu.add_command(label="Position Details", command=self.show_position_details_Function)
        
        # Bind right-click event
        self.positions_tree.bind("<Button-3>", self.show_position_menu_Function)

    def show_position_menu_Function(self, event):
        """Show the position context menu on right-click"""
        # Select row under mouse
        iid = self.positions_tree.identify_row(event.y)
        if iid:
            self.positions_tree.selection_set(iid)
            self.position_menu.post(event.x_root, event.y_root)

    def close_selected_position_Function(self):
        """Close the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        position_id = self.positions_tree.item(selection[0], "values")[0]
        self.send_command_Function(f"close_position {position_id}")

    def modify_selected_position_Function(self):
        """Open dialog to modify the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        # position_id = self.positions_tree.item(selection[0], "values")[0]
        # Open a dialog to modify position parameters
        # ...

    def show_position_details_Function(self):
        """Show detailed information about the selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        position_id = self.positions_tree.item(selection[0], "values")[0]
        self.send_command_Function(f"position_details {position_id}")
  
    def update_ui_with_status_Function(self, status_data):
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
                    self.append_to_terminal_Function(self.info_terminal,f"[BOT] {status['message']}\n")
                    
        except Exception as e:
            self.append_to_terminal_Function(self.error_terminal,f"Error updating UI: {str(e)}\n")

    def create_command_interface_Function(self, parent_frame):
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
            command=self.send_command_Function, 
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
                command=lambda c=cmd: self.send_command_Function(c),
                font=("Arial", 10),
                bg="#ecf0f1",
                width=15
            )
            cmd_btn.grid(row=0, column=i+1, padx=5, pady=5)

    def send_command_Function(self, command=None):
        """Send a command to the running bot process"""
        if not parameters.bot_running or not self.bot_process:
            messagebox.showerror("Error", "Bot is not running")
            return
        
        # Get the command from entry or parameter
        cmd = command if command else self.cmd_var.get()
        if not cmd:
            return
        
        # Log the command
        self.append_to_terminal_Function(self.info_terminal,f"\n> Executing command: {cmd}\n")
        
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
            self.append_to_terminal_Function(self.info_terminal, f"Error sending command: {str(e)}\n", False)

    def create_dashboard_Function(self, parent_frame):
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
        
    def on_escape_Function(self,event):
        """Handle ESC key press - show confirmation dialog"""
        self.confirm_exit_Function()
    
    def show_loading_window_Function(self, function_to_run, *args, title="Processing", message="Please wait...", **kwargs):
        """
        Shows a loading window while running a function
        
        Args:
            function_to_run: The function to execute while showing the loading window
            *args: Arguments to pass to the function
            title: Title for the loading window
            message: Message to display in the window
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
        """
        # Create loading window
        loading_window = tk.Toplevel(self.root)
        loading_window.title(title)
        loading_window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Set window properties
        loading_window.geometry("400x150")
        loading_window.resizable(False, False)
        loading_window.configure(bg="white", cursor="watch")
        self.root.config(cursor="watch")  # "watch" makes it look like a loading cursor
        
        # Center the window relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        loading_window.geometry(f"+{x}+{y}")
        
        # Make it modal-like
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        # Add content
        frame = tk.Frame(loading_window, bg="white", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add message
        tk.Label(
            frame, 
            text=message, 
            font=("Arial", 12), 
            bg="white"
        ).pack(pady=(0, 15))
        
        # Add progress bar
        progress = ttk.Progressbar(frame, mode="indeterminate", length=350)
        progress.pack(pady=5)
        progress.start(10)  # Start animation
        
        # Variable to store the result
        result_container = []
        
        # Force update the UI before continuing
        loading_window.update()
        
        # Function to run in thread
        def run_function_in_thread():
            try:
                # Call the actual function
                result = function_to_run(*args, **kwargs)
                result_container.append(result)
            except Exception as e:
                # Store the exception
                result_container.append(e)
            finally:
                self.root.after(0, lambda: reset_cursor_and_close())

        # Reset cursor and close window
        def reset_cursor_and_close():
            self.root.config(cursor="arrow")  # Reset cursor to normal
            loading_window.destroy()
            return
        
        # Start the thread
        thread = threading.Thread(target=run_function_in_thread)
        thread.daemon = True
        thread.start()
        
        # Wait for the loading window to be destroyed (blocks until the window is closed)
        self.root.wait_window(loading_window)
        
        # Check if we got an exception
        if result_container and isinstance(result_container[0], Exception):
            raise result_container[0]
        
        # Return the result if there is one
        return result_container[0] if result_container else None

    def confirm_exit_Function(self):
        """Show a confirmation dialog and exit if user confirms"""
        if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit?"):
            # Define the closing function
            def close_app():
                if hasattr(self, 'monitor_error_thread'):
                    if self.monitor_error_thread.is_alive():
                        self.monitor_error_thread.join(timeout=0.6)
                if hasattr(self, 'monitor_info_thread'):
                    if self.monitor_info_thread.is_alive():
                        self.monitor_info_thread.join(timeout=0.6)
                # Any other cleanup needed
                
            # Show the loading overlay while running the close function
            self.show_loading_window_Function(close_app, title="Closing", message="Stoping necessary functions...")

            if hasattr(self,'bot_process'):
                self.show_loading_window_Function(self.stop_bot_Function,title="Closing", message="Stopping Bot...")

            # After cleanup is done, destroy the window
            self.root.destroy()

    def toggle_window_size_Function(self,event):
        """Toggle between maximized and normal window state"""
        self.Is_fullscreen = not self.Is_fullscreen
        root.attributes('-fullscreen', self.Is_fullscreen)

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUI_class(root)
    root.attributes('-fullscreen', app.Is_fullscreen)
    root.bind('<Alt-Return>', app.toggle_window_size_Function)
    root.bind('<Escape>', app.on_escape_Function)
    root.protocol("WM_DELETE_WINDOW", app.confirm_exit_Function)
    root.mainloop()