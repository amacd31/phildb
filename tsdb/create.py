import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

from . import constants
from . import dbstructures
from .exceptions import AlreadyExistsError

def create(tsdb_path):

    if not os.path.exists(tsdb_path):
        os.makedirs(tsdb_path)
        os.makedirs(os.path.join(tsdb_path, 'data'))
    elif not os.listdir(tsdb_path):
        os.makedirs(os.path.join(tsdb_path, 'data'))
    else:
        raise AlreadyExistsError('TSDB already exists at: {0}'.format(tsdb_path))

    engine = create_engine('sqlite:///{0}{1}{2}'.format(tsdb_path, os.path.sep, constants.METADATA_DB))
    dbstructures.Base.metadata.create_all(engine)

    Session.configure(bind=engine)
    session = Session()

    version = dbstructures.SchemaVersion(version=constants.DB_VERSION)
    session.add(version)
    session.commit()

if __name__ == "__main__":
    create(sys.argv[1])

