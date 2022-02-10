from datetime import date, datetime, timedelta
import pymysql
import pymysql.cursors
import json

from random import randint

MYSQL_DATABASE = {
    'ENGINE': 'mysql',
    #'NAME': 'asrtoolkit_v3',
    'NAME': 'profile',
    #'USER': 'vadmintest',
    #'PASSWORD': 'vadmintest123',
    'USER': 'sanaul',
    'PASSWORD': 'sanaul123',
    'HOST': '192.168.10.62',
    'PORT': '3306',
}


class DBManager:
    def __init__(self):
        self.db_name = MYSQL_DATABASE['NAME']
        self.db_user = MYSQL_DATABASE['USER']
        self.db_password = MYSQL_DATABASE['PASSWORD']
        self.db_host = MYSQL_DATABASE['HOST']
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = pymysql.connect(host=self.db_host, user=self.db_user, passwd=self.db_password,
                                              db=self.db_name)
        except Exception as e:
            print(e)
    
    
    def set_session_id(self, session_id, phoneNumber, slots):
        res=self.exist_session_id(session_id, phoneNumber, slots)
        print(res)
        if(res>0):
            return self.update_session_data(session_id, phoneNumber, slots)
        else:
            return self.insert_session_data(session_id, phoneNumber, slots)
    
    def set_slot_value(self, session_id, slot, value):
        print('set_slot_value')
        res=self.get_session_id(session_id)
        if(len(res)):            
            data=json.loads(res[2])
            data[slot]=value
            query = ("UPDATE session_table SET slots = %s WHERE session_id = %s")
            data = (json.dumps(data), session_id)
            # Update data
            try:
                self.connect()
                self.cursor = self.connection.cursor()
                self.cursor.execute(query, data)
                rowcount = self.cursor.rowcount
                # print(rowcount)

                # Make sure data is committed to the database
                self.connection.commit()
                return rowcount

            except pymysql.Error as e:
                print('error => set_slot_value => ' + 'Error %d: %s' % (e.args[0], e.args[1]))
                return -1

            finally:
                self.cursor.close()
                self.connection.close() 
            
            
    def get_session_id(self, session_id):
        print('get_session_id')
        print(session_id)
        session_id=session_id.replace("'", "")
        query = "SELECT * FROM session_table where session_id='"+session_id+"'"        

        # read audios data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query)

            row=[] 
            for idx, item in enumerate(self.cursor.fetchall()):
                for ii in range(len(item)):
                    row.append(item[ii])
            return row

        except pymysql.Error as e:
            print('error => read_data => ' + 'Error %d: %s' % (e.args[0], e.args[1]))

        finally:
            self.cursor.close()
            self.connection.close()

    def insert_session_data(self, session_id, phoneNumber, slots):
        print('insert_session_data')
        query = ("INSERT INTO session_table "
                 "(session_id, phoneNumber, slots) "
                 "VALUES (%s, %s, %s)")

        data = (session_id, phoneNumber, slots)

        # Insert new data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, data)
            rowcount = self.cursor.rowcount
            # print(rowcount)

            # Make sure data is committed to the database
            self.connection.commit()
            return rowcount
        except pymysql.Error as e:
            print('error => insert_segment_data => ' + 'Error %d: %s' % (e.args[0], e.args[1]))
            return -1

        finally:
            self.cursor.close()
            self.connection.close()

    def update_session_data(self, session_id, phoneNumber, slots):
        print("update_session_data")
        query = ("UPDATE session_table SET phoneNumber = %s, slots = %s WHERE session_id = %s")
        data = (phoneNumber, slots, session_id)

        # Insert new data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, data)
            rowcount = self.cursor.rowcount
            # print(rowcount)

            # Make sure data is committed to the database
            self.connection.commit()
            return rowcount

        except pymysql.Error as e:
            print('error => update_data => ' + 'Error %d: %s' % (e.args[0], e.args[1]))
            return -1

        finally:
            self.cursor.close()
            self.connection.close()
    

    def exist_session_id(self, session_id, phoneNumber, slots):
        print('exist_session_id')
        query = "SELECT * FROM session_table WHERE session_id = %s"
        data = (session_id)

        # read audio_segments data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, data)

            rows = self.cursor.fetchone()
            return self.cursor.rowcount

        except pymysql.Error as e:
            print('error => read_data => audio_segments => ' + 'Error %d: %s' % (e.args[0], e.args[1]))

        finally:
            self.cursor.close()
            self.connection.close()

class rasaDBManager:
    def __init__(self):
        self.db_name = MYSQL_DATABASE['rasa']
        self.db_user = MYSQL_DATABASE['USER']
        self.db_password = MYSQL_DATABASE['PASSWORD']
        self.db_host = MYSQL_DATABASE['HOST']
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = pymysql.connect(host=self.db_host, user=self.db_user, passwd=self.db_password,
                                              db=self.db_name)
        except Exception as e:
            print(e)

    def get_conversation_id(self, conversation_id):
        print('get_conversation_id')
        print(conversation_id)
        conversation_id=conversation_id.replace("'", "")
        query = "SELECT * FROM conversation_intent_metadata where conversation_id='"+conversation_id+"'"        

        # read audios data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query)

            row=[] 
            for idx, item in enumerate(self.cursor.fetchall()):
                for ii in range(len(item)):
                    row.append(item[ii])
            return row

        except pymysql.Error as e:
            print('error => read_data => ' + 'Error %d: %s' % (e.args[0], e.args[1]))

        finally:
            self.cursor.close()
            self.connection.close()

    def insert_conversation_data(self, conversation_id, intent):
        print('insert_conversation_data')
        query = ("INSERT INTO conversation_intent_metadata "
                 "(conversation_id, intent) "
                 "VALUES (%s, %s)")

        data = (conversation_id, intent)

        # Insert new data
        try:
            self.connect()
            self.cursor = self.connection.cursor()
            self.cursor.execute(query, data)
            rowcount = self.cursor.rowcount
            # print(rowcount)

            # Make sure data is committed to the database
            self.connection.commit()
            return rowcount
        except pymysql.Error as e:
            print('error => insert_segment_data => ' + 'Error %d: %s' % (e.args[0], e.args[1]))
            return -1

        finally:
            self.cursor.close()
            self.connection.close()


# if __name__ == '__main__':
#     DBManager().read_data()
