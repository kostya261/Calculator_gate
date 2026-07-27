from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class UserDialog(QDialog):
    """Справочник пользователей (доступен только админу)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление пользователями")
        self.setMinimumSize(850, 450)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "ФИО", "Должность", "Роль", "Статус"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 100)
        self.table.doubleClicked.connect(self.edit_user)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_user)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_user)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(self.delete_btn)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()
        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        users = db.get_users()
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(u['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(u['login']))
            self.table.setItem(row, 2, QTableWidgetItem(u['full_name']))
            self.table.setItem(row, 3, QTableWidgetItem(u['position']))
            self.table.setItem(row, 4, QTableWidgetItem(u['role']))
            status = "✅ Активен" if u['is_active'] else "❌ Заблокирован"
            self.table.setItem(row, 5, QTableWidgetItem(status))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def add_user(self):
        dialog = UserEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_user(self):
        user_id = self.get_selected_id()
        if not user_id:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя!")
            return
        dialog = UserEditDialog(self, user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_user(self):
        user_id = self.get_selected_id()
        if not user_id:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя!")
            return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить пользователя?")
        if reply == QMessageBox.StandardButton.Yes:
            if db.delete_user(user_id):
                self.load_data()
                QMessageBox.information(self, "Готово", "Пользователь удалён.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить пользователя.")


class UserEditDialog(QDialog):
    """Диалог добавления/редактирования пользователя"""
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Редактирование" if user_id else "Новый пользователь")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.login_edit = QLineEdit()
        form.addRow("Логин:", self.login_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Оставьте пустым, чтобы не менять")
        form.addRow("Пароль:", self.password_edit)

        self.name_edit = QLineEdit()
        form.addRow("ФИО:", self.name_edit)

        self.position_edit = QLineEdit()
        form.addRow("Должность:", self.position_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["manager", "admin"])
        form.addRow("Роль:", self.role_combo)

        self.active_check = QCheckBox("Активен")
        self.active_check.setChecked(True)
        form.addRow("", self.active_check)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if user_id:
            self.load_data()

    def load_data(self):
        user = db.get_user_by_id(self.user_id)
        if user:
            self.login_edit.setText(user['login'])
            self.login_edit.setReadOnly(True)
            self.name_edit.setText(user['full_name'])
            self.position_edit.setText(user['position'])
            self.role_combo.setCurrentText(user['role'])
            self.active_check.setChecked(user['is_active'])

    def save(self):
        login = self.login_edit.text().strip()
        name = self.name_edit.text().strip()
        position = self.position_edit.text().strip()
        role = self.role_combo.currentText()
        active = self.active_check.isChecked()
        new_pass = self.password_edit.text().strip() or None

        if not login or not name:
            QMessageBox.warning(self, "Ошибка", "Логин и ФИО обязательны!")
            return

        if self.user_id:
            success = db.update_user(self.user_id, name, position, role, active, new_pass)
        else:
            if not new_pass:
                QMessageBox.warning(self, "Ошибка", "Для нового пользователя укажите пароль!")
                return
            success = db.add_user(login, new_pass, name, position, role)

        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить!")