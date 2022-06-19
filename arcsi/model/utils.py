from . import db

""" Wrapper method for simple model calls.
The utility method will return an initialised model object,
either an existing db record or a new object initialised in place.
Warning: The new models need to be peristed at method call site!
"""
def get_or_create(model, **kwargs):
  get = db.session.query(model).filter_by(**kwargs).first()
  if get:
    return get
  else:
    row = model(**kwargs)
    return row
  
