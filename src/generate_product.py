#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv
from openai import OpenAI

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate product data from preprocessed markdown."
    )
    parser.add_argument(
        "--mdfile",
        help="Path to the preprocessed markdown file. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--output",
        choices=["json", "swell"],
        help="Output destination. If omitted, outputs result to stdout.",
    )
    return parser.parse_args()


def load_schema(schema_path="schema_compiled.json"):
    """Load the JSON schema from a file."""
    try:
        with open(os.path.join(DATA_DIR, schema_path), "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        sys.exit(f"Error: Schema file '{schema_path}' not found.")
    except json.JSONDecodeError:
        sys.exit(f"Error: Invalid JSON in schema file '{schema_path}'.")


def load_env_variables():
    """Load environment variables from the .env file."""
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    store_id = os.getenv("store-id")
    store_key = os.getenv("store-key")

    if not openai_api_key:
        sys.exit("Error: 'OPENAI_API_KEY' not found in .env file.")

    return {
        "openai_api_key": openai_api_key,
        "store_id": store_id,
        "store_key": store_key,
    }


def read_markdown_content(mdfile):
    """Read markdown content from a file or stdin."""
    if mdfile:
        try:
            with open(mdfile, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            sys.exit(f"Error reading markdown file '{mdfile}': {e}")
    else:
        return sys.stdin.read()


def process_data_with_openai(content, schema, openai_api_key):
    """Use OpenAI API to generate structured product data from markdown content."""
    client = OpenAI(api_key=openai_api_key)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert at structured data extraction. "
                "Read the user input and generate a valid product for the catalog "
                "according to the given structure."
            ),
        },
        {"role": "user", "content": content},
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "product_response",
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        message = completion.choices[0].message

        if getattr(message, "refusal", None):
            print(f"Model refused to respond: {message.refusal}", file=sys.stderr)
            sys.exit("Error: Model refused to respond.")
        else:
            return json.loads(message.content)
    except Exception as e:
        sys.exit(f"OpenAI API error: {e}")


def remove_null_properties(data):
    """Recursively remove null properties from the data."""
    if isinstance(data, dict):
        return {
            key: remove_null_properties(value)
            for key, value in data.items()
            if value is not None
        }
    elif isinstance(data, list):
        return [remove_null_properties(item) for item in data if item is not None]
    else:
        return data


def handle_output(result, output_type, store_id=None, store_key=None):
    """Output the result to a file, Swell API, or stdout."""
    result = remove_null_properties(result)

    if output_type == "json":
        try:
            with open(os.path.join(DATA_DIR, "output.json"), "w", encoding="utf-8") as file:
                json.dump(result, file, ensure_ascii=False, indent=4)
            print("Output successfully written to 'output.json'", file=sys.stderr)
        except Exception as e:
            sys.exit(f"Error writing to 'output.json': {e}")
    elif output_type == "swell":
        if not store_id or not store_key:
            sys.exit("Error: 'store-id' or 'store-key' not found in .env file.")

        headers = {
            "Authorization": f"Bearer {store_id}:{store_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                "https://api.swell.store/products", headers=headers, json=result
            )
            response.raise_for_status()
            print("Data successfully submitted to Swell API.", file=sys.stderr)
        except requests.RequestException as e:
            sys.exit(f"Error submitting to Swell API: {e}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=4))


def main(args=None):
    if args is None:
        args = parse_arguments()  # Default to command-line arguments if none provided
    else:
        pass
    
    env_vars = load_env_variables()
    schema = load_schema()

    content = read_markdown_content(args.mdfile)
    content = content.strip()

    if not content:
        print(f"Error: The makdown input is empty.", file=sys.stderr)
        sys.exit(1)

    result = process_data_with_openai(content, schema, env_vars["openai_api_key"])

    handle_output(
        result,
        args.output,
        store_id=env_vars.get("store_id"),
        store_key=env_vars.get("store_key"),
    )


if __name__ == "__main__":
    main()