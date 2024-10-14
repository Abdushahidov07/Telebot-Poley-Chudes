import psycopg2
from secret import PASSWORD_DB

def open_conection():
    conn = psycopg2.connect(
        database="Poly_Chudes",
        user = "postgres",
        host = "localhost",
        password = PASSWORD_DB,
        port = 5432
    )
    return conn

def close_conection(conn, cur):
    cur.close()
    conn.close()

def crate_table():
    conn= open_conection()
    cur = conn.cursor()
    cur.execute("""
            create table if not exists users(
                id serial primary key,
                telgram_id varchar(100) unique,
                username varchar(100),
                first_name varchar(100),
                created_at date default now(),
                score int
                );

            create table if not exists question(
                id serial primary key,
                question_text text,
                correct_answer varchar(100),
                created_at date default now()
                )
        """)
    conn.commit()
    close_conection(conn,cur)


def add_user2(message, newname):
    crate_table()
    conn = open_conection()
    cur= conn.cursor()
    cur.execute(f"""

    insert into users(
        telgram_id,
        username,
        first_name,
        score
    )
    values(
        '{message.chat.id}',
        '{newname}',
        '{message.chat.first_name}',
        {0}
        )
    on conflict(telgram_id) do nothing
    """)
    conn.commit()
    close_conection(conn, cur)

def get_user(userid):
    conn = open_conection()
    cur = conn.cursor()
    cur.execute(f"""
                select * from users
                where telgram_id = '{userid}' 
                """)
    user = cur.fetchone()
    close_conection(conn, cur)
    if user:
        return True 
    return False

def add_user(message):
    crate_table()
    conn = open_conection()
    cur= conn.cursor()
    cur.execute(f"""

    insert into users(
        telgram_id,
        username,
        first_name,
        score
    )
    values(
        '{message.chat.id}',
        '{message.chat.username}',
        '{message.chat.first_name}',
        {0}
        )
    on conflict(telgram_id) do nothing
    """)
    conn.commit()
    close_conection(conn, cur)