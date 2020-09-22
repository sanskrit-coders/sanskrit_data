import logging
import string

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class ClientInterface(object):
  """A common interface to a database server or system.

  Accessing databases through implementations of this interface enables one to switch databases more easily down the line.
  """

  def get_database(self, db_name):
    """Create or get a database, with which one can instantiate a suitable DbInterface subclass.

    While it is better to use :meth:`get_database_interface` generally, we expose this in order to support :class:`DbInterface` subclasses which may be defined outside this module.
    :param str db_name: Name of the database which needs to be accessed (The database is created if it does not already exist).
    :returns DbInterface db: A database interface implementation for accessing this database.
    """
    pass

  def get_database_interface(self, db_name_backend, db_name_frontend=None, external_file_store=None, db_type=None):
    """Create or get a suitable :class:`DbInterface` subclass.

    :param db_name_frontend: An ID for use with the schema.users module, to verify user access to the database as needed.
    :param str db_name_backend: Name of the database which needs to be accessed (The database is created if it does not already exist).
    :param external_file_store:
    :param db_type:
    :returns DbInterface db: A database interface implementation for accessing this database.
    """
    pass

  def delete_database(self, db_name):
    """Delete a database, with which one can instantiate a suitable DbInterface subclass.

    :param str db_name: Name of the database which needs to be deleted.
    """
    pass


class DbInterface(object):
  """A common interface to a database.

  Accessing databases through implementations of this interface enables one to switch databases more easily down the line.
  """

  def __init__(self, db_name_frontend, external_file_store):
    self.db_name_frontend = db_name_frontend
    self.external_file_store = external_file_store
    self.init_external_file_store()

  def init_external_file_store(self):
    # Add filestores for use with the DB.
    if self.external_file_store is not None:
      logging.info("Initializing work directory ...")
      import os
      # noinspection PyArgumentList
      os.makedirs(name=self.external_file_store, exist_ok=True)

  def update_doc(self, doc):
    """ Update or insert a json object, represented as a dict.

    Where possible, use wrapper methods like :py:meth:`~sanskrit_data.schema.common.JsonObject.update_collection` since they do validation and other setup to ensure data consistency.

    :param db_name_frontend:
    :param dict doc: _id parameter determines the key. One will be created if it does not exist. This argument could be modified.
    :return: updated dict with _id set.
    """
    assert isinstance(doc, dict)
    pass

  def delete_doc(self, doc_id):
    """

    Where possible, use wrapper methods like :py:meth:`~sanskrit_data.schema.common.JsonObject.delete_in_collection` since they do validation.
    :param doc_id:
    :return: Not used.
    """
    pass

  # noinspection PyShadowingBuiltins
  def find_by_id(self, id):
    """

    :param id:
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find(self, find_filter):
    """ Find matching objects from the database.

    Should be a generator and return an iterator: ie it should use the yield keyword.

    :param dict find_filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    pass

  def find_one(self, find_filter):
    """ Fine one matching object from the database.

    :param find_filter: A mango or mongo query.
    :return: Returns None if nothing is found. Else a python dict representing a JSON object.
    """
    return next(self.find(find_filter=find_filter), None)

  def update_index(self, name, fields, upsert=False):
    """Create or update (if upsert=True) an index over certain fields, with a given name."""
    pass

  def add_index(self, keys_json, index_name):
    """Index the database using certain fields.

    :param index_name:
    :param keys_json: A document that contains the field and value pairs where the field is the index key and the value describes the type of index for that field. For an ascending index on a field, specify a value of 1; for descending index, specify a value of -1.
    """
    pass


def get_random_string(length):
  letters = string.ascii_lowercase
  import random
  result_str = ''.join(random.choice(letters) for i in range(length))
  return result_str
