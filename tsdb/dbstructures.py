from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String

class Timeseries(Base):
    __tablename__ = 'timeseries'

    id = Column(Integer, primary_key=True)
    primary_id = Column(String, unique=True)
    timeseries_id = Column(Integer, unique=True)

    def __repr__(self):
        return "<Timeseries(primary_id='{0}', timeseries_id='{1}')>".format(
                self.primary_id, self.timeseries_id)

class Measurand(Base):
    __tablename__ = 'measurand'

    id = Column(Integer, primary_key=True)
    short_id = Column(String, unique=True)
    long_id = Column(String, unique=True)
    description = Column(String, unique=True)

    def __repr__(self):
        return "<Timeseries(primary_id='{0}', timeseries_id='{1}')>".format(
                self.primary_id, self.timeseries_id)

class SchemaVersion(Base):
    __tablename__ = 'schema_version'

    id = Column(Integer, primary_key=True)
    version = Column(String)

    def __repr__(self):
        return "<SchemaVersion(version='{0}')>".format(self.version)

