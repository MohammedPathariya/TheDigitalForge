def factorial(n):
    """
    Calculate the factorial of a non-negative integer n.
    :param n: Non-negative integer
    :return: Factorial of n
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative integers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
