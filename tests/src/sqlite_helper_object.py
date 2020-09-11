import sqlite3

import csv_utils


class SQLiteHelperObject:

  def __init__(self, db_file):
    self.db = db_file
    self.conn = None
    self.c = None

  def connect(self):
    print(self.db)
    self.conn = sqlite3.connect(self.db)
    self.c = self.conn.cursor()

  def create_table_if_not_exists(self, table_name, row_names_list):
    self.c.execute("CREATE TABLE IF NOT EXISTS {0} ({1})"
                   .format(table_name, ", ".join(row_names_list)))

  def insert_csv_data_into_sqlite_table(self, table_name, csv_fpath, **kwargs):

    # read in csv file data
    header, data = csv_utils.read_in_data_as_tuples(csv_fpath)

    # create table if not exists yet
    column_names = header
    column_names.append(kwargs.keys())
    data_rows = [data_row + kwargs.values() for data_row in data]
    question_marks = ", ".join(["?"] * len(column_names))
    self.create_table_if_not_exists(table_name, column_names)

    # insert the rows
    self.c.executemany("INSERT INTO {0} ({1})".format(table_name, question_marks), data_rows)

  def close(self):
    self.conn.close()
