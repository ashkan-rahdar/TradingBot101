import signal
import sys
import os
import curses  # For menu UI
import keyboard  # Detecting 'space' and blocking unwanted inputs

The_emergency_flag = False  # Global emergency flag
correct_password = "1234"   # Set your password

# 1️⃣ BLOCK INPUT UNTIL SPACE OR CTRL+C
def block_input():
    """Disable user input by redirecting stdin."""
    sys.stdin = open(os.devnull)

def allow_input():
    """Re-enable user input."""
    sys.stdin = sys.__stdin__

# 2️⃣ EMERGENCY HANDLER (CTRL + C)
def emergency_handler_Function(signum, frame):
    """Handle Ctrl + C and ask for password."""
    global The_emergency_flag

    allow_input()  # Enable typing for password
    print("\n🚨 Emergency Stop Requested! Enter Password to Confirm:")
    user_input = input("Password: ").strip()

    if user_input == correct_password:
        print("✅ Emergency stop confirmed!")
        The_emergency_flag = True
        sys.exit(1)
    else:
        print("❌ Incorrect password! Ignoring emergency stop.")
        block_input()  # Block input again

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, emergency_handler_Function)

# 3️⃣ MENU SYSTEM (TRIGGERED ON SPACE)
def menu(stdscr):
    """Curses-based menu for selecting options using arrow keys."""
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    options = ["Option 1: Start Trading", "Option 2: View Logs", "Option 3: Exit"]
    current_selection = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 5, "🔽 Use Arrow Keys to Navigate | Press ENTER to Select", curses.A_BOLD)

        for i, option in enumerate(options):
            if i == current_selection:
                stdscr.addstr(i + 2, 10, f"> {option}", curses.A_REVERSE)  # Highlight selection
            else:
                stdscr.addstr(i + 2, 12, option)

        key = stdscr.getch()

        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
            current_selection += 1
        elif key == 10:  # ENTER key
            return options[current_selection]  # Return selected option

# 4️⃣ LISTEN FOR SPACE TO SHOW MENU
def listen_for_space():
    """Wait for Space key, then show the selection menu."""
    print("🔒 Press SPACE to see options, or CTRL+C to exit.")

    while True:
        keyboard.wait("space")  # Blocks until space is pressed
        allow_input()  # Temporarily allow input for menu
        selected_option = curses.wrapper(menu)  # Show menu
        print(f"✅ You selected: {selected_option}")
        block_input()  # Block input again

# Start by blocking input
block_input()

# Run listener for SPACE in a separate thread
import threading
threading.Thread(target=listen_for_space, daemon=True).start()

# Main execution loop
def main_loop():
    while not The_emergency_flag:
        print("🚀 Running... Press SPACE for options, or CTRL+C to stop.")
        keyboard.wait("esc")  # Just to hold execution (won't trigger anything)

main_loop()
