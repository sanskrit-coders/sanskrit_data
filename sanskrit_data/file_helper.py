import logging
import os
import subprocess
import urllib.request
from collections import OrderedDict
from urllib.error import HTTPError

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)
def deduce_format_from_filename(filename):
  format_hint = ".".join(filename.split(".")[1:])
  format_map = OrderedDict()
  format_map["json"] = "json"
  format_map["toml"] = "toml"
  for key, value in format_map.items():
    if key in format_hint:
      return value
  return None
