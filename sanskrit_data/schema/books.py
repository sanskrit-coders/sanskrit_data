"""
Intro
-----------

Here we define data-containers to store books. Books are stored or represented as a tree of BookPortion objects - book
containing many chapters containing many lines etc..

-  JSON schema mindmap
   `here <https://drive.mindmup.com/map?state=%7B%22ids%22:%5B%220B1_QBT-hoqqVbHc4QTV3Q2hjdTQ%22%5D,%22action%22:%22open%22,%22userId%22:%22109000762913288837175%22%7D>`__
   (Updated as needed).
- `An introductory video <https://youtu.be/bkd1pPL8HXk>`_.
- For general context and class diagram, refer to :mod:`~sanskrit_data.schema`.
"""
import logging
import sys

from sanskrit_data.schema import common
from sanskrit_data.schema.common import UllekhanamJsonObject, TYPE_FIELD, JsonObject, Target, DataSource, Text, \
  NamedEntity


class BookPositionTarget(Target):
  schema = common.recursively_merge_json_schemas(Target.schema, {
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["BookPositionTarget"]
      },
      "position": {
        "type": "number",
        "description": "Any number describing the position of one BookPortion within another."
      }
    }
  })

  @classmethod
  def from_details(cls, container_id=None, position=None):
    target = BookPositionTarget()
    if container_id:
      target.container_id = container_id
    if position:
      target.position = position
    target.validate(db_interface=None)
    return target


class PublicationDetails(JsonObject):
  schema = common.recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "description": "Publication details of a BookPortion.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["PublicationDetails"]
      },
      "release_time": {
        "type": "string"
      },
      "publisher": NamedEntity.schema,
      "canonical_source": {
        "type": "string",
      },
      "issue_page": {
        "type": "string",
      },
    }
  }))


class CreationDetails(NamedEntity):
  """Many names are possible for the same work (eg. meghasandeshaH vs meghadUtam) - hence we extend the NamedEntity schema."""
  schema = common.recursively_merge_json_schemas(NamedEntity.schema, ({
    "type": "object",
    "properties": {
      TYPE_FIELD: {
        "enum": ["CreationDetails"]
      },
      "authors": {
        "type": "array",
        "items": NamedEntity.schema
      }
    }
  }))

  @classmethod
  def from_details(cls, names, authors=None):
    obj = CreationDetails()
    obj.names = names
    if authors is not None:
      obj.authors = authors
    return obj


class BookPortion(UllekhanamJsonObject):
  schema = common.recursively_merge_json_schemas(JsonObject.schema, ({
    "type": "object",
    "description": "A BookPortion could represent a Book or a chapter or a verse or a half-verse or a sentence or any such unit.",
    "properties": {
      TYPE_FIELD: {
        "enum": ["BookPortion"]
      },
      "creation_details": CreationDetails.schema,
      "path": {
        "type": "string",
        "description": "The path prefix where files are to be stored. "
                       "If this field is empty, such a path is computed from _id of this object "
                       "and its ancestors. "
                       "Ideally, the value stored here should equal the result of this computation "
                       "- but it may not be the case, especially in the following cases: "
                       "* Imported books "
                       "* Moved BookPortions. "
                       " Once upon a time this field also uniquely identified a BookPortion."
      },
      "thumbnail_path": {
        "type": "string"
      },
      "base_data": {
        "type": "string",
        "enum": ["image", "text"]
      },

      # naming the field that contains this object `source` to make querying uniform (ref Annotation.source).
      "source": DataSource.schema,
      "publication_details": PublicationDetails.schema,
      "portion_class": {
        "type": "string",
        "description": "book, part, chapter, verse, line etc.."
      },
      "curated_content": Text.schema,
      "editable_by_others": {
        "default": False
      },
      "targets": {
        "maxLength": 1,
        "items": BookPositionTarget.schema,
        "description": (
          "Target for BookPortion of which this BookPortion is a part. It is an array only for consistency. "
          "For any given BookPortion, one can get the right order of contained BookPortions by seeking all "
          "BookPortions referring to it in the targets list, and sorting them by their target.position values.")
      }
    },
  }))

  target_class = BookPositionTarget

  @classmethod
  def get_allowed_target_classes(cls):
    return [BookPortion]

  @classmethod
  def from_details(cls, title, path=None, authors=None, targets=None, base_data=None,
                   curated_content=None, portion_class=None, publication_details=None, source=None):
    if authors is None:
      authors = []
    book_portion = BookPortion()
    book_portion.title = title
    book_portion.authors = authors
    # logging.debug(str(book_portion))
    if path:
      book_portion.path = path

    targets = targets or []
    logging.debug(str(book_portion))
    book_portion.targets = targets
    if curated_content is not None:
      book_portion.curated_content = curated_content
    if base_data is not None:
      book_portion.base_data = base_data
    if portion_class is not None:
      book_portion.portion_class = portion_class
    if publication_details is not None:
      book_portion.publication_details = publication_details
    if source is not None:
      book_portion.source = source
    book_portion.validate()
    return book_portion

  @classmethod
  def from_path(cls, path, db_interface):
    book_portion_dict = db_interface.find_one(find_filter={"path": path})
    if book_portion_dict is None:
      return None
    else:
      book_portion = JsonObject.make_from_dict(book_portion_dict)
      return book_portion

  @classmethod
  def add_indexes(cls, db_interface):
    super(BookPortion, cls).add_indexes(db_interface=db_interface)
    db_interface.add_index(keys_dict={
      "creation_details.names.script_renderings.text": 1
    }, index_name="creation_details_names_script_renderings_text")
    db_interface.add_index(keys_dict={
      "creation_details.authors.names.script_renderings.text": 1
    }, index_name="creation_details_authors_names_script_renderings_text")
    db_interface.add_index(keys_dict={
      "curated_content.script_renderings.text": 1
    }, index_name="curated_content_script_renderings_text")

    db_interface.add_index(keys_dict={
      "creation_details.names.search_strings": 1
    }, index_name="creation_details_names_search_strings")
    db_interface.add_index(keys_dict={
      "creation_details.authors.names.search_strings": 1
    }, index_name="creation_details_authors_names_search_strings")
    db_interface.add_index(keys_dict={
      "curated_content.search_strings": 1
    }, index_name="curated_content_search_strings")

  def get_path(self, db_interface):
    external_file_store = db_interface.external_file_store
    import os
    if getattr(self, "path", None) is not None:
      return os.path.join(external_file_store, self.path)
    elif getattr(self, "targets", None) is not None and len(self.targets) > 0:
      container_book = self.targets[0]
      return os.path.join(external_file_store, container_book.get_path(db_interface=db_interface), self._id)

  def dump_book_portion(self, export_dir, db_interface):
    import os
    book_node = common.JsonObjectNode.from_details(content=self)
    book_node.fill_descendents(db_interface=db_interface, entity_type="BookPortion")
    export_dir_destination = os.path.join(export_dir, self._id)
    if self.portion_class == "book":
      import copy
      copied_node = copy.deepcopy(book_node)
      copied_node.recursively_delete_attr(field_name="path")
      copied_node.dump_to_file(filename=os.path.join(export_dir_destination, "book.json"))
    elif self.portion_class == "page":
      # Just dump the file.
      import shutil
      # TODO: Remove this branch once data migration is done.
      if getattr(self, "path", None) is not None:
        src_file = self.path
        # noinspection PyArgumentList
        os.makedirs(name=export_dir_destination, exist_ok=True)
        shutil.copyfile(os.path.join(db_interface.external_file_store, src_file), os.path.join(export_dir_destination, "content" + os.path.splitext( os.path.basename(src_file))[1]))
      else:
        for f in self.list_files(db_interface=db_interface):
          # noinspection PyArgumentList
          os.makedirs(name=export_dir_destination, exist_ok=True)
          shutil.copyfile(os.path.join(self.get_external_storage_path(db_interface=db_interface), f), os.path.join(export_dir_destination, os.path.basename(f)))

    for sub_portion in book_node.children:
      sub_portion.content.dump_book_portion(export_dir=export_dir, db_interface=db_interface)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
