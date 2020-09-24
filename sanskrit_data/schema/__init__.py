"""
Intro
-----------
schema package contains modules which define various modules describing various classes for storing Sanskrit data, and their corresponding JSON schema.

Usage tips:

- Picking or defining the data container class.

  - At the base of every such data container class is the common.JsonObject class.
  - You can define such a class yourself, in your own package (Example `here <https://github.com/sanskrit-coders/jyotisha/blob/master/jyotisha/panchangam/temporal.py>`__.).

- Enabling (de)serialization (if one has defined a data container class in a new module file)

  - One needs to update :py:data:`~sanskrit_data.schema.common.json_class_index` - see the comment there for details.

Data design
-----------

General principles
~~~~~~~~~~~~~~~~~~

-  We want data to be stored and communicated between programs in a
   popular, extensible format - we want to take advantage of existing
   technologies to the maximum possible extant and not waste time
   reinventing associated (de)serialization, validation and other
   libraries.
-  But this does not prevent the data from being presented in a
   different format for human consumption.

While designing the JSON **data-model**:

-  Type-hint in JSON should be jsonClass (a language-independent name
   we've picked).
-  Try to avoid field-names which conflict with programming language
   keywords. (Eg. Prefer "source\\_type" to "type").
-  In general, use camelCase or underscore\\_case for field names - both
   are fine. Where romanized (potentially mixed case) sanskrit words are
   used, the latter is the superior convention.
-  Where field names and values are to be automatically rendered into
   various scripts, as in case of sanskrit vyAkarana jargon (eg:
   vibhakti, lakAra), we prefer SLP1 transliteration ("viBakti",
   "lakAra").

   -  PS: Convenient transliteration modules are available in various
      languages: please see them listed
      `here <https://github.com/sanskrit-coders/indic-transliteration#libraries-in-other-languages>`__.
   -  A `transliteration
      map <https://docs.google.com/spreadsheets/d/1o2vysXaXfNkFxCO-WD77C4AEbXcAcJmDVgUb-E0mYbg/edit#gid=0>`__
      for reference.

-  When in doubt, keep fields optional.

Python data containers and utilities
------------------------------------

-  For each JSON schema, we have a python class, at the root of which
   there is the generic JsonObject class with a lot of utilities. We
   define a hierarchy of classes so as to share validation and other
   code specific to certain data classes.
-  **Separate Database-specific elements through an interface**. We
   should be able to easily switch to a different database.
- The schema class field contains the corresponding JSON schema. `An introductory video describing how such schema are to be read <https://www.youtube.com/watch?v=SHzD3f5nPt0&t=29s>`_.
-  Slides `here <https://docs.google.com/presentation/d/1Wx1rxf5W5VpvSS4oGkGpp28WPPM57CUx41dGHC4ed80/edit#slide=id.p>`__

Books and annotations
~~~~~~~~~~~~~~~~~~~~~
Please refer to :mod:`~sanskrit_data.schema.books` and :mod:`~sanskrit_data.schema.ullekhanam` .

"""

# Sphinx uses the all list to check every module is loaded, but in some cases it is not and a warning is generated:
#   missing attribute mentioned in :members: or __all__: module
"""Allows users to do ``from xyz import *`` """
__all__ = ["common", "books", "ullekhanam", "users"]
