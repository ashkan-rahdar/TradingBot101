# Flag Class (`Flag.py`)

## Overview
The `Flag.py` script defines the `Flag` class, which represents a detected flag in the price data. It includes methods for initializing the flag, calculating its weight, and validating important data points (DPs).

## Workflow
1. **Initialization**:
   - Load configuration from `config.json`.
   - Define the `Flag` class with attributes for flag ID, type, high/low points, data within the flag, and important data points (FTC and EL).

2. **Methods**:
   - `__init__()`: Initializes a `Flag` object with the provided attributes.
   - `weight_of_flag()`: Calculates the weight of the flag based on its duration and configuration.
   - `validate_DP()`: Validates important data points within the flag.
   - `__repr__()`: Returns a string representation of the `Flag` object.

## Key Functions
- `__init__()`: Initializes a `Flag` object.
- `weight_of_flag()`: Calculates the weight of the flag.
- `validate_DP()`: Validates important data points.
- `__repr__()`: String representation of the `Flag` object.

## Next Steps
- Add methods to merge flags.
- Implement strategies for validating FTC and EL.