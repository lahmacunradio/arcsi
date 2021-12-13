from . import db

def get_or_create(model, **kwargs):
  get = db.session.query(model).filter_by(**kwargs).first()
  if get:
    return get
  else:
    row = model(**kwargs)
    return row
  
