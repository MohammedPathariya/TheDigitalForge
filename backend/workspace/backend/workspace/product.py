def calculate_word_frequency(text):
    # Ensure the parameter is a string
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation using regular expression
    import re
    text = re.sub(r'[^\w\s]', '', text)

    # Split the text into words
    words = text.split()

    # Initialize an empty dictionary for word counts
    word_count = {}

    # Count occurrences of each word
    for word in words:
        if word.isalpha():  # Check if the word consists only of alphabetic characters
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1

    return word_count