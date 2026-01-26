import json
import os
from schema_generator import (
    SCHEMA_FILE,
    generate_schema_canonical,
    update_schema as _update_schema_internal,
    build_vector_store,
    validate_schema_structure
)

def load_current_schema():
    if not os.path.exists(SCHEMA_FILE):
        return None
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_schema(schema: dict):
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        
def build_vector_store_internal(schema: dict):
    if validate_schema_structure(schema):
        vector_store = build_vector_store(schema)
        return vector_store
    else:
        raise ValueError("Updated schema is invalid.")

def generate_schema(text: str) -> dict:
    schema = generate_schema_canonical(text)
    save_schema(schema)
    build_vector_store_internal(schema)
    return schema

def update_schema(text: str) -> dict:
    current = load_current_schema()
    if current is None:
        raise ValueError("No schema exists. Call /schema/generate first.")
    
    schema = _update_schema_internal(text, current)
    save_schema(schema)
    build_vector_store_internal(schema)
    return schema