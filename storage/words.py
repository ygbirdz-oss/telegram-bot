from storage.db import get_conn


def load_words():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT word FROM bad_words")
    rows = cursor.fetchall()

    conn.close()
    return set(row[0] for row in rows)


def add_word(word: str):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO bad_words (word) VALUES (?)",
        (word.lower(),)
    )

    conn.commit()
    conn.close()
