from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import db
import json
import os
import base64

# Путь к файлу конфигурации
CONFIG_FILE = "user_config.json"


def load_user_config():
    """Загружает сохранённые данные пользователя"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Декодируем пароль
                if 'password' in data and data['password']:
                    try:
                        data['password'] = base64.b64decode(data['password']).decode('utf-8')
                    except:
                        data['password'] = ''
                return data
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
    return {}


def save_user_config(login, password, remember):
    """Сохраняет данные пользователя"""
    if remember:
        # Кодируем пароль в base64 (простое шифрование)
        encoded_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        data = {
            'login': login,
            'password': encoded_password,
            'remember': True
        }
    else:
        data = {
            'login': '',
            'password': '',
            'remember': False
        }

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")


class LoginDialog(QDialog):
    """Окно авторизации пользователя"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(420, 340)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.current_user = None
        self.attempts = 0
        self.max_attempts = 5

        # Загружаем сохранённые данные
        self.saved_config = load_user_config()

        # Светлая тема
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                padding: 6px;
                border: 1px solid #999999;
                border-radius: 4px;
                font-size: 13px;
                min-height: 18px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)  # Уменьшил с 12 до 8
        layout.setContentsMargins(25, 20, 25, 20)  # Уменьшил отступы

        # Заголовок
        title = QLabel("🚪 Вход в систему")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        layout.addWidget(title)

        subtitle = QLabel("Конструктор откатных ворот")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 11px; color: #555555;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)  # Уменьшил с 15 до 10

        # Логин
        login_label = QLabel("Логин:")
        login_label.setStyleSheet("font-weight: bold; color: #000000; margin-bottom: 2px;")
        layout.addWidget(login_label)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин...")
        # Подставляем сохранённый логин
        if self.saved_config.get('login'):
            self.login_input.setText(self.saved_config['login'])
        layout.addWidget(self.login_input)

        layout.addSpacing(5)  # Уменьшил с 10 до 5

        # Пароль
        password_label = QLabel("Пароль:")
        password_label.setStyleSheet("font-weight: bold; color: #000000; margin-bottom: 2px;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.try_login)
        # Подставляем сохранённый пароль
        if self.saved_config.get('password'):
            self.password_input.setText(self.saved_config['password'])
        layout.addWidget(self.password_input)

        layout.addSpacing(5)

        # Галочка "Запомнить меня"
        self.remember_check = QCheckBox("Запомнить меня")
        self.remember_check.setStyleSheet("color: #000000;")
        # Устанавливаем состояние из конфигурации
        self.remember_check.setChecked(self.saved_config.get('remember', False))
        layout.addWidget(self.remember_check)

        # Сообщение об ошибке
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #cc0000; font-size: 11px; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        layout.addSpacing(5)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.login_btn = QPushButton("🔑 Войти")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.login_btn.clicked.connect(self.try_login)
        btn_layout.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("❌ Выход")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c01212;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # Подсказка
        hint = QLabel("По умолчанию: admin / admin")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: 10px; color: #888888; font-style: italic;")
        layout.addWidget(hint)

        # Фокус на поле логина (если нет сохранённого)
        if not self.saved_config.get('login'):
            self.login_input.setFocus()
        else:
            # Если есть сохранённый логин, фокус на кнопке "Войти"
            self.login_btn.setFocus()

    def try_login(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            self.error_label.setText("Введите логин и пароль!")
            return

        self.attempts += 1
        user = db.authenticate_user(login, password)

        if user:
            self.current_user = user
            print(f"✅ Пользователь вошёл: {user['full_name']} ({user['login']})")

            # Сохраняем данные, если отмечена галочка
            remember = self.remember_check.isChecked()
            save_user_config(login, password, remember)

            self.accept()
        else:
            remaining = self.max_attempts - self.attempts
            if remaining > 0:
                self.error_label.setText(f"❌ Неверный логин или пароль! Осталось попыток: {remaining}")
            else:
                self.error_label.setText("❌ Превышено количество попыток. Программа будет закрыта.")
                self.login_btn.setEnabled(False)
                self.password_input.setEnabled(False)
                self.login_input.setEnabled(False)
                QTimer.singleShot(2000, self.reject)

            self.password_input.clear()
            self.password_input.setFocus()

    def get_current_user(self):
        return self.current_user