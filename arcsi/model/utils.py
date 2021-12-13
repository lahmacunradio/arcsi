from . import db

def get_or_create(model, **kwargs):
  get = db.session.query(model).filter_by(**kwargs).first()
  if get:
    return get
  else:
    row = model(**kwargs)
    db.session.add(row)
    db.session.commit()
    return row
  
