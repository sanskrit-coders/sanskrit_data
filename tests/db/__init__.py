import logging
import os

from sanskrit_data.db import in_memory


def ullekhanam_db_fixture(request):
    test_db = in_memory.BookPortionsInMemory(db_name_frontend="ullekhanam", external_file_store=os.path.join(os.path.dirname(__file__),  "textract-example-repo/books"))

    def db_teardown():
        logging.info("deleting db")
    request.addfinalizer(db_teardown)
    return test_db


def users_db_fixture(request):
    test_db = in_memory.UsersInMemory(db_name_frontend="users", external_file_store=None)

    def db_teardown():
        logging.info("deleting db")
    request.addfinalizer(db_teardown)
    return test_db
