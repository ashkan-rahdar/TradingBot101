# Logger (`logger.py`)

## Overview
The `logger.py` script sets up logging for the trading bot, including rotating file handlers for different log levels.

## Workflow
1. **Logger Setup**:
   - Create rotating file handlers for info, warning, and error logs.
   - Set up a formatter for the log messages.
   - Add filters to separate log levels.
   - Create a logger and add the handlers.

## Key Functions
- `LogLevelFilter`: Custom filter for separating log levels.
- Logger setup: Configures the logger with handlers and formatters.

## Next Steps
- Add more detailed logging throughout the codebase.
- Implement log rotation and archival.