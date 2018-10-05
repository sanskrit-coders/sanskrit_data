import logging
logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


from sanskrit_data.schema import common


class RootAnalysis(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "description": "Analysis of any root.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["RootAnalysis"]
      },
      "root": "string",
      "pratyayas": {
        "type": "array",
        "item": "string"
      },
    },
  }))


class Praatipadika(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "description": "A prAtipadika.",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["Praatipadika"]
      },
      "root": "string",
      "prakaara": "string",
      "linga": "string",
      "rootAnalysis": RootAnalysis.schema,
    },
  }))


