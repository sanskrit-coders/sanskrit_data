# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


# Used in the tests below
class DummyClass(common.JsonObject):
    def __init__(self):
        super(DummyClass, self).__init__()
        self.field1 = None
        self.field2 = None
    
    @classmethod
    def from_details(self, field1=None, field2=None):
      x = DummyClass()
      x.field1 = field1
      x.field2 = field2
      return x

class DummyClass2(common.JsonObject):
    def __init__(self, field1):
        super(DummyClass2, self).__init__()
        self.field1 = field1

json_class_index = {}
common.update_json_class_index(sys.modules[__name__], json_class_index=json_class_index)
logging.debug("json_class_index " + json_class_index.__str__())


def test_serialization(caplog):
    caplog.set_level(logging.DEBUG)
    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_round_trip_serialization.json.local")
    testObj = DummyClass.from_details(field1=21, field2 = {"2.1": DummyClass2(field1=1)})
    testObj.dump_to_file(filename=tmp_file_path)
    testObj2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index)
    assert testObj.field1 == testObj2.field1
    assert testObj.__str__() == testObj2.__str__()
    assert isinstance(testObj2.field2["2.1"], DummyClass2)

    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_none_value.json")
    testObj2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index)
    # assert testObj2.field2 == None
