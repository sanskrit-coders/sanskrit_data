# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging

import jsonschema
import pytest

import tests
import tests.db
from sanskrit_data.schema import ullekhanam, common, books, users

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

@pytest.fixture(scope='module')
def db_fixture(request):
  return tests.db.ullekhanam_db_fixture(request=request)



def make_tree():
  node = common.JsonObjectNode.from_details(content=books.BookPortion.from_details(
    title="halAyudhakoshaH"), children=[
    common.JsonObjectNode.from_details(content=books.BookPortion.from_details(
      title="c1"), children=[
      common.JsonObjectNode.from_details(content=books.BookPortion.from_details(
        title="c1v1"))
    ])
  ])
  node.content.editable_by_others = True
  node.children[0].content.editable_by_others = True
  node.children[0].children[0].content.editable_by_others = True
  return node


def test_update_validation(db_fixture):
  db = db_fixture
  node = make_tree()
  non_admin_user_raama = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="rAma")])
  with pytest.raises(jsonschema.ValidationError) as exception_info:
    node.update_collection(db_interface=db, user=non_admin_user_raama)
  assert exception_info.value.message.startswith("Impersonation by {}".format(non_admin_user_raama.get_first_user_id_or_none()))
  # The below should succeed.
  node.update_collection(db_interface=db)


def test_deletion_validation_general(db_fixture):
  db = db_fixture
  node = make_tree()
  non_admin_user_raama = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="rAma")])
  non_admin_user_siitaa = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="sItA")])
  node.update_collection(db_interface=db)
  node.children[0].content.source = common.DataSource.from_details(source_type="user_supplied", id=non_admin_user_raama.get_first_user_id_or_none())
  node.children[0].content.editable_by_others = False
  node.children[0].content = node.children[0].content.update_collection(db_interface=db, user=non_admin_user_raama)

  with pytest.raises(jsonschema.ValidationError) as exception_info:
    node.delete_in_collection(db_interface=db, user=non_admin_user_siitaa)
  assert exception_info.value.message.startswith("vingo____sItA cannot take over vingo____rAma's annotation for editing or deleting under a non-admin user")
  # The below should succeed.
  node.delete_in_collection(db_interface=db, user=non_admin_user_raama)


def test_deletion_validation_affect_too_many_users(db_fixture):
  db = db_fixture
  node = make_tree()
  non_admin_user_raama = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="rAma")])
  non_admin_user_siitaa = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="sItA")])
  non_admin_user_laxmaNa = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="laxmaNa")])
  non_admin_user_vibhiiShana = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="vibhiiShana")])
  node.update_collection(db_interface=db)
  node.content.source = common.DataSource.from_details(source_type="user_supplied", id=non_admin_user_vibhiiShana.get_first_user_id_or_none())
  node.content = node.content.update_collection(db_interface=db, user=non_admin_user_vibhiiShana)
  node.children[0].content.source = common.DataSource.from_details(source_type="user_supplied", id=non_admin_user_raama.get_first_user_id_or_none())
  node.children[0].content = node.children[0].content.update_collection(db_interface=db, user=non_admin_user_raama)
  node.children[0].children[0].content.source = common.DataSource.from_details(source_type="user_supplied", id=non_admin_user_laxmaNa.get_first_user_id_or_none())
  node.children[0].children[0].content = node.children[0].children[0].content.update_collection(db_interface=db, user=non_admin_user_laxmaNa)

  with pytest.raises(jsonschema.ValidationError) as exception_info:
    node.delete_in_collection(db_interface=db, user=non_admin_user_siitaa)
  assert exception_info.value.message.startswith("This deletion affects more than 2 other users.")


def test_fill_descendents(db_fixture):
  node = make_tree()
  node.update_collection(db_interface=db_fixture)
  logging.debug(node)
  target_page_id = node.children[0].children[0].content._id
  annotation = ullekhanam.ImageAnnotation()
  annotation.targets=[
    ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                        rectangle=ullekhanam.Rectangle.from_details())]
  annotation.update_collection(db_interface=db_fixture)
  top_node = node
  top_node.children = None
  top_node.fill_descendents(db_interface=db_fixture, entity_type="BookPortion")
  assert "Annotation" not in str(top_node)
