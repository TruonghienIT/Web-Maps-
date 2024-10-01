import sqlite3

def create_database():
    # Kết nối tới SQLite
    conn = sqlite3.connect('directions.db')

    # Tạo một con trỏ
    cursor = conn.cursor()

    # Tạo bảng để lưu chỉ đường
    cursor.execute('''
         CREATE TABLE IF NOT EXISTS directions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start TEXT NOT NULL,
            goal TEXT NOT NULL,
            travel_mode TEXT NOT NULL,
            distance TEXT NOT NULL,
            duration TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Lưu thay đổi và đóng kết nối
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()