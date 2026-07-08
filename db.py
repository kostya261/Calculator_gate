import psycopg2
from psycopg2 import sql, OperationalError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import config
import json


# ============================================================
# 1. ПОДКЛЮЧЕНИЯ
# ============================================================
def get_connection():
    cfg = config.get_db_config()
    try:
        return psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["dbname"],
            connect_timeout=5
        )
    except psycopg2.OperationalError as e:
        error_msg = f"Ошибка подключения к БД:\n\n{e}\n\n"
        error_msg += f"Параметры подключения:\n"
        error_msg += f"Хост: {cfg['host']}\n"
        error_msg += f"Порт: {cfg['port']}\n"
        error_msg += f"Пользователь: {cfg['user']}\n"
        error_msg += f"База данных: {cfg['dbname']}\n\n"
        error_msg += "Проверьте:\n"
        error_msg += "1. Запущен ли PostgreSQL\n"
        error_msg += "2. Правильность пароля в config.py\n"
        error_msg += "3. Доступность порта 5432"

        from PyQt6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        QMessageBox.critical(None, "Ошибка подключения к БД", error_msg)
        raise


def get_postgres_connection():
    cfg = config.get_db_config()
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database="postgres"
    )


# ============================================================
# 2. УТИЛИТЫ
# ============================================================
def column_exists(conn, table_name, column_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    result = cur.fetchone() is not None
    cur.close()
    return result


def table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = %s
    """, (table_name,))
    result = cur.fetchone() is not None
    cur.close()
    return result


def constraint_exists(conn, constraint_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname = %s
    """, (constraint_name,))
    result = cur.fetchone() is not None
    cur.close()
    return result


def add_column_if_not_exists(conn, table_name, column_name, column_type, default=None):
    if not column_exists(conn, table_name, column_name):
        cur = conn.cursor()
        try:
            sql_cmd = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default is not None:
                sql_cmd += f" DEFAULT {default}"
            cur.execute(sql_cmd)
            conn.commit()
            print(f"✅ Добавлена колонка {table_name}.{column_name}")
        except Exception as e:
            print(f"⚠️ Не удалось добавить колонку {table_name}.{column_name}: {e}")
            conn.rollback()
        finally:
            cur.close()
        return True
    return False


def ensure_unique_constraint(conn, table_name, columns, constraint_name=None):
    if constraint_name is None:
        constraint_name = f"{table_name}_{'_'.join(columns)}_key"

    if not constraint_exists(conn, constraint_name):
        cur = conn.cursor()
        try:
            columns_str = ', '.join(columns)
            cur.execute(f"""
                ALTER TABLE {table_name} 
                ADD CONSTRAINT {constraint_name} 
                UNIQUE ({columns_str})
            """)
            conn.commit()
            print(f"✅ Создано уникальное ограничение: {constraint_name}")
            cur.close()
            return True
        except Exception as e:
            print(f"⚠️ Не удалось создать ограничение {constraint_name}: {e}")
            conn.rollback()
            cur.close()
            return False
    else:
        print(f"ℹ️ Ограничение {constraint_name} уже существует")
        return True


# ============================================================
# 3. СОЗДАНИЕ БАЗЫ И ТАБЛИЦ
# ============================================================
def create_database_if_not_exists():
    cfg = config.get_db_config()
    dbname = cfg["dbname"]
    try:
        conn = get_postgres_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cur.fetchone()
        if not exists:
            print(f"База данных '{dbname}' не найдена. Создаём...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print(f"База данных '{dbname}' успешно создана.")
        cur.close()
        conn.close()
        return True
    except OperationalError as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        return False


def create_tables_if_not_exists():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # beam_types
        cur.execute("""
            CREATE TABLE IF NOT EXISTS beam_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(20) UNIQUE NOT NULL,
                height_mm INTEGER NOT NULL,
                width_mm INTEGER NOT NULL,
                weight_kg_per_m DECIMAL(5,2) NOT NULL,
                purchase_price DECIMAL(10,2) DEFAULT 0,
                retail_price DECIMAL(10,2) DEFAULT 0
            )
        """)
        print("✅ Таблица beam_types создана/проверена.")

        # units
        cur.execute("""
            CREATE TABLE IF NOT EXISTS units (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            )
        """)
        print("✅ Таблица units создана/проверена.")

        # materials
        cur.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                unit VARCHAR(20) NOT NULL,
                weight_per_unit DECIMAL(8,3),
                purchase_price DECIMAL(10,2),
                retail_price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица materials создана/проверена.")

        add_column_if_not_exists(conn, 'materials', 'parent_id', 'INTEGER')
        add_column_if_not_exists(conn, 'materials', 'is_category', 'BOOLEAN', 'FALSE')
        add_column_if_not_exists(conn, 'materials', 'is_kit', 'BOOLEAN', 'FALSE')
        add_column_if_not_exists(conn, 'materials', 'consumption_per_m2', 'DECIMAL(10,4)', '0')

        # clients
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                type VARCHAR(20) NOT NULL CHECK (type IN ('individual', 'legal')),
                last_name VARCHAR(100),
                first_name VARCHAR(100),
                middle_name VARCHAR(100),
                organization_name VARCHAR(200),
                phone1 VARCHAR(20),
                phone2 VARCHAR(20),
                email VARCHAR(100),
                messenger VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица clients создана/проверена.")

        # addresses
        cur.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                index VARCHAR(10),
                region VARCHAR(100),
                city VARCHAR(100),
                street VARCHAR(100),
                house VARCHAR(10),
                building VARCHAR(10),
                apartment VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица addresses создана/проверена.")

        # projects
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id),
                address_id INTEGER REFERENCES addresses(id),
                status VARCHAR(30) DEFAULT 'draft',
                manager VARCHAR(100),
                width_opening INTEGER,
                height_total INTEGER,
                beam_type_id INTEGER REFERENCES beam_types(id),
                sections INTEGER DEFAULT 4,
                diagonals BOOLEAN DEFAULT FALSE,
                custom_counterweight BOOLEAN DEFAULT FALSE,
                custom_counterweight_length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица projects создана/проверена.")

        # estimates
        cur.execute("""
            CREATE TABLE IF NOT EXISTS estimates (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                number VARCHAR(50),
                date DATE DEFAULT CURRENT_DATE,
                total_amount DECIMAL(12,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица estimates создана/проверена.")

        add_column_if_not_exists(conn, 'estimates', 'client_id', 'INTEGER')
        add_column_if_not_exists(conn, 'estimates', 'client_name', 'VARCHAR(200)', "'Не указан'")
        add_column_if_not_exists(conn, 'estimates', 'client_address', 'VARCHAR(300)', "'Не указан'")

        # estimate_items
        cur.execute("""
            CREATE TABLE IF NOT EXISTS estimate_items (
                id SERIAL PRIMARY KEY,
                estimate_id INTEGER REFERENCES estimates(id) ON DELETE CASCADE,
                material_id INTEGER REFERENCES materials(id),
                material_name VARCHAR(200),
                length_mm INTEGER,
                quantity DECIMAL(10,2),
                unit VARCHAR(20),
                price DECIMAL(12,2),
                total DECIMAL(12,2),
                weight_kg DECIMAL(10,3),
                note TEXT
            )
        """)
        print("✅ Таблица estimate_items создана/проверена.")

        add_column_if_not_exists(conn, 'estimate_items', 'is_kit', 'BOOLEAN', 'FALSE')
        add_column_if_not_exists(conn, 'estimate_items', 'kit_parent_id', 'INTEGER')
        add_column_if_not_exists(conn, 'estimate_items', 'is_paint', 'BOOLEAN', 'FALSE')

        # users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                login VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                salt VARCHAR(32) NOT NULL,
                full_name VARCHAR(200) NOT NULL,
                position VARCHAR(100) DEFAULT '',
                role VARCHAR(20) DEFAULT 'manager' CHECK (role IN ('admin', 'manager')),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        print("✅ Таблица users создана/проверена.")

        # kits
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kits (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                retail_price DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица kits создана/проверена.")

        # kit_items
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kit_items (
                id SERIAL PRIMARY KEY,
                kit_id INTEGER REFERENCES kits(id) ON DELETE CASCADE,
                material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
                quantity DECIMAL(10,2) DEFAULT 1,
                unit VARCHAR(20),
                consumption_per_unit DECIMAL(10,4) DEFAULT 0,
                calculation_type VARCHAR(20) DEFAULT 'fixed',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица kit_items создана/проверена.")

        add_column_if_not_exists(conn, 'kit_items', 'consumption_per_unit', 'DECIMAL(10,4)', '0')
        add_column_if_not_exists(conn, 'kit_items', 'calculation_type', 'VARCHAR(20)', "'fixed'")
        add_column_if_not_exists(conn, 'kit_items', 'notes', 'TEXT', "''")

        ensure_unique_constraint(conn, 'kit_items', ['kit_id', 'material_id'], 'kit_items_kit_id_material_id_key')

        # СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ПО УМОЛЧАНИЮ
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            print("Создаём пользователя по умолчанию (admin/admin)...")
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            password = "admin"
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (login, password_hash, salt, full_name, position, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('admin', password_hash, salt, 'Администратор', 'Администратор', 'admin'))
            print("✅ Пользователь admin создан (пароль: admin)")

        # КОРНЕВЫЕ КАТЕГОРИИ
        cur.execute("SELECT COUNT(*) FROM materials WHERE is_category = TRUE AND parent_id IS NULL")
        if cur.fetchone()[0] == 0:
            print("Создаём корневые категории...")
            categories = [
                ('Электрика', 'Категория: Электрика'),
                ('Крепёж', 'Категория: Крепёж'),
                ('Автоматика', 'Категория: Автоматика'),
                ('Комплекты', 'Категория: Комплекты'),
            ]
            for name, desc in categories:
                cur.execute("""
                    INSERT INTO materials (name, unit, is_category, description)
                    VALUES (%s, 'категория', TRUE, %s)
                """, (name, desc))
            print("✅ Корневые категории созданы.")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Все таблицы созданы/проверены.")
        return True

    except OperationalError as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        if conn:
            conn.rollback()
            cur.close()
            conn.close()
        return False


# ============================================================
# 4. ЗАПОЛНЕНИЕ СПРАВОЧНИКОВ (БЕЗ ON CONFLICT)
# ============================================================
def fill_reference_data():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Типы балок
        cur.execute("SELECT COUNT(*) FROM beam_types")
        if cur.fetchone()[0] == 0:
            print("Заполняем справочник типов балок...")
            cur.execute("""
                INSERT INTO beam_types (name, height_mm, width_mm, weight_kg_per_m) VALUES
                ('SG01', 60, 40, 5.8),
                ('SG02', 85, 60, 11.2)
            """)

        # Единицы измерения
        cur.execute("SELECT COUNT(*) FROM units")
        if cur.fetchone()[0] == 0:
            print("Заполняем справочник единиц измерения...")
            cur.execute("""
                INSERT INTO units (name) VALUES
                ('м.п.'), ('шт'), ('кг'), ('м²'), ('л')
            """)

        # Материалы
        cur.execute("SELECT COUNT(*) FROM materials WHERE is_category = FALSE AND is_kit = FALSE")
        if cur.fetchone()[0] == 0:
            print("Заполняем справочник материалов...")
            cur.execute("SELECT id, name FROM materials WHERE is_category = TRUE")
            categories = {row[1]: row[0] for row in cur.fetchall()}

            materials = [
                ('Труба 60×40×2', 'м.п.', 2.96, categories.get('Крепёж')),
                ('Труба 80×40×2', 'м.п.', 3.59, categories.get('Крепёж')),
                ('Труба 40×20×1.5', 'м.п.', 1.31, categories.get('Крепёж')),
                ('Саморез 3.5×25', 'шт', 0.01, categories.get('Крепёж')),
                ('Саморез 4.2×32', 'шт', 0.02, categories.get('Крепёж')),
                ('Анкер 10×100', 'шт', 0.05, categories.get('Крепёж')),
                ('Розетка двойная', 'шт', 0.1, categories.get('Электрика')),
                ('Выключатель', 'шт', 0.1, categories.get('Электрика')),
            ]
            for name, unit, weight, parent_id in materials:
                cur.execute("""
                    INSERT INTO materials (name, unit, weight_per_unit, parent_id)
                    VALUES (%s, %s, %s, %s)
                """, (name, unit, weight, parent_id))

        # КОМПЛЕКТ ПОКРАСКИ
        print("🔄 Настройка покраски...")

        cur.execute("SELECT COUNT(*) FROM kits WHERE name = 'Покраска'")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id FROM materials WHERE name = 'Комплекты' AND is_category = TRUE")
            kit_category = cur.fetchone()
            kit_category_id = kit_category[0] if kit_category else None

            materials_paint = [
                ('Работа (покраска)', 'м²', 1.0, 'Расходные работы по покраске'),
                ('Ветошь', 'кг', 0.05, 'Расходный материал для покраски'),
                ('Растворитель', 'л', 0.1, 'Расходный материал для покраски'),
                ('Матрикс', 'л', 0.15, 'Расходный материал для покраски'),
                ('Краска', 'л', 0.2, 'Расходный материал для покраски'),
            ]

            material_ids = {}
            for name, unit, consumption, desc in materials_paint:
                # Проверяем, есть ли уже такой материал
                cur.execute("SELECT id FROM materials WHERE name = %s", (name,))
                existing = cur.fetchone()

                if existing:
                    material_ids[name] = existing[0]
                    # Обновляем расход
                    cur.execute("""
                        UPDATE materials 
                        SET consumption_per_m2 = %s
                        WHERE name = %s
                    """, (consumption, name))
                    print(f"  ✅ Обновлён материал: {name} (расход: {consumption} {unit}/м²)")
                else:
                    cur.execute("""
                        INSERT INTO materials (name, unit, consumption_per_m2, description, parent_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (name, unit, consumption, desc, kit_category_id))
                    row = cur.fetchone()
                    if row:
                        material_ids[name] = row[0]
                        print(f"  ✅ Создан материал: {name} (расход: {consumption} {unit}/м²)")

            cur.execute("""
                INSERT INTO kits (name, description, retail_price)
                VALUES ('Покраска', 'Комплект расходных материалов для покраски', 0)
                RETURNING id
            """)
            kit_id = cur.fetchone()[0]
            print(f"  ✅ Создан комплект: Покраска (id={kit_id})")

            kit_items_data = {
                'Работа (покраска)': {'quantity': 1, 'unit': 'м²', 'consumption': 1.0, 'calc_type': 'area'},
                'Ветошь': {'quantity': 1, 'unit': 'кг', 'consumption': 0.05, 'calc_type': 'per_m2'},
                'Растворитель': {'quantity': 1, 'unit': 'л', 'consumption': 0.1, 'calc_type': 'per_m2'},
                'Матрикс': {'quantity': 1, 'unit': 'л', 'consumption': 0.15, 'calc_type': 'per_m2'},
                'Краска': {'quantity': 1, 'unit': 'л', 'consumption': 0.2, 'calc_type': 'per_m2'},
            }

            for name, data in kit_items_data.items():
                mat_id = material_ids.get(name)
                if mat_id:
                    # Проверяем, есть ли уже такая позиция в комплекте
                    cur.execute("""
                        SELECT id FROM kit_items 
                        WHERE kit_id = %s AND material_id = %s
                    """, (kit_id, mat_id))
                    existing = cur.fetchone()

                    if existing:
                        # Обновляем
                        cur.execute("""
                            UPDATE kit_items 
                            SET quantity = %s, unit = %s, consumption_per_unit = %s, calculation_type = %s
                            WHERE kit_id = %s AND material_id = %s
                        """, (data['quantity'], data['unit'], data['consumption'], data['calc_type'], kit_id, mat_id))
                    else:
                        # Вставляем
                        cur.execute("""
                            INSERT INTO kit_items (kit_id, material_id, quantity, unit, consumption_per_unit, calculation_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (kit_id, mat_id, data['quantity'], data['unit'], data['consumption'], data['calc_type']))
                    print(f"    └─ Добавлен {name}: {data['consumption']} {data['unit']}/м²")

            print("  ✅ Комплект 'Покраска' создан с новыми полями")
        else:
            print("  ℹ️ Комплект 'Покраска' уже существует")

        conn.commit()
        cur.close()
        conn.close()
        return True

    except OperationalError as e:
        print(f"❌ Ошибка при заполнении справочников: {e}")
        if conn:
            conn.rollback()
            cur.close()
            conn.close()
        return False


# ============================================================
# 5. ИНИЦИАЛИЗАЦИЯ
# ============================================================
def init_db():
    print("🔄 Инициализация базы данных...")
    if not create_database_if_not_exists():
        return False
    if not create_tables_if_not_exists():
        return False
    if not fill_reference_data():
        return False

    try:
        conn = get_connection()
        ensure_unique_constraint(conn, 'kit_items', ['kit_id', 'material_id'], 'kit_items_kit_id_material_id_key')
        conn.close()
    except Exception as e:
        print(f"⚠️ Не удалось проверить ограничение: {e}")

    print("✅ База данных инициализирована успешно.")
    return True


# ============================================================
# 6. ФУНКЦИИ ДЛЯ РАБОТЫ С КОМПЛЕКТАМИ (БЕЗ ON CONFLICT)
# ============================================================

def add_kit_item_full(kit_id, material_id, quantity=1, unit='', consumption_per_unit=0, calculation_type='fixed',
                      notes=''):
    """
    Добавляет позицию в комплект с полной информацией о расчете
    БЕЗ использования ON CONFLICT
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id FROM kit_items 
            WHERE kit_id = %s AND material_id = %s
        """, (kit_id, material_id))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE kit_items 
                SET quantity = %s, unit = %s, consumption_per_unit = %s, 
                    calculation_type = %s, notes = %s
                WHERE kit_id = %s AND material_id = %s
            """, (quantity, unit, consumption_per_unit, calculation_type, notes, kit_id, material_id))
        else:
            cur.execute("""
                INSERT INTO kit_items (kit_id, material_id, quantity, unit, consumption_per_unit, calculation_type, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (kit_id, material_id, quantity, unit, consumption_per_unit, calculation_type, notes))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления позиции в комплект: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def get_kit_items_full(kit_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ki.id, ki.material_id, ki.quantity, ki.unit, 
               ki.consumption_per_unit, ki.calculation_type, ki.notes,
               m.name, m.unit, m.retail_price, m.consumption_per_m2
        FROM kit_items ki
        JOIN materials m ON m.id = ki.material_id
        WHERE ki.kit_id = %s
    """, (kit_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            'id': r[0],
            'material_id': r[1],
            'quantity': float(r[2]) if r[2] else 1,
            'unit': r[3] or '',
            'consumption_per_unit': float(r[4]) if r[4] else 0,
            'calculation_type': r[5] or 'fixed',
            'notes': r[6] or '',
            'material_name': r[7],
            'material_unit': r[8],
            'material_price': float(r[9]) if r[9] else 0,
            'consumption_per_m2': float(r[10]) if r[10] else 0
        })
    return result


def calculate_kit_item_quantity(kit_item, context):
    calc_type = kit_item.get('calculation_type', 'fixed')
    consumption = kit_item.get('consumption_per_unit', 0)
    base_quantity = kit_item.get('quantity', 1)

    if calc_type == 'fixed':
        return base_quantity
    elif calc_type == 'per_m2':
        area = context.get('area', 0)
        return area * consumption
    elif calc_type == 'per_m':
        length_m = context.get('length', 0) / 1000
        return length_m * consumption
    elif calc_type == 'area':
        return context.get('area', 0)
    elif calc_type == 'length':
        return context.get('length', 0) / 1000
    else:
        return base_quantity


# ============================================================
# 7. БАЗОВЫЕ ФУНКЦИИ ДЛЯ КОМПЛЕКТОВ (БЕЗ ON CONFLICT)
# ============================================================

def add_kit_item(kit_id, material_id, quantity=1, unit='', notes=''):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id FROM kit_items 
            WHERE kit_id = %s AND material_id = %s
        """, (kit_id, material_id))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE kit_items 
                SET quantity = %s, unit = %s, notes = %s
                WHERE kit_id = %s AND material_id = %s
            """, (quantity, unit, notes, kit_id, material_id))
        else:
            cur.execute("""
                INSERT INTO kit_items (kit_id, material_id, quantity, unit, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (kit_id, material_id, quantity, unit, notes))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления позиции в комплект: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def remove_kit_item(kit_item_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM kit_items WHERE id = %s", (kit_item_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления позиции из комплекта: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def get_kit_items(kit_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ki.id, ki.material_id, ki.quantity, ki.unit, ki.notes,
               m.name, m.unit, m.retail_price
        FROM kit_items ki
        JOIN materials m ON m.id = ki.material_id
        WHERE ki.kit_id = %s
    """, (kit_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0],
        'material_id': r[1],
        'quantity': float(r[2]) if r[2] else 1,
        'unit': r[3] or '',
        'notes': r[4] or '',
        'material_name': r[5],
        'material_unit': r[6],
        'material_price': float(r[7]) if r[7] else 0
    } for r in rows]


# ============================================================
# 8. ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_beam_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, height_mm, width_mm, weight_kg_per_m FROM beam_types ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_beam_by_name(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, height_mm, width_mm, weight_kg_per_m,
               COALESCE(purchase_price, 0), COALESCE(retail_price, 0)
        FROM beam_types
        WHERE name = %s
    """, (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            'id': row[0], 'name': row[1],
            'height_mm': row[2], 'width_mm': row[3],
            'weight_kg_per_m': float(row[4]),
            'purchase_price': float(row[5]),
            'retail_price': float(row[6])
        }
    return None


def get_all_beam_types_full():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, height_mm, width_mm, weight_kg_per_m,
               COALESCE(purchase_price, 0), COALESCE(retail_price, 0)
        FROM beam_types ORDER BY name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'name': r[1],
        'height_mm': r[2], 'width_mm': r[3],
        'weight_kg_per_m': float(r[4]),
        'purchase_price': float(r[5]),
        'retail_price': float(r[6])
    } for r in rows]


def update_beam_prices(beam_name, purchase_price, retail_price):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE beam_types
            SET purchase_price = %s, retail_price = %s
            WHERE name = %s
        """, (purchase_price, retail_price, beam_name))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления цен балки: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def get_materials():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sku, name, unit, weight_per_unit, purchase_price, retail_price, description,
               parent_id, is_category, is_kit, COALESCE(consumption_per_m2, 0)
        FROM materials 
        WHERE is_category = FALSE
        ORDER BY name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'sku': r[1], 'name': r[2], 'unit': r[3],
        'weight_per_unit': r[4], 'purchase_price': r[5],
        'retail_price': r[6], 'description': r[7],
        'parent_id': r[8], 'is_category': r[9], 'is_kit': r[10],
        'consumption_per_m2': float(r[11]) if r[11] else 0
    } for r in rows]


def get_materials_hierarchy():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, unit, weight_per_unit, purchase_price, retail_price, 
               description, parent_id, is_category, is_kit, COALESCE(consumption_per_m2, 0)
        FROM materials 
        ORDER BY parent_id NULLS FIRST, name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{
        'id': r[0],
        'name': r[1],
        'unit': r[2] or '',
        'weight_per_unit': float(r[3]) if r[3] else 0,
        'purchase_price': float(r[4]) if r[4] else 0,
        'retail_price': float(r[5]) if r[5] else 0,
        'description': r[6] or '',
        'parent_id': r[7],
        'is_category': r[8] or False,
        'is_kit': r[9] or False,
        'consumption_per_m2': float(r[10]) if r[10] else 0
    } for r in rows]


def get_material_by_id(material_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sku, name, unit, weight_per_unit, purchase_price, retail_price, description,
               parent_id, is_category, is_kit, COALESCE(consumption_per_m2, 0)
        FROM materials WHERE id = %s
    """, (material_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            'id': row[0], 'sku': row[1], 'name': row[2], 'unit': row[3],
            'weight_per_unit': row[4], 'purchase_price': row[5],
            'retail_price': row[6], 'description': row[7],
            'parent_id': row[8], 'is_category': row[9], 'is_kit': row[10],
            'consumption_per_m2': float(row[11]) if row[11] else 0
        }
    return None


def add_material(name, unit, weight, purchase_price, retail_price, sku=None, description='', parent_id=None,
                 consumption_per_m2=0):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO materials (name, unit, weight_per_unit, purchase_price, retail_price, sku, description, parent_id, consumption_per_m2)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, unit, weight, purchase_price, retail_price, sku, description, parent_id, consumption_per_m2))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления материала: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def update_material(material_id, name, unit, weight, purchase_price, retail_price, sku=None, description='',
                    parent_id=None, consumption_per_m2=0):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE materials
            SET name = %s, unit = %s, weight_per_unit = %s,
                purchase_price = %s, retail_price = %s, sku = %s, description = %s, parent_id = %s, consumption_per_m2 = %s
            WHERE id = %s
        """, (
        name, unit, weight, purchase_price, retail_price, sku, description, parent_id, consumption_per_m2, material_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления материала: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_material(material_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM materials WHERE id = %s", (material_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления материала: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def add_category(name, parent_id=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO materials (name, unit, is_category, parent_id, description)
            VALUES (%s, 'категория', TRUE, %s, %s)
        """, (name, parent_id, f'Категория: {name}'))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления категории: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def update_category(category_id, new_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE materials SET name = %s, description = %s
            WHERE id = %s AND is_category = TRUE
        """, (new_name, f'Категория: {new_name}', category_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка переименования категории: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_category(category_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM materials WHERE parent_id = %s", (category_id,))
        cur.execute("DELETE FROM materials WHERE id = %s", (category_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления категории: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def get_materials_by_category(category_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, unit, retail_price
        FROM materials 
        WHERE parent_id = %s AND is_category = FALSE AND is_kit = FALSE
        ORDER BY name
    """, (category_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'unit': r[2], 'retail_price': r[3]} for r in rows]


def get_units():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM units ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'id': r[0], 'name': r[1]} for r in rows]


# ============================================================
# 9. ЕДИНИЦЫ ИЗМЕРЕНИЯ
# ============================================================

def add_unit(name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO units (name) VALUES (%s)", (name,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления единицы измерения: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_unit(unit_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM units WHERE id = %s", (unit_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления единицы измерения: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


# ============================================================
# 10. КЛИЕНТЫ И АДРЕСА
# ============================================================
def get_clients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, last_name, first_name, middle_name, organization_name,
               phone1, phone2, email, messenger
        FROM clients ORDER BY last_name, first_name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'type': r[1], 'last_name': r[2] or '',
        'first_name': r[3] or '', 'middle_name': r[4] or '',
        'organization_name': r[5] or '', 'phone1': r[6] or '',
        'phone2': r[7] or '', 'email': r[8] or '', 'messenger': r[9] or ''
    } for r in rows]


def get_client_by_id(client_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, last_name, first_name, middle_name, organization_name,
               phone1, phone2, email, messenger
        FROM clients WHERE id = %s
    """, (client_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            'id': row[0], 'type': row[1], 'last_name': row[2] or '',
            'first_name': row[3] or '', 'middle_name': row[4] or '',
            'organization_name': row[5] or '', 'phone1': row[6] or '',
            'phone2': row[7] or '', 'email': row[8] or '', 'messenger': row[9] or ''
        }
    return None


def add_client(type, last_name, first_name, middle_name, organization_name, phone1, phone2, email, messenger):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO clients (type, last_name, first_name, middle_name, organization_name,
                                 phone1, phone2, email, messenger)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (type, last_name, first_name, middle_name, organization_name, phone1, phone2, email, messenger))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления клиента: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def update_client(client_id, type, last_name, first_name, middle_name, organization_name, phone1, phone2, email,
                  messenger):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE clients
            SET type = %s, last_name = %s, first_name = %s, middle_name = %s,
                organization_name = %s, phone1 = %s, phone2 = %s, email = %s, messenger = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (type, last_name, first_name, middle_name, organization_name, phone1, phone2, email, messenger, client_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления клиента: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_client(client_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM clients WHERE id = %s", (client_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления клиента: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def get_addresses(client_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, client_id, index, region, city, street, house, building, apartment
        FROM addresses WHERE client_id = %s ORDER BY id
    """, (client_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'client_id': r[1], 'index': r[2] or '',
        'region': r[3] or '', 'city': r[4] or '', 'street': r[5] or '',
        'house': r[6] or '', 'building': r[7] or '', 'apartment': r[8] or ''
    } for r in rows]


def get_address_by_id(address_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, client_id, index, region, city, street, house, building, apartment
        FROM addresses WHERE id = %s
    """, (address_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            'id': row[0], 'client_id': row[1], 'index': row[2] or '',
            'region': row[3] or '', 'city': row[4] or '', 'street': row[5] or '',
            'house': row[6] or '', 'building': row[7] or '', 'apartment': row[8] or ''
        }
    return None


def add_address(client_id, index, region, city, street, house, building, apartment):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO addresses (client_id, index, region, city, street, house, building, apartment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (client_id, index, region, city, street, house, building, apartment))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления адреса: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def update_address(address_id, index, region, city, street, house, building, apartment):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE addresses
            SET index = %s, region = %s, city = %s, street = %s,
                house = %s, building = %s, apartment = %s
            WHERE id = %s
        """, (index, region, city, street, house, building, apartment, address_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления адреса: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_address(address_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM addresses WHERE id = %s", (address_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления адреса: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


# ============================================================
# 11. ПОИСК КЛИЕНТОВ
# ============================================================
def get_all_clients_short():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, last_name, first_name, middle_name, organization_name, phone1
        FROM clients ORDER BY last_name, first_name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'last_name': r[1] or '', 'first_name': r[2] or '',
        'middle_name': r[3] or '', 'organization_name': r[4] or '',
        'phone1': r[5] or ''
    } for r in rows]


def search_clients(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT c.id, c.last_name, c.first_name, c.middle_name,
                        c.organization_name, c.phone1
        FROM clients c
        LEFT JOIN addresses a ON a.client_id = c.id
        WHERE c.last_name ILIKE %s OR c.first_name ILIKE %s OR c.middle_name ILIKE %s
              OR c.organization_name ILIKE %s OR c.phone1 ILIKE %s OR c.phone2 ILIKE %s
              OR c.email ILIKE %s OR a.city ILIKE %s OR a.street ILIKE %s
        ORDER BY c.last_name, c.first_name LIMIT 100
    """, tuple([f'%{query}%'] * 9))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'last_name': r[1] or '', 'first_name': r[2] or '',
        'middle_name': r[3] or '', 'organization_name': r[4] or '',
        'phone1': r[5] or ''
    } for r in rows]


def get_client_addresses(client_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, city, street, house, apartment
        FROM addresses WHERE client_id = %s
    """, (client_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0], 'city': r[1] or '', 'street': r[2] or '',
        'house': r[3] or '', 'apartment': r[4] or ''
    } for r in rows]


# ============================================================
# 12. КОМПЛЕКТЫ (ОСНОВНЫЕ)
# ============================================================
def get_all_kits():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, description, retail_price
        FROM kits
        ORDER BY name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0],
        'name': r[1],
        'description': r[2] or '',
        'retail_price': float(r[3]) if r[3] else 0
    } for r in rows]


def get_kit_by_id(kit_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, description, retail_price
        FROM kits WHERE id = %s
    """, (kit_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    kit = {
        'id': row[0],
        'name': row[1],
        'description': row[2] or '',
        'retail_price': float(row[3]) if row[3] else 0,
        'items': []
    }

    cur.execute("""
        SELECT ki.id, ki.material_id, ki.quantity, ki.unit, ki.notes,
               m.name, m.unit, m.retail_price
        FROM kit_items ki
        JOIN materials m ON m.id = ki.material_id
        WHERE ki.kit_id = %s
    """, (kit_id,))
    items = cur.fetchall()
    cur.close()
    conn.close()

    for it in items:
        kit['items'].append({
            'kit_item_id': it[0],
            'material_id': it[1],
            'quantity': float(it[2]) if it[2] else 1,
            'unit': it[3] or '',
            'notes': it[4] or '',
            'material_name': it[5],
            'material_unit': it[6],
            'material_price': float(it[7]) if it[7] else 0
        })

    return kit


def add_kit(name, description='', retail_price=0):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO kits (name, description, retail_price)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, description, retail_price))
        kit_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return kit_id
    except Exception as e:
        print(f"❌ Ошибка добавления комплекта: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return None


def update_kit(kit_id, name, description='', retail_price=0):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE kits
            SET name = %s, description = %s, retail_price = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (name, description, retail_price, kit_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления комплекта: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_kit(kit_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM kits WHERE id = %s", (kit_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления комплекта: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


# ============================================================
# 13. СМЕТЫ
# ============================================================
def save_estimate_with_kit(project_id, estimate_data, items, client_id=None,
                           client_name='Не указан', client_address='Не указан'):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO estimates (project_id, number, date, total_amount, 
                                   client_id, client_name, client_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (project_id, estimate_data['number'], estimate_data['date'],
              estimate_data['total_amount'], client_id, client_name, client_address))
        estimate_id = cur.fetchone()[0]

        item_id_map = {}

        for idx, item in enumerate(items):
            if item.get('kit_parent_id') is not None:
                continue

            cur.execute("""
                INSERT INTO estimate_items (
                    estimate_id, material_name, length_mm, quantity, unit, 
                    price, total, weight_kg, note, is_kit, kit_parent_id, is_paint
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                estimate_id, item['name'], item.get('length', 0), item['quantity'], item['unit'],
                item['price'], item['total'], item.get('weight', 0), item.get('note', ''),
                item.get('is_kit', False), None,
                item.get('is_paint', False)
            ))

            real_id = cur.fetchone()[0]
            item_id_map[idx] = real_id

            if item.get('is_kit', False):
                print(f"  📦 Комплект сохранён: idx={idx} -> real_id={real_id}")

        for item in items:
            parent_idx = item.get('kit_parent_id')
            if parent_idx is None:
                continue

            real_parent_id = item_id_map.get(parent_idx)
            if real_parent_id is None:
                print(f"  ⚠️ Не найден родитель для дочернего элемента (parent_idx={parent_idx})")
                continue

            cur.execute("""
                INSERT INTO estimate_items (
                    estimate_id, material_name, length_mm, quantity, unit, 
                    price, total, weight_kg, note, is_kit, kit_parent_id, is_paint
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                estimate_id, item['name'], item.get('length', 0), item['quantity'], item['unit'],
                item['price'], item['total'], item.get('weight', 0), item.get('note', ''),
                False, real_parent_id,
                item.get('is_paint', False)
            ))
            print(f"    └─ Дочерний элемент сохранён: {item['name']} -> parent_id={real_parent_id}")

        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Смета сохранена (ID: {estimate_id})")
        return estimate_id
    except Exception as e:
        print(f"❌ Ошибка сохранения сметы: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return None


def save_estimate(project_id, estimate_data, items, client_id=None,
                  client_name='Не указан', client_address='Не указан'):
    return save_estimate_with_kit(project_id, estimate_data, items, client_id,
                                  client_name, client_address)


def get_estimates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, number, date, total_amount, client_name
        FROM estimates
        ORDER BY date DESC, id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0],
        'number': r[1] or f"СМ-{r[0]}",
        'date': r[2].strftime('%d.%m.%Y') if r[2] else '',
        'total_amount': float(r[3]) if r[3] is not None else 0.0,
        'client_name': r[4] or 'Не указан'
    } for r in rows]


def get_estimate_by_id(estimate_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, number, date, total_amount, project_id, client_id, client_name, client_address
        FROM estimates WHERE id = %s
    """, (estimate_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    estimate = {
        'id': row[0],
        'number': row[1],
        'date': row[2],
        'total_amount': float(row[3]) if row[3] else 0,
        'project_id': row[4],
        'client_id': row[5],
        'client_name': row[6] or 'Не указан',
        'client_address': row[7] or 'Не указан',
        'items': []
    }

    cur.execute("""
        SELECT id, material_name, length_mm, quantity, unit, price, total, weight_kg, note, is_kit, kit_parent_id, is_paint
        FROM estimate_items WHERE estimate_id = %s
        ORDER BY id
    """, (estimate_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    kit_items = {}
    regular_items = []

    for r in rows:
        item = {
            'id': r[0],
            'name': r[1],
            'length': r[2] or 0,
            'quantity': float(r[3]) if r[3] else 1,
            'unit': r[4] or 'шт',
            'price': float(r[5]) if r[5] else 0,
            'total': float(r[6]) if r[6] else 0,
            'weight': float(r[7]) if r[7] else 0,
            'note': r[8] or '',
            'is_kit': r[9] or False,
            'kit_parent_id': r[10],
            'is_paint': r[11] or False
        }

        if item['is_kit']:
            kit_items[item['id']] = {
                'kit': item,
                'children': []
            }
        elif item['kit_parent_id'] is not None and item['kit_parent_id'] in kit_items:
            kit_items[item['kit_parent_id']]['children'].append(item)
        else:
            regular_items.append(item)

    for kit_id, kit_data in kit_items.items():
        estimate['items'].append(kit_data['kit'])
        for child in kit_data['children']:
            estimate['items'].append(child)

    estimate['items'].extend(regular_items)

    return estimate


def delete_estimate(estimate_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM estimates WHERE id = %s", (estimate_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления сметы: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


# ============================================================
# 14. ПОЛЬЗОВАТЕЛИ
# ============================================================
import hashlib
import secrets


def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password, password_hash, salt):
    return hash_password(password, salt) == password_hash


def authenticate_user(login, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, login, password_hash, salt, full_name, position, role, is_active
        FROM users WHERE login = %s
    """, (login,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    user_id, login_db, password_hash, salt, full_name, position, role, is_active = row

    if not is_active:
        cur.close()
        conn.close()
        return None

    if not verify_password(password, password_hash, salt):
        cur.close()
        conn.close()
        return None

    cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {
        'id': user_id,
        'login': login_db,
        'full_name': full_name,
        'position': position,
        'role': role
    }


def get_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, login, full_name, position, role, is_active, 
               created_at, last_login
        FROM users ORDER BY login
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        'id': r[0],
        'login': r[1],
        'full_name': r[2],
        'position': r[3] or '',
        'role': r[4],
        'is_active': r[5],
        'created_at': r[6],
        'last_login': r[7]
    } for r in rows]


def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, login, full_name, position, role, is_active
        FROM users WHERE id = %s
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {
            'id': row[0], 'login': row[1], 'full_name': row[2],
            'position': row[3] or '', 'role': row[4], 'is_active': row[5]
        }
    return None


def add_user(login, password, full_name, position='', role='manager'):
    conn = get_connection()
    cur = conn.cursor()
    try:
        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        cur.execute("""
            INSERT INTO users (login, password_hash, salt, full_name, position, role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (login, password_hash, salt, full_name, position, role))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def update_user(user_id, full_name, position, role, is_active, new_password=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if new_password:
            salt = secrets.token_hex(16)
            password_hash = hash_password(new_password, salt)
            cur.execute("""
                UPDATE users 
                SET full_name = %s, position = %s, role = %s, is_active = %s,
                    password_hash = %s, salt = %s
                WHERE id = %s
            """, (full_name, position, role, is_active, password_hash, salt, user_id))
        else:
            cur.execute("""
                UPDATE users 
                SET full_name = %s, position = %s, role = %s, is_active = %s
                WHERE id = %s
            """, (full_name, position, role, is_active, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления пользователя: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления пользователя: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        return False