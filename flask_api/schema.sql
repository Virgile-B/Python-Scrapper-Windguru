CREATE TABLE conditions (
  date TEXT NOT NULL,
  hour INTEGER NOT NULL,
  speed INTEGER NOT NULL,
  direction INTEGER NOT NULL,
  temperature INTEGER NOT NULL,
  PRIMARY KEY (date, hour)
);