

def extract_joke(json: dict) -> str:
    return f"{json['setup']}\n{json['punchline']}"
