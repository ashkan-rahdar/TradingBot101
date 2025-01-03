# Fetching Data (`fetching_data.py`)

## Overview
The `fetching_data.py` script is responsible for initializing MetaTrader 5, logging in, and fetching historical data for specified timeframes.

## Workflow
1. **Initialization**:
   - Load configuration from `config.json`.
   - Map timeframes from configuration to MetaTrader 5 timeframes.

2. **Functions**:
   - `initialize_mt5()`: Initializes MetaTrader 5.
   - `login_mt5()`: Logs into MetaTrader 5 using credentials from the configuration.
   - `fetch_data()`: Fetches historical data for specified timeframes.
   - `main_fetching_data()`: Orchestrates the initialization, login, and data fetching process.

## Key Functions
- `initialize_mt5()`: Initializes MetaTrader 5.
- `login_mt5()`: Logs into MetaTrader 5.
- `fetch_data()`: Fetches historical data for specified timeframes.
- `main_fetching_data()`: Main function to fetch data.

## Next Steps
- Ensure data fetching handles multiple symbols.
- Add error handling and retries for network issues.