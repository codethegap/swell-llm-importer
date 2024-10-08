import json
import yaml
import logging
import os
import sys
import copy
from jsonschema import Draft7Validator
from typing import Any, Dict, List, Union, Optional

# Constants
SCHEMA_FILE = 'schema.json'
CONFIG_FILE = 'instructions.yaml'

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


def load_schema(filename: str) -> Dict[str, Any]:
    """
    Load and validate the JSON Schema from a file.

    Args:
        filename: The filename of the JSON Schema.

    Returns:
        A dictionary representing the JSON Schema.

    Raises:
        SystemExit: If the file is not found or the JSON is invalid.
    """
    logging.info(f"Loading JSON Schema from '{filename}'...")
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            schema = json.load(f)
        # Validate that it is well-formed JSON Schema
        try:
            Draft7Validator.check_schema(schema)
            logging.info("JSON Schema is valid.")
        except Exception as e:
            logging.error(f"Invalid JSON Schema: {e}")
            sys.exit(1)
        return schema
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in '{filename}': {e}")
        sys.exit(1)


def resolve_references(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve all $ref references in the JSON Schema.

    Args:
        schema: The JSON Schema with potential $ref references.

    Returns:
        A new schema dictionary with all references resolved.
    """
    logging.info("Resolving $ref references...")
    definitions = schema.get('$defs', {})
    return _resolve_refs(schema, definitions)


def _resolve_refs(node: Any, definitions: Dict[str, Any]) -> Any:
    """
    Helper function to recursively resolve $ref references in the schema.

    Args:
        node: The current node in the schema.
        definitions: The definitions from the schema's $defs.

    Returns:
        The node with references resolved.
    """
    if isinstance(node, dict):
        if '$ref' in node:
            ref = node['$ref']
            if ref.startswith('#/$defs/'):
                def_key = ref.replace('#/$defs/', '')
                if def_key in definitions:
                    resolved_def = copy.deepcopy(definitions[def_key])
                    # Recursively resolve references in the resolved definition
                    resolved_node = _resolve_refs(resolved_def, definitions)
                    # Merge with existing keys except $ref
                    for key, value in node.items():
                        if key != '$ref':
                            resolved_node[key] = value
                    return resolved_node
                else:
                    logging.error(f"Definition '{def_key}' not found in $defs.")
                    sys.exit(1)
            else:
                logging.error(f"Unsupported $ref format: {ref}")
                sys.exit(1)
        else:
            return {k: _resolve_refs(v, definitions) for k, v in node.items()}
    elif isinstance(node, list):
        return [_resolve_refs(item, definitions) for item in node]
    else:
        return node


def load_config(filename: str) -> Dict[str, Any]:
    """
    Load the YAML configuration file.

    Args:
        filename: The filename of the YAML configuration.

    Returns:
        A dictionary representing the configuration.

    Raises:
        SystemExit: If the file is not found or the YAML is invalid.
    """
    logging.info(f"Loading configuration from '{filename}'...")
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            config = yaml.safe_load(f) or {}
        return config
    except FileNotFoundError:
        logging.error(f"File '{filename}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML in '{filename}': {e}")
        sys.exit(1)


def get_schema_node(schema_node: Dict[str, Any], path_list: List[str]) -> Optional[Dict[str, Any]]:
    """
    Navigate through the schema to find the node at the specified path.

    Args:
        schema_node: The current node in the schema.
        path_list: The list of keys representing the path to the target node.

    Returns:
        The schema node at the specified path, or None if not found.
    """
    if not path_list:
        return schema_node

    key = path_list[0]
    node_types = schema_node.get('type')
    if isinstance(node_types, list):
        node_types = node_types
    else:
        node_types = [node_types]

    if 'object' in node_types and 'properties' in schema_node:
        if key in schema_node['properties']:
            return get_schema_node(schema_node['properties'][key], path_list[1:])
    elif 'array' in node_types and 'items' in schema_node:
        return get_schema_node(schema_node['items'], path_list)

    return None


def del_schema_node(schema_node: Dict[str, Any], path_list: List[str]) -> None:
    """
    Delete a node from the schema based on the specified path.

    Args:
        schema_node: The current node in the schema.
        path_list: The list of keys representing the path to the node to delete.
    """
    if not path_list:
        return

    key = path_list[0]
    node_types = schema_node.get('type')
    if isinstance(node_types, list):
        node_types = node_types
    else:
        node_types = [node_types]

    if 'object' in node_types and 'properties' in schema_node:
        if key in schema_node['properties']:
            if len(path_list) == 1:
                del schema_node['properties'][key]
                logging.debug(f"Deleted property '{key}'")
            else:
                del_schema_node(schema_node['properties'][key], path_list[1:])
    elif 'array' in node_types and 'items' in schema_node:
        del_schema_node(schema_node['items'], path_list)


def handle_mappings(schema: Dict[str, Any], path_list: List[str], mapping_values: Dict[str, str]) -> None:
    """
    Apply mappings to a property in the schema by adding an enum and updating the description.

    Args:
        schema: The schema dictionary.
        path_list: The list of keys representing the path to the property.
        mapping_values: The mappings to apply.
    """
    prop = get_schema_node(schema, path_list)
    if prop is None:
        logging.warning(f"Property '{'.'.join(path_list)}' not found in schema.")
        return

    ids = list(mapping_values.values())
    prop_type = prop.get('type')
    if isinstance(prop_type, list):
        prop_types = prop_type
    else:
        prop_types = [prop_type]

    if 'array' in prop_types:
        if 'items' in prop:
            prop['items']['enum'] = ids
        else:
            logging.warning(f"'items' not found in array property '{'.'.join(path_list)}'.")
            return
    else:
        prop['enum'] = ids

    mappings_str = ", ".join([f"'{k}' => '{v}'" for k, v in mapping_values.items()])
    mappings_description = f"Mappings: {mappings_str}"
    prop['description'] = prop.get('description', '') + "\n" + mappings_description


def modify_schema(schema: Dict[str, Any], config: Dict[str, Any]) -> None:
    """
    Modify the schema based on the configuration.

    Args:
        schema: The schema dictionary to modify.
        config: The configuration dictionary.
    """
    logging.info("Modifying schema based on configuration...")
    for key, value in config.items():
        path_list = key.split('.')
        if isinstance(value, bool):
            if not value:
                del_schema_node(schema, path_list)
        elif isinstance(value, dict):
            handle_mappings(schema, path_list, value)
        elif isinstance(value, list):
            mapping_values = {}
            for item in value:
                if isinstance(item, dict):
                    mapping_values.update(item)
                elif isinstance(item, str):
                    mapping_values[item] = item
            handle_mappings(schema, path_list, mapping_values)
        else:
            logging.warning(f"Unsupported config value type for key '{key}'.")


def enforce_constraints(schema: Dict[str, Any]) -> None:
    """
    Enforce constraints on the schema by setting all fields as required and disabling additional properties.

    Args:
        schema: The schema dictionary to modify.
    """
    logging.info("Setting all fields as required...")
    logging.info("Setting 'additionalProperties' to false for all objects...")

    def set_required_and_additional_properties(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get('type')
            if isinstance(node_type, list):
                node_types = node_type
            else:
                node_types = [node_type]

            if 'object' in node_types and 'properties' in node:
                props = node['properties']
                node['required'] = list(props.keys())
                node['additionalProperties'] = False
                for prop in props.values():
                    set_required_and_additional_properties(prop)
            elif 'array' in node_types and 'items' in node:
                set_required_and_additional_properties(node['items'])

    set_required_and_additional_properties(schema)


def calculate_statistics(schema: Dict[str, Any]) -> None:
    """
    Calculate and report statistics about the schema.

    Args:
        schema: The schema dictionary.
    """
    logging.info("Calculating schema statistics...")
    total_properties = 0
    max_nesting = 0

    def traverse(node: Any, current_level: int) -> None:
        nonlocal total_properties, max_nesting
        if isinstance(node, dict):
            node_type = node.get('type')
            if isinstance(node_type, list):
                node_types = node_type
            else:
                node_types = [node_type]

            if 'object' in node_types and 'properties' in node:
                props = node['properties']
                total_properties += len(props)
                max_nesting = max(max_nesting, current_level)
                for prop in props.values():
                    traverse(prop, current_level + 1)
            elif 'array' in node_types and 'items' in node:
                traverse(node['items'], current_level + 1)

    traverse(schema, 1)
    logging.info(f"Total properties: {total_properties}")
    logging.info(f"Maximum nesting level: {max_nesting}")
    constraints_met = True
    if total_properties > 100:
        logging.warning("Total properties exceed 100.")
        constraints_met = False
    if max_nesting > 5:
        logging.warning("Maximum nesting level exceeds 5.")
        constraints_met = False
    if constraints_met:
        logging.info("Schema meets the property and nesting constraints.")
    else:
        logging.info("Schema does not meet the property and nesting constraints.")


def save_schema(schema: Dict[str, Any], original_filename: str) -> None:
    """
    Save the modified schema to a new file.

    Args:
        schema: The modified schema dictionary.
        original_filename: The original schema filename.
    """
    base, ext = os.path.splitext(original_filename)
    new_filename = f"{base}_compiled{ext}"
    logging.info(f"Saving modified schema to '{new_filename}'...")
    try:
        with open(os.path.join(DATA_DIR, new_filename), 'w') as f:
            json.dump(schema, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving schema: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main function to process the schema and configuration.
    """
    schema = load_schema(SCHEMA_FILE)
    schema = resolve_references(schema)
    # Remove $defs and $ref from the schema to make it self-contained
    schema.pop('$defs', None)
    config = load_config(CONFIG_FILE)
    modify_schema(schema, config)
    enforce_constraints(schema)
    calculate_statistics(schema)
    save_schema(schema, SCHEMA_FILE)
    logging.info("Process completed successfully.")


if __name__ == '__main__':
    main()