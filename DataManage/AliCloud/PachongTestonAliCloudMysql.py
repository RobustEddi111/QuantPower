import pymysql

# 建立连接
conn = pymysql.connect(
    host="127.0.0.1",
    port=13306,
    user="ptrader",
    password="2744798981",
    charset="utf8mb4",
    connect_timeout=5,
)

try:
    with conn.cursor() as cur:
        # 1. 创建测试数据库（如果不存在）
        cur.execute("CREATE DATABASE IF NOT EXISTS test_db DEFAULT CHARACTER SET utf8mb4;")
        cur.execute("USE test_db;")

        # 2. 创建用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100),
                age INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 3. 创建订单表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_name VARCHAR(100),
                amount DECIMAL(10, 2),
                status ENUM('pending', 'paid', 'shipped', 'completed') DEFAULT 'pending',
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 4. 创建产品表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock INT DEFAULT 0,
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 5. 插入测试数据 - 用户
        cur.execute("""
            INSERT INTO users (username, email, age) VALUES
            ('alice', 'alice@example.com', 25),
            ('bob', 'bob@example.com', 30),
            ('charlie', 'charlie@example.com', 28)
            ON DUPLICATE KEY UPDATE email=VALUES(email);
        """)

        # 6. 插入测试数据 - 产品
        cur.execute("""
            INSERT INTO products (name, description, price, stock, category) VALUES
            ('笔记本电脑', '高性能办公笔记本', 5999.00, 50, '电子产品'),
            ('无线鼠标', '人体工学设计', 99.00, 200, '电子产品'),
            ('机械键盘', 'Cherry轴', 399.00, 100, '电子产品'),
            ('显示器', '27英寸 4K', 2199.00, 30, '电子产品'),
            ('咖啡杯', '陶瓷材质', 29.90, 500, '生活用品')
            ON DUPLICATE KEY UPDATE price=VALUES(price);
        """)

        # 7. 插入测试数据 - 订单
        cur.execute("""
            INSERT INTO orders (user_id, product_name, amount, status) VALUES
            (1, '笔记本电脑', 5999.00, 'completed'),
            (1, '无线鼠标', 99.00, 'completed'),
            (2, '机械键盘', 399.00, 'shipped'),
            (3, '显示器', 2199.00, 'paid'),
            (2, '咖啡杯', 29.90, 'pending')
            ON DUPLICATE KEY UPDATE status=VALUES(status);
        """)

        # 提交事务
        conn.commit()

        # 8. 验证数据
        print("=" * 50)
        print("数据库和表创建成功！\n")

        # 查询用户数量
        cur.execute("SELECT COUNT(*) FROM users;")
        print(f"用户表记录数: {cur.fetchone()[0]}")

        # 查询产品数量
        cur.execute("SELECT COUNT(*) FROM products;")
        print(f"产品表记录数: {cur.fetchone()[0]}")

        # 查询订单数量
        cur.execute("SELECT COUNT(*) FROM orders;")
        print(f"订单表记录数: {cur.fetchone()[0]}")

        print("\n" + "=" * 50)
        print("查询示例 - 用户及其订单统计：\n")

        cur.execute("""
            SELECT 
                u.username,
                u.email,
                COUNT(o.id) as order_count,
                COALESCE(SUM(o.amount), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.username, u.email
            ORDER BY total_spent DESC;
        """)

        for row in cur.fetchall():
            print(f"用户: {row[0]}, 邮箱: {row[1]}, 订单数: {row[2]}, 总消费: ¥{row[3]}")

        print("=" * 50)
        print("\n✅ 所有测试表创建并插入数据成功！")

except pymysql.Error as e:
    print(f"❌ 数据库错误: {e}")
    conn.rollback()
except Exception as e:
    print(f"❌ 发生错误: {e}")
finally:
    conn.close()
    print("\n连接已关闭")
