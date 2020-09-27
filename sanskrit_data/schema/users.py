"""
Intro
-----

- For general context and class diagram, refer to :mod:`~sanskrit_data.schema`.


"""
import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject, recursively_merge_json_schemas, TYPE_FIELD, update_json_class_index

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class UserPermission(JsonObject):
  schema = recursively_merge_json_schemas(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["UserPermission"]
        },
        "service": {
          "type": "string",
          "description": "Allowable values should be predetermined regular expressions."
        },
        "actions": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["read", "write", "admin"],
          },
          "description": "Should be an enum in the future."
        },
      },
    }
  )

  @classmethod
  def from_details(cls, service, actions):
    obj = UserPermission()
    obj.service = service
    obj.actions = actions
    return obj


def hash_password(plain_password):
  import bcrypt
  #   (Using bcrypt, the salt is saved into the hash itself)
  return bcrypt.hashpw(plain_password.encode(encoding='utf8'), bcrypt.gensalt()).decode(encoding='utf8')


class AuthenticationInfo(JsonObject):
  schema = recursively_merge_json_schemas(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["AuthenticationInfo"]
        },
        "auth_user_id": {
          "type": "string"
        },
        "auth_provider": {
          "type": "string",
          "enum": ["google", "vedavaapi"]
        },
        "auth_secret_bcrypt": {
          "type": "string",
          "description": "This should be hashed, and merits being stored in a database."
        },
        "auth_secret_plain": {
          "type": "string",
          "description": "This should NEVER be set when stored in a database; but is good for client-server transmission purposes."
        }
      }
    }
  )

  VEDAVAAPI_AUTH = "vedavaapi"

  def __str__(self):
    return self.auth_provider + "____" + self.auth_user_id

  def check_password(self, plain_password):
    # Check hased password. Using bcrypt, the salt is saved into the hash itself
    import bcrypt
    return bcrypt.checkpw(plain_password.encode(encoding='utf8'), self.auth_secret_bcrypt.encode(encoding='utf8'))

  @classmethod
  def from_details(cls, auth_user_id, auth_provider, auth_secret_hashed=None):
    obj = AuthenticationInfo()
    obj.auth_user_id = auth_user_id
    obj.auth_provider = auth_provider
    if auth_secret_hashed:
      obj.auth_secret_hashed = auth_secret_hashed
    return obj

  def set_bcrypt_password(self):
    if getattr(self, "auth_secret_plain", None) is not None and self.auth_secret_plain != "":
      # noinspection PyAttributeOutsideInit
      self.auth_secret_bcrypt = hash_password(plain_password=self.auth_secret_plain)
      delattr(self, "auth_secret_plain")

  def validate_schema(self):
    super(AuthenticationInfo, self).validate_schema()
    from jsonschema import ValidationError
    self.set_bcrypt_password()
    if getattr(self, "auth_secret_hashed", None) is not None and (self.auth_secret_hashed == ""):
      raise ValidationError(message="auth_secret_hashed should be non-empty if present.")


class User(JsonObject):
  """Represents a user of our service."""
  schema = recursively_merge_json_schemas(
    JsonObject.schema, {
      "properties": {
        TYPE_FIELD: {
          "enum": ["User"]
        },
        "user_type": {
          "type": "string",
          "enum": ["human", "bot"]
        },
        "authentication_infos": {
          "type": "array",
          "items": AuthenticationInfo.schema,
        },
        "permissions": {
          "type": "array",
          "items": UserPermission.schema,
        },
      },
    }
  )

  @classmethod
  def from_details(cls, user_type, auth_infos, permissions=None):
    obj = User()
    obj.authentication_infos = auth_infos
    obj.user_type = user_type
    if permissions:
      obj.permissions = permissions
    return obj

  def validate_schema(self):
    super(User, self).validate_schema()

  def check_permission(self, service, action):
    def fullmatch(pattern, string, flags=0):
      """Emulate python-3.4 re.fullmatch()."""
      import re
      return re.match("(?:" + pattern + r")\Z", string, flags=flags)

    if getattr(self, "permissions", None) is not None:
      for permission in self.permissions:
        if fullmatch(pattern=permission.service, string=service):
          for permitted_action in permission.actions:
            if fullmatch(pattern=permitted_action, string=action):
              return True
    return False

  def is_admin(self, service):
    return self.check_permission(service=service, action="admin")

  def is_human(self):
    return getattr(self, "user_type", None) is not None and self.user_type == "human"

  def get_user_ids(self):
    return [str(auth_info) for auth_info in self.authentication_infos]

  def get_first_user_id_or_none(self):
    user_ids = self.get_user_ids()
    if len(user_ids) > 0:
      return user_ids[0]
    else:
      return None

    # Essential for depickling to work.


update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
