import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.logger import logger

async def run_with_retries(coroutine_func, *args, retries=3, delay=5):
    """
    Run a coroutine with retries in case of errors.
    """
    for attempt in range(retries):
        try:
            return await coroutine_func(*args)
        except Exception as e:
            logger.error(f"Error in {coroutine_func.__name__} on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying {coroutine_func.__name__} in {delay} seconds...")
                await asyncio.sleep(delay)
    logger.critical(f"Failed to execute {coroutine_func.__name__} after {retries} attempts.")
    raise RuntimeError(f"{coroutine_func.__name__} failed after retries.")