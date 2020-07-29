from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey


class Timeseries(Base):
    __tablename__ = "timeseries"

    id = Column(Integer, primary_key=True)
    primary_id = Column(String, unique=True)
    ts_instances = relationship("TimeseriesInstance")

    def __repr__(self):
        return "<Timeseries(primary_id='{0}')>".format(self.primary_id)


class Measurand(Base):
    __tablename__ = "measurand"

    id = Column(Integer, primary_key=True)
    short_id = Column(String, unique=True)
    long_id = Column(String, unique=True)
    description = Column(String, unique=True)

    def __repr__(self):
        return "<Measurand(short_id='{0}', long_id='{1}', description={2})>".format(
            self.short_id, self.long_id, self.description
        )


class Source(Base):
    __tablename__ = "source"

    id = Column(Integer, primary_key=True)
    short_id = Column(String, unique=True)
    description = Column(String, unique=True)

    def __repr__(self):
        return "<Source(short_id='{0}', description={1})>".format(
            self.short_id, self.description
        )


class Attribute(Base):
    __tablename__ = "attribute"

    id = Column(Integer, primary_key=True)
    short_id = Column(String, unique=True)
    description = Column(String, unique=True)

    def __repr__(self):
        return "<Attribute(short_id='{0}', description={1})>".format(
            self.short_id, self.description
        )


class AttributeValue(Base):
    __tablename__ = "attribute_value"

    id = Column(Integer, primary_key=True)
    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    attribute_value = Column(String, unique=True)

    def __repr__(self):
        return "<Attribute(attribute_id='{0}', attribute_value={1})>".format(
            self.attribute_id, self.attribute_value
        )


class SchemaVersion(Base):
    __tablename__ = "schema_version"

    id = Column(Integer, primary_key=True)
    version = Column(String)

    def __repr__(self):
        return "<SchemaVersion(version='{0}')>".format(self.version)


class TimeseriesInstance(Base):
    __tablename__ = "timeseries_instance"
    ts_id = Column(Integer, ForeignKey("timeseries.id"), primary_key=True)
    freq = Column(String(10), primary_key=True)
    measurand_id = Column(Integer, ForeignKey("measurand.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("source.id"), primary_key=True)
    initial_metadata = Column(String(255))
    measurand = relationship("Measurand", backref="measurands")
    timeseries = relationship("Timeseries", backref="timeseries")
    source = relationship("Source", backref="source")
    uuid = Column(String(32))

    def __repr__(self):
        return "<TimeseriesInstance(timeseries='{0}, measurand='{1}', source='{2}')>".format(
            self.timeseries, self.measurand, self.source
        )
