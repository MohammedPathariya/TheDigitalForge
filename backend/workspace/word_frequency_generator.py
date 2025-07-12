def generate_word_frequency(text):
    # Normalize the text by lowering the case
    text = text.lower()
    # Split the text into words
    words = text.split()
    # Create a dictionary to hold the frequency of each word
    word_frequency = {}

    # Count the frequency of each word
    for word in words:
        # Only count words that are 'hello' or 'world'
        if word in ['hello', 'world']:
            if word in word_frequency:
                word_frequency[word] += 1
            else:
                word_frequency[word] = 1

    return word_frequency
