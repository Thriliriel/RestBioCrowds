from typing import TYPE_CHECKING
import psycopg2

if TYPE_CHECKING:
    from BioCrowds import BioCrowdsClass

class BioCrowdsDataBase():

    def ConnectDB(self):
        self.conn = psycopg2.connect(host="localhost",
                                database="biocrowds",
                                user="postgres",
                                password="postgres")

    def execute_cursor_command(self, comm):
        cursor = self.conn.cursor()
        cursor.execute(comm)
        self.conn.commit()
        cursor.close()

    def ClearDatabase(self, ip):
        self.execute_cursor_command("delete from config where id = '" + ip + "'")
        self.execute_cursor_command("delete from agents where ip = '" + ip + "'")
        self.execute_cursor_command("delete from goals where id = '" + ip + "'")
        self.execute_cursor_command("delete from obstacles where id = '" + ip + "'")
        self.execute_cursor_command("delete from obstacles_points where id = '" + ip + "'")
        self.execute_cursor_command("delete from cells where id = '" + ip + "'")
        self.execute_cursor_command("delete from agents_paths where id = '" + ip + "'")

    def close_connection(self):
        self.conn.close()