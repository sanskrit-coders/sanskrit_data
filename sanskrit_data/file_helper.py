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


# noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
def convert(value):
  B = float(value)
  KB = float(1024)
  MB = float(KB ** 2)
  GB = float(KB ** 3)
  TB = float(KB ** 4)
  if B < KB:
    return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'B')
  if KB <= B < MB:
    return '{0:.2f} KB'.format(B / KB)
  if MB <= B < GB:
    return '{0:.2f} MB'.format(B / MB)
  if GB <= B < TB:
    return '{0:.2f} GB'.format(B / GB)


def list_dirtree(rootdir):
  all_data = []
  try:
    contents = os.listdir(rootdir)
  except Exception as e:
    logging.error("Error listing " + rootdir + ": " + str(e))
    return all_data
  else:
    for item in contents:
      itempath = os.path.join(rootdir, item)
      info = {}
      children = []
      if os.path.isdir(itempath):
        all_data.append(
          dict(title=item,
               path=itempath,
               folder=True,
               lazy=True,
               key=itempath))
      else:
        fsize = os.path.getsize(itempath)
        fsize = convert(fsize)
        fstr = '[' + fsize + ']'
        all_data.append(dict(title=item + ' ' + fstr, key=itempath))
  return all_data


def deduce_format_from_filename(filename):
  format_hint = ".".join(filename.split(".")[1:])
  format_map = OrderedDict()
  format_map["json"] = "json"
  format_map["toml"] = "toml"
  for key, value in format_map.items():
    if key in format_hint:
      return value
  return None


def run_command(cmd):
  try:
    # shellswitch = isinstance(cmd, collections.Sequence)
    # print "cmd:",cmd
    # print "type:",shellswitch
    shellval = False if (type(cmd) == type([])) else True
    result = subprocess.Popen(cmd, shell=shellval,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE).communicate()
    if result[1] != "" and result[1] != b"":
      logging.error(cmd)
      logging.error(result)
      raise Exception(result[1])
    return result[0].decode("utf-8")  # Returns the STDOUT
  except Exception as e:
    logging.error("Error in " + str(cmd) + ": " + str(e))
    raise e


# function to check if an input url exists or not(for csv visualizer)
def check(url):
  try:
    urllib.request.urlopen(url)
    return True
  except HTTPError:
    return False
