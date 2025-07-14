def is_valid_email(email: str) -> bool:
    # Check if there is exactly one '@' symbol
    if email.count('@') != 1:
        return False
    
    at_index = email.index('@')
    # Ensure there is at least one '.' following the '@'
    if '.' not in email[at_index:]:
        return False
    
    return True