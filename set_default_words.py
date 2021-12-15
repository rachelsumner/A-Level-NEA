import goslate
import sqlite3
import time

common_words = ["hello", "goodbye"]

gs = goslate.Goslate(service_urls=['http://translate.google.zh'])
with sqlite3.connect("databases/country_codes.sqlite") as conn:
    cur = conn.cursor()
    query = "SELECT CODE\
             FROM language_codes"
    cur.execute(query)
    codes = [i[0] for i in cur.fetchall()]
    del codes[0]
print(codes)

for i in codes:
    with sqlite3.connect("databases/user_details.sqlite"):
        cur = conn.cursor()
        query = "CREATE TABLE {}(ENGLISH VARCHAR(20), \
        TRANSLATED VARCHAR(20), \
        ONE INTEGER, \
        TWO INTEGER, \
        THREE INTEGER, \
        FOUR INTEGER, \
        FIVE INTEGER, \
        SIX INTEGER, \
        PRIMARY KEY(ENGLISH));".format(i)
        try:
            cur.execute(query)
        except Exception as e:
            print(e)
        conn.commit()
    words = []
    for english in common_words:
        try:
            time.sleep(5)
            print(english)
            print(type(english))
            print(gs.translate(text=english, target_language="zh", source_language="en"))

        except Exception as e:
            print(e)

    with sqlite3.connect("databases/user_details.sqlite") as conn:
        cur = conn.cursor()
        query = "INSERT INTO {}\
                 VALUES(\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\");"
        for j in range(len(words)):
            cur.execute(query.format(i, common_words[j], words[j], "1", "0", "0", "0", "0", "0"))
            conn.commit()
