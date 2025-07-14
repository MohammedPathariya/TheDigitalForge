def is_valid_email(email: str) -> bool:
    """
    Validate the format of an email address.

    Parameters:
    email (str): The email address to validate.

    Returns:
    bool: True if the email format is valid, otherwise False.
    """
    if email.count('@') != 1:
        return False
    
    at_index = email.index('@')
    if '.' not in email[at_index:]:
        return False
    
    return True