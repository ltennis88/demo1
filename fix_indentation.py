#!/usr/bin/env python3

with open('app.py', 'r') as file:
    lines = file.readlines()

changes = [
    # Fix load_dummy_inquiries function (line 538)
    ('            return df', '        return df'),
    
    # Fix classification function try/except blocks
    ('        try:', '    try:'),
    ('            response = openai.ChatCompletion.create(', '        response = openai.ChatCompletion.create('),
    ('            output_cost = calculate_token_cost(output_tokens, "output")', '        output_cost = calculate_token_cost(output_tokens, "output")'),
    ('            total_cost = input_cost + output_cost', '        total_cost = input_cost + output_cost'),
    ('        except Exception as e:', '    except Exception as e:'),
    ('                return {', '        return {'),
    ('                    "inbound_route": "error",', '            "inbound_route": "error",'),
    
    # Fix else block in response generation
    ('            else:', '        else:'),
    
    # Fix expected indented block
    ('        latest_generation = st.session_state["token_usage"]["generations"][-1]', '            latest_generation = st.session_state["token_usage"]["generations"][-1]')
]

for old, new in changes:
    for i, line in enumerate(lines):
        if old in line:
            lines[i] = line.replace(old, new)

with open('app.py', 'w') as file:
    file.writelines(lines)

print("Fixed indentation errors in app.py") 