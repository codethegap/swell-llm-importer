#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time

# Import the modules
import preprocess_source
import generate_product

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def process_csv_batch(batch_file):
    """Process a CSV batch file and return a list of CSV strings, each containing the header and one data row."""
    products = []
    with open(os.path.join(DATA_DIR, batch_file), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print('Error: CSV file is empty.')
            sys.exit(1)
        for row in reader:
            output = csv.StringIO()
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerow(row)
            products.append(output.getvalue())
    return products

def find_first_array(obj):
    """Recursively find the first array in a JSON object."""
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, dict):
        for value in obj.values():
            result = find_first_array(value)
            if result is not None:
                return result
        return None
    else:
        return None

def process_json_batch(batch_file):
    """Process a JSON batch file and return a list of JSON strings, each representing an element in the first array."""
    products = []
    with open(os.path.join(DATA_DIR, batch_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
        array = find_first_array(data)
        if array is None:
            print('Error: No array found in JSON file.')
            sys.exit(1)
        for item in array:
            product_str = json.dumps(item)
            products.append(product_str)
    return products

def process_urls_batch(batch_file):
    """Process a TXT batch file containing URLs and return a list of valid URLs."""
    products = []
    url_pattern = re.compile(
        r'^(https?|ftp):\/\/'                 # Scheme
        r'(?:(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,6}'  # Domain
        r'|localhost'                         # localhost
        r'|\d{1,3}(?:\.\d{1,3}){3})'          # or IP
        r'(?::\d+)?'                          # Optional port
        r'(?:\/\S*)?$'                        # Path
    )
    with open(os.path.join(DATA_DIR, batch_file), 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url_pattern.match(url):
                products.append(url)
            else:
                print(f'Invalid URL skipped: {url}')
    return products

def main():
    """Main function to process the batch file and import products."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Import batch products into the e-commerce system.')
    parser.add_argument('--batch-file', required=True, help='Path to the input batch file (CSV, JSON, or TXT) in data folder.')
    parser.add_argument('--batch-type', required=True, choices=['csv', 'json', 'urls'], help='Type of the batch file.')
    args = parser.parse_args()

    batch_file = args.batch_file
    batch_type = args.batch_type

    # Validate batch file
    if not os.path.isfile(os.path.join(DATA_DIR, batch_file)):
        print(f'Error: The batch file "{batch_file}" does not exist or is not a file.')
        sys.exit(1)

    # Process the batch file based on batch_type
    if batch_type == 'csv':
        products = process_csv_batch(batch_file)
    elif batch_type == 'json':
        products = process_json_batch(batch_file)
    elif batch_type == 'urls':
        products = process_urls_batch(batch_file)
    else:
        print(f'Error: Invalid batch type "{batch_type}".')
        sys.exit(1)

    # Calculate the number of products and confirm with the user
    num_products = len(products)
    print(f'Found {num_products} product(s) to import.')
    proceed = input(f'Do you want to continue with processing of {num_products} product records? (y/n): ').strip().lower()
    if proceed not in ('y', 'yes'):
        print('Operation cancelled by the user.')
        sys.exit(0)

    # Create the data directory
    unique_id = int(time.time())
    data_dir = os.path.join(DATA_DIR, f'batch_{unique_id}')
    #data_dir = f'./data/batch_{unique_id}'
    os.makedirs(data_dir, exist_ok=True)

    # Process each product
    success_count = 0
    for index, product in enumerate(products, start=1):
        print(f'Processing product {index}/{num_products}...')
        product_file = os.path.join(data_dir, str(index))

        if batch_type in ('csv', 'json'):
            # Write the product string to a file
            with open(product_file, 'w', encoding='utf-8') as f:
                f.write(product)
            input_uri = f'file://{os.path.abspath(product_file)}'
            input_type = 'text'
        elif batch_type == 'urls':
            input_uri = product  # The URL itself
            input_type = 'webpage'

        output_file = product_file  # Same for all types

        # Prepare arguments for preprocess_source
        preprocess_args = argparse.Namespace(
            input_uri=input_uri,
            input_type=input_type,
            output_file=output_file
        )

        # Call preprocess_source.main()
        try:
            preprocess_source.main(preprocess_args)
        except Exception as e:
            print(f'Error in preprocess_source for product {index}: {e}')
            continue  # Skip to the next product

        # Prepare arguments for generate_product
        generate_args = argparse.Namespace(
            mdfile=product_file,
            output='swell'
        )

        # Call generate_product.main()
        try:
            generate_product.main(generate_args)
            print(f'Product {index} imported successfully.')
            success_count += 1
        except Exception as e:
            print(f'Error in generate_product for product {index}: {e}')
            continue  # Skip to the next product

    # Completion message
    print(f'{success_count} out of {num_products} products were imported.')

    # Ask the user whether to delete interim data
    cleanup = input(f'Do you want to delete interim data at {data_dir}? (y/n): ').strip().lower()
    if cleanup in ('y', 'yes'):
        try:
            shutil.rmtree(data_dir)
            print('Interim data deleted.')
        except Exception as e:
            print(f'Error deleting interim data: {e}')
    else:
        print(f'Interim data kept at {data_dir}.')

if __name__ == '__main__':
    main()