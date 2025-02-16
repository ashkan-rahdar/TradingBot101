# Main Script (`main.py`)

## Overview
The `main.py` script is the entry point of the trading bot. It orchestrates the entire process of fetching data, detecting flags, visualizing flags, and reacting to flags. It also handles emergency situations and user inputs.

## Workflow
1. **Initialization**:
   - Load configuration from `config.json`.
   - Set up emergency flag and event.

2. **Emergency Listener**:
   - Listens for user input to trigger emergency mode.
   - If the user types the emergency keyword, the bot enters emergency mode.

3. **Main Loop**:
   - Fetches data for the specified timeframes.
   - Detects flags using the `FlagDetector` class.
   - Saves detected flags to an Excel file.
   - Visualizes the flags if in development mode.
   - Reacts to the detected flags using the `main_reaction_detector` function.
   - Waits for a specified refresh time or until an emergency event is triggered.

4. **Emergency Handling**:
   - If an emergency is triggered, the bot performs emergency actions and logs the event.

## Key Functions
- `emergency_listener()`: Listens for user input to trigger emergency mode.
- `emergency_handler()`: Handles `Ctrl+C` to gracefully terminate the process.
- `main()`: The main function that runs the trading bot.

## Next Steps
- Add a `PositionManager` class to manage positions based on detected flags.