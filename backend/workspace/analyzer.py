def count_vowels(input_string: str) -> int:
    # Convert the input string to lowercase to ensure the function is case-insensitive
    input_string = input_string.lower()
    # Define the set of vowels to look for
    vowels = {'a', 'e', 'i', 'o', 'u'}
    # Use a generator expression to count the vowels in the input string
    count = sum(1 for char in input_string if char in vowels)
    return count
