from types import NoneType
from typing import (
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field, create_model


def create_pydantic_model(name: str, schema: dict[str, Any]) -> type[BaseModel]:  # noqa: C901
    """Create a Pydantic model or type hint from a JSON schema, handling nested structures."""
    type_mapping: dict[str, Any] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "array": list,
        "null": NoneType,  # Changed from None to NoneType
    }

    def parse_schema(sub_name: str, sub_schema: dict[str, Any]) -> Any:  # noqa: ANN401
        schema_type = sub_schema.get("type", "string")

        if "const" in sub_schema:
            return parse_const(sub_schema)

        if "enum" in sub_schema:
            return parse_enum(sub_schema)

        if isinstance(schema_type, list):
            return parse_union(schema_type)

        if schema_type == "object":
            return parse_object(sub_name, sub_schema)

        if schema_type == "array":
            return parse_array(sub_name, sub_schema)

        if schema_type == "null":
            return NoneType  # Handle "null" type separately

        return type_mapping.get(schema_type, Any)

    def parse_const(sub_schema: dict[str, Any]) -> Any:  # noqa: ANN401
        const_value = sub_schema["const"]
        if not isinstance(const_value, (str, int, float, bool, NoneType)):
            msg = f"Unsupported const value type: {type(const_value)}"
            raise TypeError(msg)
        return Literal[const_value]

    def parse_enum(sub_schema: dict[str, Any]) -> Any:  # noqa: ANN401
        """Parse enum values into a Literal type."""
        enum_values = sub_schema["enum"]
        if not enum_values:
            msg = "Enum must have at least one value"
            raise ValueError(msg)
        if not all(isinstance(v, (str, int, float, bool, NoneType)) for v in enum_values):
            msg = "Enum values must be strings, numbers, booleans, or null"
            raise TypeError(msg)
        return Literal[tuple(enum_values)]

    def parse_union(schema_types: list[str]) -> Any:  # noqa: ANN401
        types: list[Any] = []
        for t in schema_types:
            if t == "null":
                types.append(NoneType)  # Use NoneType instead of None
            else:
                types.append(type_mapping.get(t, Any))
        return Union[tuple(types)]

    def parse_object(sub_name: str, sub_schema: dict[str, Any]) -> type[BaseModel]:
        properties = sub_schema.get("properties", {})
        fields: dict[str, tuple[Any, Any]] = {}
        required_fields = sub_schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            prop_type = parse_schema(f"{sub_name}_{prop_name}", prop_schema)
            default: Any = ...
            if "default" in prop_schema:
                default = prop_schema["default"]
            elif prop_name not in required_fields:
                default = None  # Optional field
                if get_origin(prop_type) is Union:
                    if NoneType not in get_args(prop_type):
                        prop_type = Union[(*get_args(prop_type), NoneType)]
                else:
                    prop_type = Union[prop_type, NoneType]
            elif "const" in prop_schema:
                default = prop_schema["const"]
            description = prop_schema.get("description", "")
            field_info = Field(default=default, description=description)
            fields[prop_name] = (prop_type, field_info)

        return create_model(sub_name, **fields)

    def parse_array(sub_name: str, sub_schema: dict[str, Any]) -> Any:  # noqa: ANN401
        items_schema = sub_schema.get("items", {})
        item_type = parse_schema(f"{sub_name}_item", items_schema)
        return list[item_type]

    return parse_schema(name, schema)


if __name__ == "__main__":
    # Example usage with union types
    sample_schema = {
        "type": "object",
        "properties": {
            "priority": {
                "type": "string",
                "enum": [
                    "low",
                    "medium",
                    "high",
                    "urgent",
                ],
                "description": "The priority level of the escalation",
            },
        },
    }

    GeneratedModel = create_pydantic_model("Person", sample_schema)
