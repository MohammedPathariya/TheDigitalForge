def calculate_factorial(n: int) -> int:
    # Check if n is less than 0
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    
    # Return 1 for factorial of 0
    if n == 0:
        return 1
    
    # Calculate factorial iteratively for positive integers
    result = 1
    for i in range(1, n + 1):
        result *= i
    
    return result