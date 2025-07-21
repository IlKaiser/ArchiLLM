import json

def single_quote_to_double(str_in) -> str:
    """
    A function to parse a string and convert it into a valid JSON format.
    It replaces single quotes with double quotes
    """
    # Replace single quotes with double quotes except when they are inside double quotes.
    opend = False
    str_out = ""
    for c in str_in:
        if c != "'":
            if c == '"' and not opend:
                opend = True
            elif c == '"' and opend:
                opend = False
            str_out += c
        else:
            if opend:
                str_out += c
            else:
                str_out += '"'
    
  
    
    return str_out

def to_dict(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__))
