#!/usr/bin/env python3
import json
import re

def extract_json_fields(input_file, output_file=None):
    """
    Reads a malformed JSON file, extracts the key fields, and creates a new valid JSON.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Optional path to write the fixed JSON (if None, prints to console)
    """
    # Read the file content
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Extract the key fields using regex
    name_match = re.search(r'"name":\s*"([^"]+)"', content)
    description_match = re.search(r'"description":\s*"([^"]+)"', content)
    user_id_match = re.search(r'"user_id":\s*"([^"]+)"', content)
    
    # Extract the content field - this is trickier because it's a large text block
    # We'll look for the start of the content field and capture everything until the next field
    content_match = re.search(r'"content":\s*"(.*?)(?:"\s*,\s*"user_id"|"\s*})', content, re.DOTALL)
    
    # Create a new JSON object with the extracted fields
    new_json = {
        "name": name_match.group(1) if name_match else "Revenued Info Agent Test",
        "description": description_match.group(1) if description_match else "Test Revenued Info Agent",
        "user_id": user_id_match.group(1) if user_id_match else "jason@amotivv.com"
    }
    
    # Add the content field if we found it
    if content_match:
        # Clean up the content field
        content_text = content_match.group(1)
        # Replace escaped quotes
        content_text = content_text.replace('\\"', '"')
        # Replace escaped single quotes
        content_text = content_text.replace("\\'", "'")
        # Replace newlines with actual newlines
        content_text = content_text.replace("\\n", "\n")
        # Remove any control characters
        content_text = ''.join(ch if ord(ch) >= 32 else ' ' for ch in content_text)
        
        new_json["content"] = content_text
    else:
        # If we couldn't extract the content, create a minimal version
        new_json["content"] = "REVENUED AI ASSISTANT SYSTEM INSTRUCTION"
    
    # Output the new JSON
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(new_json, f, indent=2)
        print(f"Fixed JSON written to {output_file}")
    else:
        # Pretty print the JSON
        print(json.dumps(new_json, indent=2))
    
    return True

def manual_json_creation(input_file, output_file=None):
    """
    Creates a valid JSON file with the key fields from the input file.
    This is a more direct approach when regex extraction fails.
    """
    # Create a new JSON object with the known fields
    new_json = {
        "name": "Revenued Info Agent Test",
        "description": "Test Revenued Info Agent",
        "user_id": "jason@amotivv.com"
    }
    
    # Read the file content to extract the content field
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find the start of the content field
    content_start = content.find('"content": "') + 12
    
    # Extract everything after the content field start
    # We'll clean it up manually
    content_text = content[content_start:]
    
    # Find the end of the content field (before the user_id field or the end of the JSON)
    end_marker1 = '", "user_id"'
    end_marker2 = '"}'
    
    end_pos1 = content_text.find(end_marker1)
    end_pos2 = content_text.find(end_marker2)
    
    if end_pos1 != -1:
        content_text = content_text[:end_pos1]
    elif end_pos2 != -1:
        content_text = content_text[:end_pos2]
    
    # Clean up the content text
    content_text = content_text.replace('\\"', '"')
    content_text = content_text.replace("\\'", "'")
    
    # Add the cleaned content to the JSON
    new_json["content"] = content_text
    
    # Output the new JSON
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(new_json, f, indent=2)
        print(f"Fixed JSON written to {output_file}")
    else:
        # Pretty print the JSON
        print(json.dumps(new_json, indent=2))
    
    return True

if __name__ == "__main__":
    # Try both approaches
    try:
        # First try the regex extraction approach
        success = extract_json_fields("prompt.json", "fixed_prompt.json")
        if not success:
            # If that fails, try the manual approach
            manual_json_creation("prompt.json", "fixed_prompt.json")
    except Exception as e:
        print(f"Error: {e}")
        # Fall back to the manual approach
        manual_json_creation("prompt.json", "fixed_prompt.json")
