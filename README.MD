# Swell 4o-structured importer

Swell LLM Importer is a Python project designed to convert unstructured product information into structured JSON for importing into the Swell eCommerce platform and using 4o structured output.

## Quick Start

1. Clone the repository and install the project:
   ```
   git clone https://github.com/codethegap/swell-llm-importer.git
   cd swell_llm_importer
   pip install -e .
   ```
   This installs the project in editable mode, allowing you to access the data folder.

2. Set up the environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys and credentials as needed. The `.env.example` file contains comments indicating which fields are required and which are optional.

3. Run the batch import:
   ```
   import_batch --batch-file examples/woo_samples.csv --batch-type csv
   ```

## Features

- Processes various input formats: CSV, JSON, or URLs
- Converts unstructured data to Swell-compatible JSON
- Customizable schema building
- OpenAI GPT-4 integration for intelligent data structuring

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

- The project uses a `data` folder for storing configuration files and schemas. After installation, you can find this folder in your project directory.
- Customize the import process by modifying the `data/instructions.yaml` file to specify which fields to include or exclude in the schema.
- The `.env` file should be in the root of your project directory. Ensure it's properly configured before running any commands.

## Data Folder

The `data` folder contains important files for the project:

- `schema.json`: The base Swell product schema.
- `instructions.yaml`: Configuration file for customizing the schema and import process.

When you run the `build_schema` script, it will look for `instructions.yaml` and `schema.json` in the `data` folder and output `schema_compiled.json` to the same location.

## Requirements

- Python 3.7+
- OpenAI API key
- Swell store credentials
- Jina AI key (for URL processing)

For a complete list of dependencies, refer to the `setup.py` file.

## How It Works

1. **build_schema**: 
   - Loads the base Swell product schema from `data/schema.json`
   - Applies modifications based on `data/instructions.yaml`
   - Generates a compiled schema (`data/schema_compiled.json`) for use in product generation

2. **preprocess_source**:
   - Accepts various input types (HTML, PDF, plain text)
   - Cleans and standardizes the input data
   - For URLs, uses Jina AI for advanced preprocessing

3. **generate_product**:
   - Uses the compiled schema and preprocessed data
   - Leverages OpenAI's GPT-4 to structure the product information
   - Outputs Swell-compatible JSON

4. **import_batch**:
   - Streamlines the process for multiple products
   - Supports CSV, JSON, and URL list inputs
   - Orchestrates the entire import process

## Notes

- Ensure all necessary API keys and credentials are set up in your `.env` file before running the importer.
- The quality of the output depends on the input data and the configured schema. Adjust the `data/instructions.yaml` file as needed for optimal results.
- For large batches, consider running the import process in smaller chunks to manage API usage and potential rate limits.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

---
For customizations or integration support, feel free to reach out to the [Code the Gap](https://www.codethegap.com/) team.
