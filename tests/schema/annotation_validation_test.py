# -*- coding: utf-8 -*-
"""
Tests for the ullekhanam_db interface and the associated schema classes.
"""

from __future__ import absolute_import

import logging
import os
import pytest
import jsonschema
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


def test_ImageAnnotation_source_auto_set(db_fixture):
    db = db_fixture
    book_portion = books.BookPortion.from_details(
        title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
    updated_book = book_portion.update_collection(db)
    target_page_id = updated_book._id
    annotation = ullekhanam.ImageAnnotation()
    annotation.targets=[
        ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                            rectangle=ullekhanam.Rectangle.from_details())]

    # logging.debug(annotation.to_json_map())

    updated_annotation = annotation.update_collection(db_interface=db)
    # logging.debug("update result is " + str(updated_annotation))
    assert(updated_annotation.source.get_wire_typeid() == "DataSource")


def test_ImageAnnotation_take_over_while_editing(db_fixture):
    db = db_fixture
    book_portion = books.BookPortion.from_details(
        title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
    updated_book = book_portion.update_collection(db)
    target_page_id = updated_book._id
    non_admin_user_raama = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="rAma")])
    annotation = ullekhanam.ImageAnnotation.from_details(targets=[
        ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                            rectangle=ullekhanam.Rectangle.from_details())],
        source=ullekhanam.DataSource.from_details("user_supplied", non_admin_user_raama.get_first_user_id_or_none()))

    logging.debug(annotation.to_json_map())

    # Write as admin program impersonating rAma
    updated_annotation_1 = annotation.update_collection(db_interface=db)

    # By default: updated_annotation_1.editable_by_others = True
    non_admin_user_siitaa = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="sItA")])
    updated_annotation_1.source.id = non_admin_user_siitaa.get_first_user_id_or_none()

    # The below will only affect future writes, not this update.
    updated_annotation_1.editable_by_others = False
    updated_annotation_2 = updated_annotation_1.update_collection(db_interface=db, user=non_admin_user_siitaa)

    with pytest.raises(jsonschema.ValidationError) as exception_info:
        updated_annotation_2.source.id = non_admin_user_raama.get_first_user_id_or_none()
        updated_annotation_3 = updated_annotation_2.update_collection(db_interface=db, user=non_admin_user_raama)
    assert exception_info.value.message.startswith("{} cannot take over {}'s annotation for editing or deleting under a non-admin user".format(non_admin_user_raama.get_first_user_id_or_none(), non_admin_user_siitaa.get_first_user_id_or_none()))


def test_ImageAnnotation_take_over_while_deleting(db_fixture):
    db = db_fixture
    book_portion = books.BookPortion.from_details(
        title="halAyudhakoshaH", authors=["halAyudhaH"], path="myrepo/halAyudha")
    updated_book = book_portion.update_collection(db)
    target_page_id = updated_book._id
    non_admin_user_raama = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="rAma")])
    non_admin_user_siitaa = users.User.from_details(user_type="human", auth_infos=[users.AuthenticationInfo.from_details(auth_provider="vingo", auth_user_id="sItA")])
    annotation = ullekhanam.ImageAnnotation.from_details(targets=[
        ullekhanam.ImageTarget.from_details(container_id=str(target_page_id),
                                            rectangle=ullekhanam.Rectangle.from_details())],
        source=ullekhanam.DataSource.from_details("user_supplied", non_admin_user_raama.get_first_user_id_or_none()))

    logging.debug(annotation.to_json_map())

    # Write as rAma
    updated_annotation_1 = annotation.update_collection(db_interface=db, user=non_admin_user_raama)
    # Delete as sItA
    updated_annotation_1.delete_in_collection(db_interface=db, user=non_admin_user_siitaa)

    # Make read-only-by-others, Write as rAma
    annotation.editable_by_others = False
    updated_annotation_1 = annotation.update_collection(db_interface=db, user=non_admin_user_raama)

    with pytest.raises(jsonschema.ValidationError) as exception_info:
        # Delete as sItA
        updated_annotation_1.delete_in_collection(db_interface=db, user=non_admin_user_siitaa)
    assert exception_info.value.message.startswith("{} cannot take over {}'s annotation for editing or deleting under a non-admin user".format(non_admin_user_siitaa.get_first_user_id_or_none(), non_admin_user_raama.get_first_user_id_or_none()))
