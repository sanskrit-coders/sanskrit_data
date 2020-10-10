# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import sys

import pytest

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

class DummySubClass(DummyClass):
    def __init__(self):
        super(DummyClass, self).__init__()


class DummyClass2(common.JsonObject):
    def __init__(self, field1):
        super(DummyClass2, self).__init__()
        self.field1 = field1

json_class_index = {}
common.update_json_class_index(sys.modules[__name__], json_class_index_in=json_class_index)
logging.debug("json_class_index " + json_class_index.__str__())


def test_json_serialization(caplog):
    caplog.set_level(logging.DEBUG)

    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_round_trip_serialization.json.local")
    test_obj = DummyClass.from_details(field1=21, field2 = {"2.1": DummyClass2(field1=1)})
    test_obj.dump_to_file(filename=tmp_file_path)
    test_obj_2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index)
    assert test_obj.field1 == test_obj_2.field1
    assert test_obj.__str__() == test_obj_2.__str__()
    assert isinstance(test_obj_2.field2["2.1"], DummyClass2)

    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_round_trip_serialization.toml.local")
    test_obj = DummyClass.from_details(field1=21, field2 = {"2.1": DummyClass2(field1=1)})
    test_obj.dump_to_file(filename=tmp_file_path)
    test_obj_2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index)
    assert test_obj.field1 == test_obj_2.field1
    assert test_obj.__str__() == test_obj_2.__str__()



def test_return_none_by_default(caplog):
    caplog.set_level(logging.DEBUG)
    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_none_value.json")
    with pytest.raises(AttributeError):
        test_obj_2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index, default_to_none=False)
        assert test_obj_2.field2 == None
    test_obj_2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index, default_to_none=True)
    assert test_obj_2.field2 == None


def test_serialization_omit_nones(caplog):
    caplog.set_level(logging.DEBUG)
    tmp_file_path = os.path.join(TEST_DATA_DIR, "test_none_value.json")
    test_obj_2 = JsonObject.read_from_file(filename=tmp_file_path, name_to_json_class_index_extra=json_class_index, default_to_none=True)
    test_obj_2.field3 = None
    test_obj_2_map = test_obj_2.to_json_map()
    assert "field3" not in test_obj_2_map
