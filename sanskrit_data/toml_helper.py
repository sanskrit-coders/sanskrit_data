from toml.encoder import _dump_str, TomlEncoder, unicode


def _dump_str_prefer_multiline(v):
  multilines = v.split('\n')
  if len(multilines) > 1:
    return unicode('"""\n' + v.replace('"""', '\\"""').strip() + '\n"""')
  else:
    return _dump_str(v)


class MultilinePreferringTomlEncoder(TomlEncoder):
  def __init__(self, _dict=dict, preserve=False):
    super(MultilinePreferringTomlEncoder, self).__init__(_dict=dict, preserve=preserve)
    self.dump_funcs[str] = _dump_str_prefer_multiline
