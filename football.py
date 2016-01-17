from sqlalchemy import (
	create_engine,
	Column,
	Date,
	ForeignKey,
	Integer,
	String,
	Time,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Match(Base):
	__tablename__ = 'match'

	match_id = Column(Integer, primary_key=True)

	home_team = Column(String(250), nullable=False)
	away_team = Column(String(250), nullable=False)

	country = Column(String(250))
	league = Column(String(250))

	start_time = Column(Time)
	start_date = Column(Date)

	state_id = Column(Integer, ForeignKey('state.state_id'))

	state = relationship(
		"State",
		uselist=False,
		back_populates="match",
		cascade='save-update',
	)

class State(Base):
	__tablename__ = 'state'

	state_id = Column(Integer, primary_key=True)

	home_score = Column(Integer)
	away_score = Column(Integer)

	mins = Column(Integer)

	match = relationship("Match", uselist=False, back_populates="state")

def get_db_session(db_name):
	engine = create_engine(db_name)
	Base.metadata.bind = engine

	Base.metadata.create_all(engine)

	db_session = sessionmaker()
	db_session.bind = engine

	session = db_session()

	return session
