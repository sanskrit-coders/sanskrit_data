import logging
import os

from sanskrit_data.db.interfaces import InMemoryDb


def ullekhanam_db_fixture(request):
    test_db = InMemoryDb(external_file_store=os.path.join(os.path.durname(__file__), "textract-example-repo/books"))

    def db_teardown():
        logging.info("deleting db")
    request.addfinalizer(db_teardown)
    return test_db
