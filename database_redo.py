#import libraries
import sqlite3
from datetime import datetime
import json

#create database class
class Database:
    #constructor
    def __init__(self,db_name='learning_roadmap_redo.db'):
        self.name=db_name
        self.init_db()#initialize db
    
    def get_connection(self):
        conn=sqlite3.connect(self.name)#if no database exits, it creates db object, else opens the db object
        conn.row_factory=sqlite3.Row
        return conn
    
    def init_db(self):
        conn=self.get_connection()#get conncetion object
        cursor=conn.cursor()

        #create tables
        cursor.execute(
            '''
           CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT
)
            '''
        )
        conn.commit()#save changes
        conn.close()
        print(" Database initialized successfully!")

#create class object
if __name__ == "__main__":
    db = Database()
    print("Database setup complete!")


