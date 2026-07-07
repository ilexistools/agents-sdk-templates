from collections import Counter

def count_words(text: str) -> dict:
    """
    Count the number of words and characters in a given text.

    Args:
        text: The input text to analyze.

    Returns:
        A dictionary with word_count and character_count.
    """
    words = text.split()
    word_count = len(words)
    character_count = sum(len(word) for word in words)
    return {"word_count": word_count, "character_count": character_count}

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in a given text by replacing multiple spaces with a single space.

    Args:
        text: The input text with irregular whitespace.

    Returns:
        The same text with normalized whitespace.
    """
    return ' '.join(text.split())
