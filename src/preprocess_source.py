#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
from io import BytesIO

import requests
import tiktoken
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PyPDF2 import PdfReader

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

class InputDataError(Exception):
    pass

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Preprocess unstructured data into markdown format."
    )
    parser.add_argument(
        "--input-uri",
        help="URI of the input data (file or URL). If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--input-type",
        required=True,
        choices=["pdf", "text", "webpage"],
        help="Type of the input data.",
    )
    parser.add_argument(
        "--output-file",
        help="Output destination in data folder (e.g., 'batch_01/file.md'). If omitted, outputs markdown to stdout.",
    )
    return parser.parse_args()


def load_env_variables():
    load_dotenv()
    jina_key = os.getenv("jina-key")
    if not jina_key:
        sys.exit("Error: 'jina-key' not found in .env file.")
    return jina_key


def calculate_tokens(text):
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    print(f"Number of tokens in input text: {num_tokens}", file=sys.stderr)
    return num_tokens


def read_input_data(input_uri):
    """Read data from stdin or from the specified input URI."""
    if input_uri:
        if input_uri.startswith("file://"):
            file_path = input_uri[7:]
            if not os.path.exists(file_path):
                sys.exit(f"Error: File '{file_path}' does not exist.")
            with open(file_path, "rb") as file:
                return file.read()
        elif input_uri.startswith(("http://", "https://")):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.google.com/',
                }
                response = requests.get(input_uri, headers=headers, timeout=10)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                raise InputDataError(f"Error fetching URL '{input_uri}': {e}") from e
        else:
            raise InputDataError(
                "Error: Invalid input-uri scheme. Must start with 'file://', 'http://', or 'https://'."
            )
    else:
        return sys.stdin.buffer.read()


def process_pdf(data, is_remote=False, jina_key=None, input_uri=None):
    """Extract text from a PDF file."""
    if is_remote:
        # Use Jina AI for remote PDF processing
        pdf_base64 = base64.b64encode(data).decode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-With-Generated-Alt": "true",
            "Authorization": f"Bearer {jina_key}",
        }
        payload = {"url": input_uri, "pdf": pdf_base64}
        try:
            response = requests.post("https://r.jina.ai/", headers=headers, json=payload)
            response.raise_for_status()
            return response.text  # Assuming markdown text is returned
        except requests.RequestException as e:
            sys.exit(f"Error processing PDF with Jina AI: {e}")
    else:
        # Local PDF processing using PyPDF2
        try:
            reader = PdfReader(BytesIO(data))
            text = "".join(page.extract_text() for page in reader.pages)
            return text
        except Exception as e:
            sys.exit(f"Error reading PDF data: {e}")


def process_webpage(data, is_remote=False, jina_key=None, input_uri=None):
    """Extract text from a webpage."""
    if is_remote:
        # Use Jina AI for remote webpage processing
        headers = {
            "Content-Type": "application/json",
            "X-With-Generated-Alt": "true",
            "Authorization": f"Bearer {jina_key}",
        }
        payload = {"url": input_uri}
        try:
            response = requests.post("https://r.jina.ai/", headers=headers, json=payload)
            response.raise_for_status()
            return response.text  # Assuming markdown text is returned
        except requests.RequestException as e:
            sys.exit(f"Error processing webpage with Jina AI: {e}")
    else:
        # Local webpage processing using BeautifulSoup
        soup = BeautifulSoup(data, "html.parser")
        text = soup.get_text(separator="\n")
        return text


def process_text(data):
    """Process plain text data."""
    return data.decode("utf-8")


def process_input_data(input_type, data, is_remote=False, jina_key=None, input_uri=None):
    """Process input data based on the input type."""
    if input_type == "pdf":
        return process_pdf(data, is_remote=is_remote, jina_key=jina_key, input_uri=input_uri)
    elif input_type == "webpage":
        return process_webpage(data, is_remote=is_remote, jina_key=jina_key, input_uri=input_uri)
    elif input_type == "text":
        return process_text(data)
    else:
        sys.exit(f"Error: Unsupported input type '{input_type}'.")


def handle_output(markdown_text, output_option):
    """Output the markdown text to a file or stdout."""
    if output_option:
        output_path = os.path.join(DATA_DIR, output_option)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(markdown_text)
            print(f"Output successfully written to '{output_option}'", file=sys.stderr)
        except Exception as e:
            sys.exit(f"Error writing to '{output_option}': {e}")
    else:
        print(markdown_text)


def main(args=None):
    if args is None:
        args = parse_arguments()  # Default to command-line arguments if none provided
    else:
        pass
    
    jina_key = load_env_variables() if args.input_uri and args.input_uri.startswith(("http://", "https://")) else None

    try:
        data = read_input_data(args.input_uri)
    except InputDataError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    is_remote = args.input_uri.startswith(("http://", "https://")) if args.input_uri else False

    content = process_input_data(
        input_type=args.input_type,
        data=data,
        is_remote=is_remote,
        jina_key=jina_key,
        input_uri=args.input_uri,
    )

    calculate_tokens(content)
    handle_output(content, args.output_file)


if __name__ == "__main__":
    main()