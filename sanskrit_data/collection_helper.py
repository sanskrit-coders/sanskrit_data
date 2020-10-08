import logging


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


def dictify(x, included_protected_attributes=["_id"]):
  from sanskrit_data.schema.common import JsonObject
  if isinstance(x, dict):
    dict_y = {}
    for key, value in iter(x.items()):
      if key is None:
        continue
      if not key.startswith("_") or key in included_protected_attributes:
        dict_y[key] = dictify(value, included_protected_attributes=included_protected_attributes)
    return dict_y
  elif isinstance(x, (tuple, list)):
    return [dictify(y, included_protected_attributes=included_protected_attributes) for y in x]
  elif isinstance(x, JsonObject):
    return dictify(x.__dict__, included_protected_attributes=included_protected_attributes)
  else:
    return x


def assert_dict_equality(x, y, floating_point_precision=None, key_trace=[]):
  try:
    assert x.keys() == y.keys(), (key_trace, sorted(x.keys()), sorted(y.keys()))
  except AssertionError:
    raise
  x = round_floats(tuples_to_lists(x), floating_point_precision=floating_point_precision)
  y = round_floats(tuples_to_lists(y), floating_point_precision=floating_point_precision)
  for key, value in iter(x.items()):
    other_value = y.get(key, None)
    if isinstance(value, dict):
      try:
        assert_dict_equality(value, other_value, key_trace=key_trace+[key])
      except AssertionError:
        logging.error(key)
        raise
    elif isinstance(value, list):
      try:
        assert len(value) == len(other_value), (key_trace+[key], value, other_value)
      except AssertionError:
        logging.error("key: %s", key)
        raise
      for index, item in enumerate(value):
        if isinstance(value, dict):
          try:
            assert_dict_equality(item, other_value[index], key_trace=key_trace+[key, index])
          except AssertionError:
            logging.error("key: %s, index: %s", key, index)
            raise
        else:
          try:
              assert item == other_value[index], (key_trace+[key, index], item, other_value[index])
          except AssertionError:
            logging.error("key: %s, index: %s", key, index)
            raise
    else:
      try:
        assert value == other_value, (key_trace+[key], value, other_value, type(value))
      except AssertionError:
        logging.error("key: %s", key)
        raise


def round_floats(o, floating_point_precision):
  if floating_point_precision is None:
    return o
  if isinstance(o, float): return round(o, floating_point_precision)
  if isinstance(o, dict): return {k: round_floats(v, floating_point_precision=floating_point_precision) for k, v in iter(o.items())}
  if isinstance(o, (list, tuple)): return [round_floats(x, floating_point_precision=floating_point_precision) for x in o]
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
    parent[segment] = leaf
  
  for leaf in leaves:
    path = path_fn(leaf)
    _insert_to_tree(leaf=leaf, path=path)
  
  return tree