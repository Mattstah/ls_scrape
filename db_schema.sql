CREATE TABLE EV_URLS(
	EV_ID   INT   PRIMARY KEY   NOT NULL,
	URL     TEXT                 NOT NULL
);

CREATE TABLE EV_INFO(
	EV_ID        INT   PRIMARY KEY   NOT NULL,
	START_DATE   TEXT,
	START_TIME   TEXT,
	HOME_TEAM    TEXT   NOT NULL,
	AWAY_TEAM    TEXT   NOT NULL,
	COUNTRY      TEXT   NOT NULL,
	LEAGUE       TEXT   NOT NULL
);

CREATE TABLE EV_STATE(
	EV_ID        INT   PRIMARY KEY   NOT NULL,
	HOME_SCORE   INT,
	AWAY_SCORE   INT,
	SECS         TEXT
);
