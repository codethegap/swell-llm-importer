# Swell LLM Importer

Swell LLM Importer is a Python project designed to convert unstructured product information into structured JSON for importing into the Swell eCommerce platform and using gpt 4o structured output.

## Quick Start

1. Install the project:
   ```
   pip install git+https://github.com/codethegap/swell-llm-importer.git
   ```

2. Copy the `.env.example` file to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys and credentials as needed. The `.env.example` file contains comments indicating which fields are required and which are optional.

3. Run the batch import:
   ```
   import_batch --batch-file examples/shopify_samples.csv --batch-type csv
   ```

## Features

- Processes various input formats: CSV, JSON, or URLs
- Converts unstructured data to Swell-compatible JSON
- Customizable schema building
- OpenAI GPT-4 integration for data structuring

## Main Components

1. **build_schema**: Generates a JSON schema based on Swell's product structure and user-defined instructions.
2. **preprocess_source**: Cleans and standardizes input data from various sources (HTML, PDF, plain text).
3. **generate_product**: Creates structured product data using the schema and preprocessed information.
4. **import_batch**: Simplifies the import process for multiple products.

## Usage Examples

Process a single product:
```
build_schema && preprocess_source --input-uri "https://example.com/product" --input-type webpage | generate_product --output swell
```

Batch import from CSV:
```
import_batch --batch-file examples/shopify_samples.csv --batch-type csv
```

Batch import from JSON:
```
import_batch --batch-file examples/woo_samples.json --batch-type json
```

Batch import from URLs:
```
import_batch --batch-file examples/shopify-loox.txt --batch-type urls
```

## Configuration

- Customize the import process by modifying the `instructions.yaml` file to specify which fields to include or exclude in the schema. Specify your categories lookup.
- Refer to the `.env.example` file for required and optional environment variables. Copy this file to `.env` and fill in your specific credentials.

## Requirements

- Python 3.7+
- OpenAI API key
- Swell store credentials
- Jina AI key (for URL processing)

For a complete list of dependencies, refer to the `setup.py` file.

## How It Works

1. **build_schema**: 
   - Loads the base Swell product schema
   - Applies modifications based on `instructions.yaml`
   - Generates a compiled schema for use in product generation

2. **preprocess_source**:
   - Accepts various input types (HTML, PDF, plain text)
   - Cleans and standardizes the input data
   - For URLs, uses jina.ai for advanced preprocessing

3. **generate_product**:
   - Uses the compiled schema and preprocessed data
   - Leverages OpenAI's GPT-4o to structure the product information
   - Outputs Swell-compatible JSON

4. **import_batch**:
   - Streamlines the process for multiple products
   - Supports CSV, JSON, and URL list inputs
   - Orchestrates the entire import process

## Notes

- Ensure all necessary API keys and credentials are set up in your `.env` file before running the importer.
- The quality of the output depends on the input data and the configured schema. Adjust the `instructions.yaml` file as needed for optimal results.
- For large batches, consider running the import process in smaller chunks to manage API usage and potential rate limits.

## License

[MIT License](LICENSE)