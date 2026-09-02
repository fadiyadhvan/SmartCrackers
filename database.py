# ==========================================
# DATABASE CONNECTION
# ==========================================

import pymysql


def get_connection():

    connection = pymysql.connect(

        host="localhost",

        user="root",

        password="",

        database="smartcrackers",

        cursorclass=pymysql.cursors.DictCursor

    )

    return connection


# ==========================================
# ADD MOBILE COLUMN TO ORDERS TABLE
# ==========================================

def add_mobile_column():

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            ALTER TABLE orders
            ADD COLUMN mobile VARCHAR(20)
        """)

        connection.commit()

        print("✅ Mobile column added successfully!")

    except pymysql.err.OperationalError as error:

        # 1060 means the column already exists
        if error.args[0] == 1060:

            print("✅ Mobile column already exists!")

        else:

            print("❌ Database error:", error)

    finally:

        cursor.close()

        connection.close()


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    add_mobile_column()