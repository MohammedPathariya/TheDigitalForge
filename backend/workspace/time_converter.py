def minutes_to_seconds(minutes: int) -> int:
    if minutes < 0:
        raise ValueError("Input must be a non-negative integer.")
    return minutes * 60
