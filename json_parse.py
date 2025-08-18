import json
import argparse
from collections import OrderedDict
from typing import Any, Dict, List, Set


def load_json(path: str) -> Any:
	"""Load JSON file from disk."""
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)


def merge_dict_keys(dicts: List[Dict[str, Any]]) -> List[str]:
	"""Return a sorted list of all keys present in any of the dictionaries."""
	all_keys: Set[str] = set()
	for d in dicts:
		all_keys.update(d.keys())
	return sorted(all_keys)


def summarize_list(value: List[Any]) -> str:
	if not value:
		return 'list[empty]'
	# Collect elementary type names for all elements (non-recursive summarization)
	elem_type_names = []
	for v in value:
		elem_type_names.append(basic_type_name(v))
	unique = sorted(set(elem_type_names))
	return f"list[len={len(value)}]<{'|'.join(unique)}>"


def basic_type_name(v: Any) -> str:
	if isinstance(v, dict):
		return 'object'
	if isinstance(v, list):
		return 'list'
	if v is None:
		return 'null'
	return type(v).__name__


def build_schema(value: Any) -> Any:
	"""Build a lightweight schema-like representation from a JSON value.

	For objects -> OrderedDict of key -> subschema
	For lists -> dict with markers: {"__list__": <element schema or set of element types>}
	For primitives -> python type name
	"""
	if isinstance(value, dict):
		schema: "OrderedDict[str, Any]" = OrderedDict()
		# Iterate in original order (json.load preserves source order in Python 3.7+)
		for k, v in value.items():
			schema[k] = build_schema(v)
		return schema
	if isinstance(value, list):
		if not value:
			return {"__list__": {"element_types": [], "element_schema": None}}
		# If all elements are dicts, merge their schemas.
		if all(isinstance(el, dict) for el in value):
			# Build merged schema preserving first-seen key order across list elements.
			merged: Dict[str, List[Any]] = {}
			key_order: List[str] = []
			for el in value:
				for k, v in el.items():
					if k not in merged:
						merged[k] = []
						key_order.append(k)
					merged[k].append(v)
			merged_schema: OrderedDict[str, Any] = OrderedDict()
			for k in key_order:
				vals = merged[k]
				if all(not isinstance(x, (dict, list)) for x in vals):
					# Preserve order of first occurrence of each primitive type
					seen_types: List[str] = []
					for x in vals:
						tn = basic_type_name(x)
						if tn not in seen_types:
							seen_types.append(tn)
					if len(seen_types) == 1:
						merged_schema[k] = seen_types[0]
					else:
						merged_schema[k] = f"union<{','.join(seen_types)}>"
				else:
					complex_candidate = next((x for x in vals if isinstance(x, (dict, list))), None)
					merged_schema[k] = build_schema(complex_candidate)
			element_schema = merged_schema
		else:
			# Heterogeneous list or primitives
			element_schema = None
		# Preserve element type order (first appearance) while removing duplicates
		elem_types: List[str] = []
		for el in value:
			name = basic_type_name(el)
			if name not in elem_types:
				elem_types.append(name)
		return {"__list__": {"element_types": elem_types, "element_schema": element_schema}}
	# Primitive
	return basic_type_name(value)


def print_schema(schema: Any, indent: int = 0, key_name: str | None = None):
	"""Pretty-print the schema produced by build_schema."""
	prefix = ' ' * indent
	if isinstance(schema, OrderedDict):
		if key_name is not None:
			print(f"{prefix}{key_name}: object")
		for k, v in schema.items():
			print_schema(v, indent + (0 if key_name is None else 2), k)
	elif isinstance(schema, dict) and "__list__" in schema:
		meta = schema["__list__"]
		elem_types = meta["element_types"]
		type_str = f"list<{ '|'.join(elem_types) }>"
		if key_name is not None:
			print(f"{prefix}{key_name}: {type_str}")
		element_schema = meta["element_schema"]
		if isinstance(element_schema, OrderedDict):
			# print element object fields
			for k, v in element_schema.items():
				print_schema(v, indent + 2, k)
	else:
		if key_name is not None:
			print(f"{prefix}{key_name}: {schema}")
		else:
			print(f"{prefix}{schema}")


def collect_paths(schema: Any, base: str = "") -> List[str]:
	paths: List[str] = []
	if isinstance(schema, OrderedDict):
		for k, v in schema.items():
			new_base = f"{base}.{k}" if base else k
			if isinstance(v, (OrderedDict, dict)):
				paths.extend(collect_paths(v, new_base))
			else:
				paths.append(f"{new_base}: {v}")
	elif isinstance(schema, dict) and "__list__" in schema:
		meta = schema["__list__"]
		elem_types = '|'.join(meta['element_types'])
		paths.append(f"{base}: list<{elem_types}>")
		if isinstance(meta['element_schema'], OrderedDict):
			paths.extend(collect_paths(meta['element_schema'], base + '[]'))
	else:
		paths.append(f"{base}: {schema}")
	return paths


def main():
	parser = argparse.ArgumentParser(description="Infer and display data types for each key in a nested JSON file.")
	parser.add_argument('json_file', help='Path to JSON file (e.g. sample_get.json)')
	parser.add_argument('--mode', choices=['tree', 'paths', 'both'], default='tree', help='Output format.')
	args = parser.parse_args()

	data = load_json(args.json_file)
	schema = build_schema(data)

	if args.mode in ('tree', 'both'):
		print("# Schema (tree view)")
		print_schema(schema)
	if args.mode in ('paths', 'both'):
		print("\n# Schema (dot paths)")
		for line in collect_paths(schema):
			print(line)


if __name__ == '__main__':
	main()

