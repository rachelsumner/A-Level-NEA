CREATE TABLE USER_EXPERIENCE(USER_ID INTEGER, LANGUAGE VARCHAR(2), FOREIGN KEY(USER_ID) REFERENCES USER_DETAILS(USER_ID), PRIMARY KEY(USER_ID, LANGUAGE);