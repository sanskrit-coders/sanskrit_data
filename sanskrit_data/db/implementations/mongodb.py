""".. note:: For undocumented classes and methods, please see superclass documentation in :mod:`sanskrit_data.db`."""

import logging

# noinspection PyPackageRequirements
from bson import ObjectId

from sanskrit_data.db.interfaces import ClientInterface, DbInterface
from sanskrit_data.db.interfaces.ullekhanam_db import BookPortionsInterface
from sanskrit_data.db.interfaces.users_db import UsersInterface

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def get_db_collection_names(db_collection_string):
    """
  
    :param db_collection_string: A string like someDb.someCollection or just someCollection, which is interpreted as someCollection.someCollection.
    :return: An object with db and collection names.
    """
    name_parts = db_collection_string.split(".")
    assert len(name_parts) > 0
    obj = {"db": name_parts[0],
           "collection": name_parts[0],
           }
    if len(name_parts) == 2:
        obj["collection"] = name_parts[1]
    return obj


class Collection(DbInterface):
    def __init__(self, some_collection, db_name_frontend, external_file_store=None):
        logging.info("Initializing collection :" + str(some_collection))
        self.mongo_collection = some_collection
        self.db_name_frontend = db_name_frontend
        self.external_file_store = external_file_store
        self.init_external_file_store()

    # noinspection PyShadowingBuiltins
    def find_by_id(self, id):
        return self.find_one(find_filter={"_id": id})

    def find_one(self, find_filter):
        _fix_id_filter(filter_dict=find_filter)
        result = self.mongo_collection.find_one(filter=find_filter)
        _fix_id(doc=result)
        return result

    def find(self, find_filter):
        results = self.mongo_collection.find(find_filter)
        for result in results:
            _fix_id(doc=result)
            yield result

    def update_doc(self, doc):
        from pymongo import ReturnDocument
        if "_id" in doc:
            filter_dict = {"_id": ObjectId(doc["_id"])}
            doc.pop("_id", None)
        else:
            filter_dict = doc
        updated_doc = self.mongo_collection.find_one_and_update(filter_dict, {"$set": doc}, upsert=True,
                                                                return_document=ReturnDocument.AFTER)
        _fix_id(doc=updated_doc)
        return updated_doc

    def delete_doc(self, doc_id):
        self.mongo_collection.delete_one({"_id": ObjectId(doc_id)})

    def add_index(self, keys_dict, index_name):
        self.mongo_collection.create_index(keys=list(keys_dict.items()), name=index_name, background=True)


def _fix_id(doc):
    if doc is not None and "_id" in doc:
        doc["_id"] = str(doc["_id"])


def _fix_id_filter(filter_dict):
    if "_id" in filter_dict:
        filter_dict["_id"] = ObjectId(filter_dict["_id"])


class BookPortionsMongodb(Collection, BookPortionsInterface):
    def __init__(self, some_collection, db_name_frontend, external_file_store=None):
        super(BookPortionsMongodb, self).__init__(some_collection=some_collection, db_name_frontend=db_name_frontend,
                                                  external_file_store=external_file_store)


class UsersMongodb(Collection, UsersInterface):
    def __init__(self, some_collection, db_name_frontend="users"):
        super(UsersMongodb, self).__init__(some_collection=some_collection, db_name_frontend=db_name_frontend)


class Client(ClientInterface):
    def __init__(self, url):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(host=url)
        except Exception as e:
            logging.error("Error initializing MongoDB database; aborting.")
            raise e

    def get_database(self, db_name):
        db_details = get_db_collection_names(db_collection_string=db_name)
        return self.client[db_details["db"]][db_details["collection"]]

    def get_database_interface(self, db_name_backend, db_name_frontend=None, external_file_store=None, db_type=None):
        db_name_frontend_final = db_name_frontend if db_name_frontend is not None else db_name_backend
        if db_type == "ullekhanam_db":
            return BookPortionsMongodb(some_collection=self.get_database(db_name=db_name_backend),
                                       db_name_frontend=db_name_frontend_final, external_file_store=external_file_store)
        elif db_type == "users_db":
            db_name_frontend_final = db_name_frontend if db_name_frontend is not None else "users"
            return UsersMongodb(some_collection=self.get_database(db_name=db_name_backend),
                                db_name_frontend=db_name_frontend_final)
        else:
            return Collection(some_collection=self.get_database(db_name=db_name_backend),
                              db_name_frontend=db_name_frontend_final, external_file_store=external_file_store)

    def delete_database(self, db_name):
        """Deletes a collection, does not bother with the database."""
        db_details = get_db_collection_names(db_collection_string=db_name)
        self.client[db_details["db"]].drop_collection(db_details["collection"])
