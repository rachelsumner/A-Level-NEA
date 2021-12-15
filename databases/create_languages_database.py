languages_and_codes = open("languages_to_add.txt","r")
query = ""
for line in languages_and_codes:
    line = line.strip()
    if len(line) == 2:
        query += "\"{}\");\n".format(str(line))
    else:
        query += "INSERT INTO language_codes (Language, Code)\n"
        query += "VALUES(\"{}\",".format(str(line))
languages_and_codes.close()
print(query)
