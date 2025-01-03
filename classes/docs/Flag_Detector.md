# Flag Detector (`Flag_Detector.py`)

## Overview
The `Flag_Detector.py` script defines the `FlagDetector` class, which is responsible for detecting flags in the price data. Flags are patterns that indicate potential trading opportunities based on price action.

## Workflow
1. **Initialization**:
   - Load configuration from `config.json`.
   - Define the `FlagDetector` class with attributes for the dataset and detected flags.

2. **Methods**:
   - `__init__()`: Initializes a `FlagDetector` object with the provided dataset.
   - `run_detection()`: Runs the flag detection algorithm on the dataset.
   - `detect_flag()`: Detects individual flags within the dataset.
   - `validate_flag()`: Validates the detected flags to ensure they meet certain criteria.
   - `__repr__()`: Returns a string representation of the `FlagDetector` object.

## Key Functions
- `__init__()`: Initializes a `FlagDetector` object.
- `run_detection()`: Runs the flag detection algorithm.
- `detect_flag()`: Detects individual flags.
- `validate_flag()`: Validates the detected flags.
- `__repr__()`: String representation of the `FlagDetector` object.

## Algorithm
1. **Initialization**:
   - Load the dataset and configuration.
   - Initialize an empty list to store detected flags.

2. **Run Detection**:
   - Iterate through the dataset to identify potential flags.
   - For each potential flag, call the `detect_flag()` method to determine if it meets the criteria for a flag.

3. **Detect Flag**:
   - Analyze the price action within the dataset to identify patterns that match the criteria for a flag.
   - Calculate the high and low points, duration, and other attributes of the flag.

4. **Validate Flag**:
   - Ensure the detected flag meets the criteria defined in the configuration.
   - Adjust the flag attributes if necessary to ensure they are valid.

## Next Steps
- Optimize the flag detection algorithm for performance.
- Add more detailed logging and error handling.
- Implement strategies for merging and validating multiple flags.