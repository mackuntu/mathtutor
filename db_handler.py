import sqlite3


class DatabaseHandler:
    @staticmethod
    def save_to_database(worksheet_id, problems, answers, version):
        conn = sqlite3.connect("worksheets.db")
        c = conn.cursor()

        # Create table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS worksheets (
                     id TEXT PRIMARY KEY, 
                     version TEXT, 
                     problems TEXT, 
                     answers TEXT
                     )''')

        # Convert answers to strings and join
        str_answers = [str(answer) for answer in answers]

        # Insert data
        c.execute("INSERT INTO worksheets (id, version, problems, answers) VALUES (?, ?, ?, ?)",
                  (worksheet_id, version, ",".join(problems), ",".join(str_answers)))

        conn.commit()
        conn.close()
