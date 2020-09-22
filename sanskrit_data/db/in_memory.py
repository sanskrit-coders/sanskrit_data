from sanskrit_data.db.interfaces import DbInterface, get_random_string, users_db, ullekhanam_db
from sanskrit_data.schema.common import JsonObject


class InMemoryDb(DbInterface):
  def __init__(self, db_name_frontend, external_file_store=None):
    super(InMemoryDb, self).__init__(external_file_store=external_file_store, db_name_frontend=db_name_frontend)
    self.db = {}

  # noinspection PyShadowingBuiltins
  def find_by_id(self, id):
    return self.db.get(id, None)

  def find(self, find_filter):
    for index, key in enumerate(self.db):
      if JsonObject.make_from_dict(self.db[key]).match_filter(find_filter=find_filter):
          yield self.db[key]

  def update_doc(self, doc):
    if not "_id" in doc:
      doc["_id"] = get_random_string(8)
    self.db[doc["_id"]] = doc
    return doc

  def delete_doc(self, doc_id):
    self.db.pop(doc_id)


class BookPortionsInMemory(InMemoryDb, ullekhanam_db.BookPortionsInterface):
    def __init__(self, db_name_frontend, external_file_store=None):
        super(BookPortionsInMemory, self).__init__(db_name_frontend=db_name_frontend,
                                                   external_file_store=external_file_store)


class UsersInMemory(InMemoryDb, users_db.UsersInterface):
    def __init__(self, db_name_frontend, external_file_store=None):
        super(UsersInMemory, self).__init__(db_name_frontend=db_name_frontend,
                                                   external_file_store=external_file_store)
