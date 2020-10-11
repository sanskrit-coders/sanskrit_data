from copy import deepcopy


def remove_none_keys(dict_x):
  dict_y = {}
  for key, value in iter(dict_x.items()):
    if isinstance(value, dict):
      value = remove_none_keys(value)
    if key is not None:
      dict_y[key] = value
  return dict_y


def remove_dict_none_values(value, from_dictified_objects_only=False):
  """
  Recursively remove all None values from dictionaries and lists, and returns
  the result as a new dictionary or list.
  """
  def get_non_none_valued_dict(value):
    return {
      key: remove_dict_none_values(value=val, from_dictified_objects_only=from_dictified_objects_only)
      for key, val in value.items()
      if val is not None
    }
    
  if isinstance(value, list):
    return [remove_dict_none_values(value=x, from_dictified_objects_only=from_dictified_objects_only) for x in value]
  elif isinstance(value, dict):
    if not from_dictified_objects_only:
      return get_non_none_valued_dict(value)
    else:
      from sanskrit_data.schema import common
      if common.JSONPICKLE_TYPE_FIELD in dict:
        return get_non_none_valued_dict(value)
      else:
        return value
  else:
    return value


def stringify_keys(x):
  if isinstance(x, dict):
    dict_y = {}
    for key, value in iter(x.items()):
      dict_y[str(key)] = stringify_keys(value)
    return dict_y
  elif isinstance(x, (tuple, list)):
    return [stringify_keys(y) for y in x]
  else:
    return x


def dictify(x, included_protected_attributes=None, omit_none_values=True):
  if included_protected_attributes is None:
    included_protected_attributes = ["_id"]
  from sanskrit_data.schema.common import JsonObject
  if isinstance(x, dict):
    dict_y = {}
    for key, value in iter(x.items()):
      if key is None:
        continue
      if not key.startswith("_") or key in included_protected_attributes:
        if omit_none_values != True or value is not None:
          dict_y[key] = dictify(value, included_protected_attributes=included_protected_attributes, omit_none_values=omit_none_values)
    return dict_y
  elif isinstance(x, (tuple, list)):
    return [dictify(y, included_protected_attributes=included_protected_attributes, omit_none_values=omit_none_values) for y in x]
  elif isinstance(x, JsonObject):
    dict_x = dictify(x.__dict__, included_protected_attributes=included_protected_attributes, omit_none_values=omit_none_values)
    from sanskrit_data.schema.common import TYPE_FIELD
    dict_x[TYPE_FIELD] = x.get_wire_typeid()
    return dict_x
  else:
    return x


def assert_approx_equals(x, y, floating_point_precision=None, key_trace=None):
  if key_trace is None:
    key_trace = []
  x = round_floats(dictify(x), floating_point_precision=floating_point_precision)
  y = round_floats(dictify(y), floating_point_precision=floating_point_precision)
  if isinstance(x, dict):
    try:
      assert x.keys() == y.keys(), (key_trace, sorted(x.keys()), sorted(y.keys()))
    except AssertionError:
      raise
    for key, value in iter(x.items()):
      other_value = y.get(key, None)
      assert_approx_equals(value, other_value, key_trace=key_trace + [key])
  elif isinstance(x, (list, tuple)):
    assert len(x) == len(y), (key_trace, len(x), len(y))
    for index, item in enumerate(x):
      assert_approx_equals(item, y[index], key_trace=key_trace + [index])
  else:
    assert x == y, (key_trace, x, y, type(x))


def round_floats(o, floating_point_precision):
  from sanskrit_data.schema.common import JsonObject
  if floating_point_precision is None:
    return o
  elif isinstance(o, float): return round(o, floating_point_precision)
  elif isinstance(o, dict): return {k: round_floats(v, floating_point_precision=floating_point_precision) for k, v in iter(o.items())}
  elif isinstance(o, (list, tuple)): return [round_floats(x, floating_point_precision=floating_point_precision) for x in o]
  elif isinstance(o, JsonObject):
    o = deepcopy(o)
    for k, v in iter(o.__dict__.items()):
      setattr(o, k, round_floats(v, floating_point_precision=floating_point_precision))
  return o


def tuples_to_lists(o):
  if isinstance(o, dict): return {k: tuples_to_lists(v) for k, v in iter(o.items())}
  if isinstance(o, (list, tuple)): return [tuples_to_lists(x) for x in o]
  return o


def flatten_dict(o):
  if isinstance(o, dict):
    flattened_dict = {}
    for key, value in iter(o.items()):
      if isinstance(value, dict):
        inner = flatten_dict(value)
        for key_inner, value_inner in iter(inner.items()):
          flattened_dict[".".join([key, key_inner])] = value_inner
      else:
        flattened_dict[str(key)] = flatten_dict(value)
    return flattened_dict
  if isinstance(o, (list, tuple)): return [flatten_dict(x) for x in o]
  return o


def tree_maker(leaves, path_fn):
  tree = {}
  def _insert_to_tree(path, leaf):
    segments = [x for x in path.split("/") if x != ""]
    node = tree
    for segment in segments:
      parent = node
      node = node.get(segment, {})
      parent[segment] = node
    if len(segments) > 0:
      parent[segment] = leaf
  
  for leaf in leaves:
    path = path_fn(leaf)
    _insert_to_tree(leaf=leaf, path=path)
  
  return tree


def _set_json_object_type(obj):
  from sanskrit_data.schema.common import JsonObject
  if isinstance(obj, JsonObject):
    obj.set_type()
    for key, value in iter(obj.__dict__.items()):
      _set_json_object_type(value)
  elif isinstance(obj, (list, tuple)):
    for item in obj:
      _set_json_object_type(item)
  elif isinstance(obj, dict):
    for key_inner, value_inner in obj.items():
      _set_json_object_type(value_inner)


def delete_attribute_recursively(obj, attr):
  if hasattr(obj, attr):
    delattr(obj, attr)
    for key, value in iter(obj.__dict__.items()):
      delete_attribute_recursively(value, attr)

  if isinstance(obj, (list, tuple)):
    for item in obj:
      delete_attribute_recursively(item, attr)
  elif isinstance(obj, dict):
    for key_inner, value_inner in obj.items():
      delete_attribute_recursively(value_inner, attr)




def _set_jsonpickle_type_recursively(obj, json_class_index):
  """Translates jsonClass fields to py/object"""
  if isinstance(obj, dict):
    from sanskrit_data.schema.common import TYPE_FIELD
    wire_type = obj.pop(TYPE_FIELD, None)
    if wire_type:
      from sanskrit_data.schema.common import JSONPICKLE_TYPE_FIELD
      obj[JSONPICKLE_TYPE_FIELD] = json_class_index[wire_type].__module__ + "." + wire_type
    for key, value in iter(obj.items()):
      _set_jsonpickle_type_recursively(obj=value, json_class_index=json_class_index)
  elif isinstance(obj, (list, tuple)):
    for item in obj:
      _set_jsonpickle_type_recursively(obj=item, json_class_index=json_class_index)
