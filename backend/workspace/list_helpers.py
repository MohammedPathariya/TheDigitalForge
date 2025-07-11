def find_max(lst):
    """Returns the maximum value from a list."""
    if not lst:
        return None  # Handle empty list case
    max_value = lst[0]
    for num in lst:
        if num > max_value:
            max_value = num
    return max_value
