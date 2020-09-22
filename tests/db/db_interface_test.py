from __future__ import absolute_import

import logging
import unittest

import tests
from sanskrit_data.db.interfaces import InMemoryDb
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class TestDBRoundTrip(unittest.TestCase):

  def setUp(self):
    tests.set_configuration()
    self.test_db = InMemoryDb()

  def tearDown(self):
    pass

  def test_update_doc(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    updated_doc["xyz"] = "xyzvalue"
    updated_doc = self.test_db.update_doc(updated_doc)
    logging.debug(updated_doc)
    self.assertNotEqual(updated_doc, None)
    self.assertEqual("xyz" in updated_doc, True)
    updated_doc = self.test_db.find_by_id(updated_doc["_id"])
    self.assertNotEqual(updated_doc, None)


  def test_delete_doc_find_by_id(self):
    doc = JsonObject()
    updated_doc = self.test_db.update_doc(doc.to_json_map())
    logging.debug(updated_doc)
    doc_id = updated_doc["_id"]
    self.test_db.delete_doc(doc_id)
    self.assertEqual(self.test_db.find_by_id(doc_id), None)


if __name__ == '__main__':
  unittest.main()