# pip install pymysql
import pymysql
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "ptrader"
MYSQL_PASSWORD = "2744798981"

DB_NAME = "py_test_db_MacbookAir_Kraken2"

schema_sql = f"""
CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `{DB_NAME}`;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 产品表
CREATE TABLE IF NOT EXISTS products (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  sku VARCHAR(64) NOT NULL,
  title VARCHAR(200) NOT NULL,
  price_cents INT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_products_sku (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  status ENUM('NEW','PAID','CANCELLED') NOT NULL DEFAULT 'NEW',
  total_cents INT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_orders_user_id (user_id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单明细表
CREATE TABLE IF NOT EXISTS order_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  qty INT UNSIGNED NOT NULL,
  unit_price_cents INT UNSIGNED NOT NULL,
  PRIMARY KEY (id),
  KEY idx_items_order_id (order_id),
  KEY idx_items_product_id (product_id),
  CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

seed_sql = f"""
USE `{DB_NAME}`;

INSERT INTO users(email, name) VALUES
('alice@example.com','Alice'),
('bob@example.com','Bob')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO products(sku, title, price_cents) VALUES
('SKU-001','Keyboard',19900),
('SKU-002','Mouse',5900)
ON DUPLICATE KEY UPDATE title=VALUES(title), price_cents=VALUES(price_cents);

-- 创建一笔订单（Alice）
INSERT INTO orders(user_id, status, total_cents)
SELECT id, 'NEW', 0 FROM users WHERE email='alice@example.com'
LIMIT 1;

-- 给这笔订单加两条明细，并回写总价
SET @oid := LAST_INSERT_ID();

INSERT INTO order_items(order_id, product_id, qty, unit_price_cents)
SELECT @oid, p.id, 1, p.price_cents FROM products p WHERE p.sku='SKU-001';
INSERT INTO order_items(order_id, product_id, qty, unit_price_cents)
SELECT @oid, p.id, 2, p.price_cents FROM products p WHERE p.sku='SKU-002';

UPDATE orders o
JOIN (
  SELECT order_id, SUM(qty * unit_price_cents) AS total
  FROM order_items
  WHERE order_id=@oid
  GROUP BY order_id
) t ON t.order_id=o.id
SET o.total_cents = t.total
WHERE o.id=@oid;
"""

def main():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=True,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
    )

    with conn.cursor() as cur:
        cur.execute(schema_sql)
        cur.execute(seed_sql)

        cur.execute(f"SHOW DATABASES LIKE '{DB_NAME}';")
        print("db:", cur.fetchone())

        cur.execute(f"SHOW TABLES FROM `{DB_NAME}`;")
        print("tables:", cur.fetchall())

        cur.execute(f"SELECT * FROM `{DB_NAME}`.orders ORDER BY id DESC LIMIT 5;")
        print("orders:", cur.fetchall())

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
