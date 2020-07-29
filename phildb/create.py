import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

from phildb import constants
from phildb import dbstructures
from phildb.exceptions import AlreadyExistsError


def create(tsdb_path):

    if not os.path.exists(tsdb_path):
        os.makedirs(tsdb_path)
        os.makedirs(os.path.join(tsdb_path, "data"))
    elif not os.listdir(tsdb_path):
        os.makedirs(os.path.join(tsdb_path, "data"))
    else:
        raise AlreadyExistsError(
            "PhilDB database already exists at: {0}".format(tsdb_path)
        )

    engine = create_engine(
        "sqlite:///{0}{1}{2}".format(tsdb_path, os.path.sep, constants.METADATA_DB)
    )
    dbstructures.Base.metadata.create_all(engine)

    Session.configure(bind=engine)
    session = Session()

    version = dbstructures.SchemaVersion(version=constants.DB_VERSION)
    session.add(version)
    session.commit()


def main():
    parser = argparse.ArgumentParser(description="Create PhilDB database.")
    parser.add_argument("dbname", help="PhilDB database to create")

    args = parser.parse_args()

    create(args.dbname)


if __name__ == "__main__":
    main()
