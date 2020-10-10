"""
A module containing some data container base classes.
"""

from __future__ import absolute_import

import json
import logging
import sys
from copy import deepcopy

import jsonpickle
import jsonschema
import toml
from jsonschema import SchemaError
from jsonschema import ValidationError
from jsonschema.exceptions import best_match
from six import string_types

from sanskrit_data import collection_helper, file_helper
from sanskrit_data.collection_helper import round_floats, tuples_to_lists

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

JSONPICKLE_TYPE_FIELD = "py/object"
TYPE_FIELD = "jsonClass"

#: Maps jsonClass values to the containing Python module object. Useful for (de)serialization. Updated using :func:`update_json_class_index` calls at the end of each module file (such as this one) whose classes may be serialized.
json_class_index = {}


def update_json_class_index(module_in, json_class_index=json_class_index):
  """Call this function to enable (de)serialization.

  Usage example: common.update_json_class_index(sys.modules[__name__]).
  """
  import inspect
  for name, obj in inspect.getmembers(module_in):
    if inspect.isclass(obj):
      json_class_index[name] = obj


def check_class(obj, allowed_types):
  results = [isinstance(obj, some_type) for some_type in allowed_types]
  # logging.debug(results)
  return True in results


def check_list_item_types(some_list, allowed_types):
  check_class_results = [check_class(item, allowed_types=allowed_types) for item in some_list]
  # logging.debug(check_class_results)
  return not (False in check_class_results)


def recursively_merge_json_schemas(a, b, json_path=""):
  assert a.__class__ == b.__class__, str(a.__class__) + " vs " + str(b.__class__)

  if isinstance(b, dict) and isinstance(a, dict):
    a_and_b = set(a.keys()) & set(b.keys())
    every_key = set(a.keys()) | set(b.keys())
    merged_dict = {}
    for k in every_key:
      if k in a_and_b:
        merged_dict[k] = recursively_merge_json_schemas(a[k], b[k], json_path=json_path + "/" + k)
      else:
        merged_dict[k] = deepcopy(a[k] if k in a else b[k])
    return merged_dict
  elif isinstance(b, list) and isinstance(a, list) and not json_path.endswith(TYPE_FIELD + "/enum"):
    # TODO: What if we have a list of dicts?
    return list(set(a + b))
  else:
    return deepcopy(b)


def _set_json_object_type(obj):
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


def _set_jsonpickle_type_recursively(obj, json_class_index):
  """Translates jsonClass fields to py/object"""
  if isinstance(obj, dict):
    wire_type = obj.pop(TYPE_FIELD, None)
    if wire_type:
      obj[JSONPICKLE_TYPE_FIELD] = json_class_index[wire_type].__module__ + "." + wire_type
    for key, value in iter(obj.items()):
      _set_jsonpickle_type_recursively(obj=value, json_class_index=json_class_index)
  elif isinstance(obj, (list, tuple)):
    for item in obj:
      _set_jsonpickle_type_recursively(obj=item, json_class_index=json_class_index)


class JsonObject(object):
  """The base class of all Json-serializable data container classes, with many utility methods."""

  schema = {
    "type": "object",
    "$schema": "https://json-schema.org/draft/2019-09/schema",
    "properties": {
      TYPE_FIELD: {
        "type": "string",
        "description": "A hint used by json libraries to deserialize json data to an object of the appropriate type."
                       " This is necessary for sub-objects to have as well (to ensure that the deserialization functions as expected)."
      },
    },
    "required": [TYPE_FIELD]
  }

  DEFAULT_TO_NONE__DEFAULT = True

  def __getattr__(self, name):
    if name == "default_to_none":
      return JsonObject.DEFAULT_TO_NONE__DEFAULT
    if self.default_to_none:
      return None
    else:
      # Default behaviour
      raise AttributeError

  # We override this because messing with __getattr__ has resulted in deepcopy breakage.
  def __deepcopy__(self, memo):
    return self.make_from_dict(self.to_json_map())

  def __init__(self):
    # Dont do: self._id = None . You'll get "_id": null when the object is serialized.
    self.set_type()
    self.default_to_none = JsonObject.DEFAULT_TO_NONE__DEFAULT

  def __hash__(self):
    return hash(self.__str__())

  @classmethod
  def make_from_dict(cls, input_dict, **kwargs):
    """Defines *our* canonical way of constructing a JSON object from a dict.

    All other deserialization methods should use this.
    Note that this assumes that json_class_index is populated properly!
    Note that constructor is NOT called and variable initializations therein won't take effect.

    - ``from sanskrit_data.schema import *`` before using this should take care of it.

    :param input_dict:
    :return: A subclass of JsonObject
    """
    if input_dict is None:
      return None
    assert TYPE_FIELD in input_dict, "no type field: " + str(input_dict)
    dict_without_id = deepcopy(input_dict)
    _id = dict_without_id.pop("_id", None)

    _set_jsonpickle_type_recursively(obj=dict_without_id, json_class_index=json_class_index)

    new_obj = jsonpickle.decode(json.dumps(dict_without_id))
    for key, value in kwargs.items():
      setattr(new_obj, key, value)
    # logging.debug(new_obj.__class__)
    if _id:
      new_obj._id = str(_id)
    _set_json_object_type(new_obj)
    return new_obj

  @classmethod
  def make_from_dict_list(cls, input_dict_list):
    assert isinstance(input_dict_list, list)
    return [cls.make_from_dict(input_dict=input_dict) for input_dict in input_dict_list]

  @classmethod
  def make_from_pickledstring(cls, pickle):
    input_str = pickle
    if not isinstance(pickle, str):
      input_str = str(pickle,'utf-8')
    if input_str.strip().startswith("["):
      return cls.make_from_dict_list(jsonpickle.decode(pickle))
    else:
      obj = cls.make_from_dict(jsonpickle.decode(pickle))
      return obj

  @classmethod
  def read_from_file(cls, filename, name_to_json_class_index_extra=None, **kwargs):
    """
    
    :param filename: the file which should be read.
    :param name_to_json_class_index_extra: An optional dictionary mapping names to class objects. For example: {"Panchangam": annual.Panchangam}  
    :return: 
    """
    if name_to_json_class_index_extra is not None:
      json_class_index.update(name_to_json_class_index_extra)
    try:
      with open(filename) as fhandle:
        format = file_helper.deduce_format_from_filename(filename)
        if "json" in format:
          input_dict = jsonpickle.decode(fhandle.read())
        elif "toml" in format:
          input_dict = toml.loads(fhandle.read())
        obj = cls.make_from_dict(input_dict=input_dict, **kwargs)
        return obj
    except Exception as e:
      try:
        import traceback
        traceback.print_exc()
        logging.info("Could not load as a dict. May be a list of dicts. Trying..")
        with open(filename) as fhandle:
          obj = cls.make_from_dict_list(jsonpickle.decode(fhandle.read()))
          return obj
      except Exception as e:
        logging.error("Error reading " + filename + " : ".format(e))
        raise e

  def dump_to_file(self, filename: str, floating_point_precision: int = None, sort_keys: bool = True) -> None:
    try:
      import os
      os.makedirs(os.path.dirname(filename), exist_ok=True)
      with open(filename, "w") as f:
        format = file_helper.deduce_format_from_filename(filename)
        f.write(self.to_string(format=format, floating_point_precision=floating_point_precision, sort_keys=sort_keys))
    except Exception as e:
      logging.error("Error writing " + filename + " : ".format(e))
      raise e

  @classmethod
  def get_wire_typeid(cls):
    return cls.__name__

  @classmethod
  def get_jsonpickle_typeid(cls):
    return cls.__module__ + "." + cls.__name__

  @classmethod
  def get_json_map_list(cls, some_list):
    return [item.to_json_map() for item in some_list]

  def get_external_storage_path(self, db_interface):
    """Get the directory path where files associated with this object are to be stored."""
    import os
    return os.path.join(db_interface.external_file_store, self._id)

  def list_files(self, db_interface, suffix_pattern="*"):
    import glob
    import os
    file_list = glob.glob(pathname=os.path.join(self.get_external_storage_path(db_interface=db_interface), suffix_pattern))
    return [os.path.basename(f) for f in file_list]

  def set_type(self):
    # self.class_type = str(self.__class__.__name__)
    setattr(self, TYPE_FIELD, self.__class__.get_wire_typeid())
    # setattr(self, TYPE_FIELD, self.__class__.__name__)

  def set_jsonpickle_type_recursively(self):
    self.set_type()
    for key, value in iter(self.__dict__.items()):
      if isinstance(value, JsonObject):
        _set_json_object_type(value)
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, JsonObject):
            item.set_jsonpickle_type_recursively()
      elif isinstance(value, dict):
        for key_inner, value_inner in enumerate(value.items()):
          if isinstance(value_inner, JsonObject):
            value_inner.set_jsonpickle_type_recursively()

  def to_string(self, format="json", floating_point_precision=None, sort_keys=True):
    json_map = self.to_json_map(floating_point_precision=floating_point_precision)
    if format == "json":
      return json.dumps(json_map, sort_keys=sort_keys, indent=2)
    else:
      return toml.dumps(json_map)

  def __str__(self):
    return self.to_string(format="json")

  def set_from_dict(self, input_dict):
    if input_dict:
      for key, value in iter(input_dict.items()):
        if isinstance(value, list):
          setattr(self, key,
                  [JsonObject.make_from_dict(item) if isinstance(item, dict) else item for item in value])
        elif isinstance(value, dict):
          setattr(self, key, JsonObject.make_from_dict(value))
        else:
          setattr(self, key, value)

  # noinspection PyShadowingBuiltins
  def set_from_id(self, db_interface, id):
    return self.set_from_dict(db_interface.find_by_id(id=id))

  def to_json_map(self, floating_point_precision=None):
    """One convenient way of 'serializing' the object.

    So, the type must be properly set.
    Many functions accept such json maps, just as they accept strings.
    """
    _set_json_object_type(self)
    json_map = collection_helper.dictify(self)
    if self.default_to_none:
      json_map = collection_helper.remove_dict_none_values(json_map)
    json_map = tuples_to_lists(json_map)
    # Sometimes values may be ugly dicts.
    json_map = collection_helper.remove_none_keys(json_map)
    json_map = collection_helper.stringify_keys(json_map)
    if floating_point_precision is not None:
      rounded = round_floats(json_map, floating_point_precision=floating_point_precision)
      return rounded
    else:
      return json_map


  def __eq__(self, other):
    """Overrides the default implementation"""
    return super(JsonObject, self).__eq__(other) or isinstance(other, JsonObject) and self.equals_ignore_id(other=other)

  def equals_ignore_id(self, other):
    # Makes a unicode copy.
    def to_unicode(text):
      if isinstance(text, dict):
        return {key: to_unicode(value) for key, value in iter(text.items())}
      elif isinstance(text, list):
        return [to_unicode(element) for element in text]
      elif isinstance(text, string_types):
        return text.encode('utf-8')
      else:
        return text

    dict1 = to_unicode(self.to_json_map())
    dict1.pop("_id", None)
    # logging.debug(self.__dict__)
    # logging.debug(dict1)
    dict2 = to_unicode(other.to_json_map())
    dict2.pop("_id", None)
    # logging.debug(other.__dict__)
    # logging.debug(dict2)
    return dict1 == dict2

  def match_filter(self, find_filter):
    flat_json_map = collection_helper.flatten_dict(self.to_json_map())
    for key, value in iter(find_filter.items()):
      value_at_key = flat_json_map.get(key, None)
      if isinstance(value_at_key, list) and isinstance(value, dict) and value.get("$elemMatch", None) is not None:
        jo_values = [JsonObject.make_from_dict(item) for item in value_at_key]
        filtered_values = [item for item in jo_values if item.match_filter(value.get("$elemMatch", None))]
        if len(filtered_values) == 0:
          return False
      elif value_at_key != value:
        return False
    return True


  def update_collection(self, db_interface, user=None):
    """Do JSON validation and write to database."""
    _set_json_object_type(self)
    if getattr(self, "schema", None) is not None:
      self.validate(db_interface=db_interface, user=user)
    updated_doc = db_interface.update_doc(self.to_json_map())
    updated_obj = JsonObject.make_from_dict(updated_doc)
    return updated_obj

  def validate_deletion(self, db_interface, user=None):
    if getattr(self, "_id", None) is None:
      raise ValidationError("_id not present!")

  def delete_in_collection(self, db_interface, user=None):
    """

    To delete referrent items also, use appropriate method in JsonObjectNode.
    :param db_interface:
    :param user:
    :return:
    """
    self.validate_deletion(db_interface=db_interface, user=user)
    import shutil
    db_interface.delete_doc(self._id)
    shutil.rmtree(path=self.get_external_storage_path(db_interface=db_interface), ignore_errors=True)

  def validate(self, db_interface=None, user=None):
    """Validate the JSON serialization of this object using the schema member. Called before database writes.

    :param user:
    :param db_interface: Potentially useful in subclasses to perform validations (eg. is the target_id valid).
      This value may not be available: for example when called from the from_details methods.

    :return: a boolean.
    """
    self.validate_schema()

  # Override and call this method to add extra validations.
  def validate_schema(self):
    json_map = self.to_json_map()
    json_map.pop("_id", None)
    # logging.debug(str(self))
    try:
      jsonschema.validate(json_map, self.schema)

      # Subobjects could have specialized validation rules, specified using validate_schema overrides. Hence we specially call those methods.
      for key, value in iter(self.__dict__.items()):
        # logging.debug("%s %s", key, value)
        if isinstance(value, JsonObject):
          value.validate_schema()
        elif isinstance(value, list):
          json_map[key] = [item.validate_schema() if isinstance(item, JsonObject) else item for item in value]
        else:
          pass
    except SchemaError as e:
      logging.error("Exception message: " + e.message)
      logging.error("Schema is: " + jsonpickle.dumps(self.schema))
      logging.error("Context is: " + str(e.context))
      logging.error("Best match is: " + str(best_match(errors=[e])))
      raise e
    except ValidationError as e:
      logging.error("Exception message: " + e.message)
      logging.error("self is: " + str(self))
      logging.error("Schema is: " + jsonpickle.dumps(self.schema))
      logging.error("Context is: " + str(e.context))
      logging.error("Best match is: " + str(best_match(errors=[e])))
      logging.error("json_map is: " + jsonpickle.dumps(json_map))
      raise e

  # noinspection PyShadowingBuiltins
  @classmethod
  def from_id(cls, id, db_interface):
    """Returns None if nothing is found."""
    item_dict = db_interface.find_by_id(id=id)
    item = None
    if item_dict is not None:
      item = cls.make_from_dict(item_dict)
    return item

  @classmethod
  def add_indexes(cls, db_interface):
    db_interface.add_index(keys_dict={
      "jsonClass": 1
    }, index_name="jsonClass")


class TargetValidationError(Exception):
  def __init__(self, allowed_types, target_obj, targeting_obj):
    self.allowed_types = allowed_types
    self.target_obj = target_obj
    self.targeting_obj = targeting_obj
    self.message = str(self)

  def __str__(self):
    return "%s\n targets object \n" \
           "%s,\n" \
           "which does not belong to \n" \
           "%s" % (self.targeting_obj, self.target_obj, str(self.allowed_types))


# noinspection PyProtectedMember,PyUnresolvedReferences
class Target(JsonObject):
  schema = recursively_merge_json_schemas(JsonObject.schema, {
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["Target"]
      },
      "container_id": {
        "type": "string"
      }
    },
    "required": ["container_id"]
  })

  def get_target_entity(self, db_interface):
    """Returns null if db_interface doesnt have any such entity."""
    return JsonObject.from_id(id=self.container_id, db_interface=db_interface)

  def check_target_class(self, db_interface, allowed_types, targeting_obj):
    if db_interface is not None:
      target_entity = self.get_target_entity(db_interface=db_interface)
      if not check_class(obj=target_entity, allowed_types=allowed_types):
        raise TargetValidationError(allowed_types=allowed_types, targeting_obj=targeting_obj,
                                    target_obj=target_entity)

  @classmethod
  def check_target_classes(cls, targets_to_check, db_interface, allowed_types, targeting_obj):
    for target in targets_to_check:
      target.check_target_class(db_interface=db_interface, allowed_types=allowed_types, targeting_obj=targeting_obj)

  @classmethod
  def from_details(cls, container_id):
    target = Target()
    target.container_id = container_id
    target.validate()
    return target

  @classmethod
  def from_ids(cls, container_ids):
    return [Target.from_details(str(container_id)) for container_id in container_ids]

  @classmethod
  def from_containers(cls, containers):
    return Target.from_ids(container_ids=[container._id for container in containers])


class DataSource(JsonObject):
  schema = recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "description": "Source of the json-data which contains this node. Eg. Uploader details in case of books, annotator in case of annotations."
                   " Consider naming the field that contains this object `source` to make querying uniform.",
    TYPE_FIELD: {
      "enum": ["DataSource"]
    },
    "properties": {
      "source_type": {
        "type": "string",
        "enum": ["system_inferred", "user_supplied"],
        "description": "Does this data come from a machine, or a human? source_ prefix avoids keyword conflicts in some languages.",
        "default": "system_inferred"
      },
      "id": {
        "type": "string",
        "description": "Something to identify the particular data source.",
      },
      "by_admin": {
        "type": "boolean",
        "description": "Was the creator of this data an admin at the time it was created or updated?"
      }
    },
    "required": ["source_type"]
  }))

  def __init__(self):
    """Set the default properties"""
    super().__init__()
    # noinspection PyTypeChecker
    self.source_type = self.schema["properties"]["source_type"]["default"]

  # noinspection PyShadowingBuiltins
  @classmethod
  def from_details(cls, source_type, id):
    source = DataSource()
    source.source_type = source_type
    source.id = id
    source.validate_schema()
    return source

  def infer_by_admin(self, db_interface=None, user=None):
    if getattr(self, "by_admin", None) is None:
      # source_type is a compulsory attribute, because that validation is done separately and a suitable error is thrown.
      if getattr(self, "source_type", None) is not None and self.source_type == "user_supplied":
        if user is not None and db_interface is not None:
          if getattr(self, "id", None) is None or self.id in user.get_user_ids():
            self.by_admin = user.is_admin(service=db_interface.db_name_frontend)

  def setup_source(self, db_interface=None, user=None):
    if getattr(self, "source_type", None) is None:
      self.source_type = "user_supplied" if (user is not None and user.is_human()) else "system_inferred"
    if getattr(self, "id", None) is None and user is not None and user.get_first_user_id_or_none() is not None:
      self.id = user.get_first_user_id_or_none()

  def is_id_impersonated_by_non_admin(self, db_interface=None, user=None):
    """A None user is assumed to be a valid authorized backend script."""
    if getattr(self, "id", None) is not None and user is not None and db_interface is not None:
      if self.id not in user.get_user_ids() and not user.is_admin(service=db_interface.db_name_frontend):
        return True
    return False

  def validate(self, db_interface=None, user=None):
    if self.is_id_impersonated_by_non_admin(db_interface=db_interface, user=user):
      raise ValidationError("Impersonation by %(id_1)s as %(id_2)s not allowed for this user." % dict(id_1=user.get_first_user_id_or_none(), id_2=self.id))
    if "user" in self.source_type and getattr(self, "id", None) is None:
      raise ValidationError("User id compulsary for user sources.")
    if getattr(self, "source_type", None) is not None and self.source_type == "system_inferred":
      if user is not None and user.is_human() and not user.is_admin(service=db_interface.db_name_frontend):
        raise ValidationError("Impersonation by %(id_1)s as a bot not allowed for this user." % dict(id_1=user.get_first_user_id_or_none()))
    super(DataSource, self).validate(db_interface=db_interface, user=user)

    # Only if the writer user is an admin or None, allow by_admin to be set to true (even when the admin is impersonating another user).
    if getattr(self, "by_admin", None) is not None and self.by_admin:
      if user is not None and db_interface is not None and not user.is_admin(service=db_interface.db_name_frontend):
        raise ValidationError("Impersonation by %(id_1)s of %(id_2)s not allowed for this user." % dict(id_1=user.get_first_user_id_or_none(), id_2=self.id))

      # source_type is a compulsory attribute, because that validation is done separately and a suitable error is thrown.
      if getattr(self, "source_type", None) is not None and self.source_type != "user_supplied":
        if user is not None and db_interface is not None:
          raise ValidationError("non user_supplied source_type cannot be an admin.")


class UllekhanamJsonObject(JsonObject):
  """The archetype JsonObject for use with the Ullekhanam project. See description.schema field"""

  schema = recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "description": "Some JsonObject which can be saved as a document in the ullekhanam database.",
    "properties": {
      "source": DataSource.schema,
      "editable_by_others": {
        "type": "boolean",
        "description": "Can this annotation be taken over by others for wiki-style editing or deleting?",
        "default": True
      },
      "targets": {
        "type": "array",
        "items": Target.schema,
        "description": "This field lets us define a directed graph involving JsonObjects stored in a database."
      }
    },
    "required": [TYPE_FIELD]
  }))

  target_class = Target

  def is_editable_by_others(self):
    # noinspection PyTypeChecker
    return self.editable_by_others if getattr(self, "editable_by_others", None) is not None else self.schema["properties"]["editable_by_others"]["default"]

  def __init__(self):
    super(UllekhanamJsonObject, self).__init__()
    self.source = DataSource()

  def detect_illegal_takeover(self, db_interface=None, user=None):
    if getattr(self, "_id", None) is not None and db_interface is not None:
      old_obj = JsonObject.from_id(id=self._id, db_interface=db_interface)
      if old_obj is not None and not old_obj.is_editable_by_others():
        if getattr(self.source, "id", None) is not None and getattr(old_obj.source, "id", None) is not None and self.source.id != old_obj.source.id:
          if user is not None and not user.is_admin(service=db_interface.db_name_frontend):
            raise ValidationError("{} cannot take over {}'s annotation for editing or deleting under a non-admin user {}'s authority".format(self.source.id, old_obj.source.id, user.get_first_user_id_or_none))

  def update_collection(self, db_interface, user=None):
    self.source.setup_source(db_interface=db_interface, user=user)
    return super(UllekhanamJsonObject, self).update_collection(db_interface=db_interface, user=user)

  def validate_deletion_ignoring_targetters(self, db_interface, user=None):
    super(UllekhanamJsonObject, self).validate_deletion(db_interface=db_interface, user=user)
    if user is not None:
      self.source.id = user.get_first_user_id_or_none()
    self.detect_illegal_takeover(db_interface=db_interface, user=user)

  def validate_deletion(self, db_interface, user=None):
    # Not calling: super(UllekhanamJsonObject, self).validate_deletion(db_interface=db_interface, user=user) as it's called inside the below.
    self.validate_deletion_ignoring_targetters(db_interface=db_interface, user=user)
    targetting_entities = self.get_targetting_entities(db_interface=db_interface)
    if len(targetting_entities) > 0:
      raise ValidationError("Unsafe deletion of %s: %d entities refer to this entity. Delete them first" % (self._id, len(targetting_entities)))

  @classmethod
  def get_allowed_target_classes(cls):
    return []

  def validate_targets(self, db_interface):
    allowed_types = self.get_allowed_target_classes()
    targets_to_check = self.targets if getattr(self, "targets", None) is not None else []
    Target.check_target_classes(targets_to_check=targets_to_check, db_interface=db_interface, allowed_types=allowed_types, targeting_obj=self)


  def validate(self, db_interface=None, user=None):
    super(UllekhanamJsonObject, self).validate(db_interface=db_interface, user=user)
    self.validate_targets(db_interface=db_interface)
    self.source.validate(db_interface=db_interface, user=user)
    self.detect_illegal_takeover(db_interface=db_interface, user=user)

  # noinspection PyTypeHints
  def get_targetting_entities(self, db_interface, entity_type=None):
    """

    :type entity_type: str
    """
    # Alas, the below shows that no index is used:
    # curl -sg vedavaapi.org:5984/vedavaapi_ullekhanam_db/_explain -H content-type:application/json -d '{"selector": {"targets": {"$elemMatch": {"container_id": "4b9f454f5aa5414e82506525d015ac68"}}}}'|jq
    # TODO: Use index.
    find_filter = {
      "targets": {
        "$elemMatch": {
          "container_id": str(self._id)
        }
      }
    }
    targetting_objs = [JsonObject.make_from_dict(item) for item in db_interface.find(find_filter)]
    if entity_type is not None:
      targetting_objs = list(filter(lambda obj: isinstance(obj, json_class_index[entity_type]), targetting_objs))
    return targetting_objs

  @classmethod
  def add_indexes(cls, db_interface):
    super(UllekhanamJsonObject, cls).add_indexes(db_interface=db_interface)
    db_interface.add_index(keys_dict={
      "targets.container_id": 1
    }, index_name="targets_container_id")


# noinspection PyProtectedMember,PyAttributeOutsideInit,PyAttributeOutsideInit,PyTypeChecker
class JsonObjectNode(JsonObject):
  """Represents a tree (not a general Directed Acyclic Graph) of UllekhanamJsonObject.

  `A video describing its use <https://youtu.be/neVeKcxzeQI>`_.
  """
  schema = recursively_merge_json_schemas(
    JsonObject.schema, {
      "$id": "JsonObjectNode",
      "properties": {
        TYPE_FIELD: {
          "enum": ["JsonObjectNode"]
        },
        "content": JsonObject.schema,
        "children": {
          "type": "array",
          "items": {
            'type': 'object',
            '$ref': "JsonObjectNode"
          }
        }
      },
      "required": [TYPE_FIELD]
    }
  )

  def setup_source(self, source):
    assert self.content is not None
    self.content.source = source
    for child in self.children:
      child.setup_source(source=source)

  def validate_children_types(self):
    """Recursively valdiate target-types."""
    for child in self.children:
      if not check_class(self.content, child.content.get_allowed_target_classes()):
        raise TargetValidationError(targeting_obj=child, allowed_types=child.content.get_allowed_target_classes(),
                                    target_obj=self.content)
    for child in self.children:
      child.validate_children_types()

  def validate(self, db_interface=None, user=None):
    super(JsonObjectNode, self).validate(db_interface=db_interface, user=user)
    self.validate_children_types()

  @classmethod
  def from_details(cls, content, children=None):
    if children is None:
      children = []
    node = JsonObjectNode()
    # logging.debug(content)
    # Strangely, without the backend.data_containers, the below test failed on 20170501
    node.content = content
    # logging.debug(check_list_item_types(children, [JsonObjectNode]))
    node.children = children
    node.validate(db_interface=None)
    return node

  def update_collection(self, db_interface, user=None):
    """Special info: Mutates this object."""
    # But we don't call self.validate() as child.content.targets (required of Annotations) mayn't be set.
    self.validate_children_types()
    # The content is validated within the below call.
    self.content = self.content.update_collection(db_interface=db_interface, user=user)
    for child in self.children:
      # Initialize the target array if it does not already exist.
      if (getattr(child.content, "targets", None) is None) or child.content.targets is None or len(child.content.targets) == 0:
        child.content.targets = [child.content.target_class()]

      assert len(child.content.targets) == 1
      child.content.targets[0].container_id = str(self.content._id)
      child.update_collection(db_interface=db_interface, user=user)

  def affected_user_ids(self):
    if getattr(self, "content", None) is None:
      raise ValidationError("This is a node with no content! Not allowed.")
    user_ids = []
    if getattr(self.content.source, "id", None) is not None:
      user_ids = [self.content.source.id]
    for child in self.children:
      user_ids = user_ids + child.affected_user_ids()
    return user_ids

  def validate_deletion(self, db_interface, user=None):
    # Deliberately not calling super.validate_deletion - the node does not exist in the database.
    if getattr(self, "content", None) is None:
      raise ValidationError("This is a node with no content! Not allowed.")
    self.content.validate_deletion_ignoring_targetters(db_interface=db_interface, user=user)
    for child in self.children:
      child.validate_deletion(db_interface=db_interface, user=user)
    self.content = JsonObject.from_id(id = self.content._id, db_interface=db_interface)
    affected_users = self.affected_user_ids()
    # logging.debug(affected_users)
    if len(set(affected_users)) > 2 and not user.is_admin(service=db_interface.db_name_frontend):
      raise ValidationError("This deletion affects more than 2 other users. Only admins can do that.")

  def delete_in_collection(self, db_interface, user=None):
    self.validate_deletion(db_interface=db_interface, user=user)
    self.fill_descendents(db_interface=db_interface, depth=100)
    for child in self.children:
      child.delete_in_collection(db_interface=db_interface, user=user)
    # Delete or disconnect children before deleting oneself.
    self.content.delete_in_collection(db_interface=db_interface, user=user)

  def fill_descendents(self, db_interface, depth=10, entity_type=None):
    targetting_objs = self.content.get_targetting_entities(db_interface=db_interface, entity_type=entity_type)
    self.children = []
    if depth > 0:
      for targetting_obj in targetting_objs:
        child = JsonObjectNode.from_details(content=targetting_obj)
        child.fill_descendents(db_interface=db_interface, depth=depth - 1, entity_type=entity_type)
        self.children.append(child)

  def recursively_delete_attr(self, field_name):
    """Rarely useful method: example when the schema of a Class changes to omit a field.

    Limitation: Only useful with direct members.
    """
    if getattr(self.content, field_name, None) is not None:
      delattr(self.content, field_name)
    for child in self.children:
      child.recursively_delete_attr(field_name)


class ScriptRendering(JsonObject):
  schema = recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["ScriptRendering"]
      },
      "text": {
        "type": "string",
      },
      "encoding_scheme": {
        "type": "string",
      },
    },
    "required": ["text"]
  }))

  @classmethod
  def from_details(cls, text, encoding_scheme=None):
    obj = ScriptRendering()
    obj.text = text
    if encoding_scheme is not None:
      obj.encoding_scheme = encoding_scheme
    obj.validate()
    return obj


class Text(JsonObject):
  schema = recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["Text"]
      },
      "script_renderings": {
        "type": "array",
        "minItems": 1,
        "items": ScriptRendering.schema
      },
      "language_code": {
        "type": "string",
      },
      "search_strings": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Search strings which should match this text. "
                       "It could be derived from script_renderings - "
                       "by a simple copy (intended for use with a text index) "
                       "or some intelligent tokenization thereof."
      },
    }
  }))

  @classmethod
  def from_details(cls, script_renderings, language_code=None):
    obj = Text()
    obj.script_renderings = script_renderings
    if language_code is not None:
      obj.language_code = language_code
    return obj

  @classmethod
  def from_text_string(cls, text_string, language_code=None, encoding_scheme=None):
    obj = Text()
    obj.script_renderings = [ScriptRendering.from_details(text=text_string, encoding_scheme=encoding_scheme)]
    if language_code is not None:
      obj.language_code = language_code
    return obj


class NamedEntity(JsonObject):
  """The same name written in different languages have different spellings - oft due to differing case endings and conventions: kAlidAsaH vs Kalidasa. Hence this container."""
  schema = recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["NamedEntity"]
      },
      "names": {
        "type": "array",
        "items": Text.schema,
        "minItems": 1
      }
    }
  }))

  @classmethod
  def from_details(cls, names):
    obj = NamedEntity()
    obj.names = names
    return obj

  @classmethod
  def from_name_string(cls, name, language_code=None, encoding_scheme=None):
    obj = NamedEntity()
    obj.names = [Text.from_text_string(text_string=name, language_code=language_code, encoding_scheme=encoding_scheme)]
    return obj


def get_schemas(module_in):
  import inspect
  schemas = {}
  for name, obj in inspect.getmembers(module_in):
    if inspect.isclass(obj) and getattr(obj, "schema", None) is not None:
      schemas[name] = obj.schema
  return schemas


# Essential for depickling to work.
update_json_class_index(sys.modules[__name__])
logging.debug(json_class_index)
