def get_greeting(name: str) -> str:
    if name == 'Admin':
        return 'Welcome, Admin!'
    else:
        return f'Hello, {name}!'