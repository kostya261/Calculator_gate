from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class ClientSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор клиента")
        self.setMinimumSize(900, 500)

        self.selected_client_id = None
        self.selected_client_name = None

        layout = QVBoxLayout(self)

        # ===== Строка поиска =====
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Фамилия, имя, организация, телефон, адрес...")
        self.search_input.returnPressed.connect(self.search_clients)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.search_clients)
        search_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("Сброс")
        self.clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_btn)

        layout.addLayout(search_layout)

        # ===== Таблица клиентов =====
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Фамилия", "Имя", "Отчество", "Организация", "Телефон"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 180)
        self.table.doubleClicked.connect(self.select_client)
        layout.addWidget(self.table)

        # ===== Кнопки =====
        btn_layout = QHBoxLayout()

        self.select_btn = QPushButton("✅ Выбрать")
        self.select_btn.clicked.connect(self.select_client)
        btn_layout.addWidget(self.select_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()
        self.count_label = QLabel("Всего клиентов: 0")
        btn_layout.addWidget(self.count_label)

        layout.addLayout(btn_layout)

        # Загружаем всех клиентов
        self.search_clients()

    def search_clients(self):
        """Поиск клиентов по тексту"""
        query = self.search_input.text().strip()

        if query:
            clients = db.search_clients(query)
        else:
            clients = db.get_all_clients_short()

        self.table.setRowCount(len(clients))
        for row, c in enumerate(clients):
            self.table.setItem(row, 0, QTableWidgetItem(str(c['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(c['last_name']))
            self.table.setItem(row, 2, QTableWidgetItem(c['first_name']))
            self.table.setItem(row, 3, QTableWidgetItem(c['middle_name']))
            self.table.setItem(row, 4, QTableWidgetItem(c['organization_name']))
            self.table.setItem(row, 5, QTableWidgetItem(c['phone1']))

        self.count_label.setText(f"Всего клиентов: {len(clients)}")

    def clear_search(self):
        self.search_input.clear()
        self.search_clients()

    def select_client(self):
        """Выбор клиента из таблицы"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента из списка!")
            return

        id_item = self.table.item(row, 0)
        if not id_item:
            return

        self.selected_client_id = int(id_item.text())

        # Формируем имя клиента
        last = self.table.item(row, 1).text() or ''
        first = self.table.item(row, 2).text() or ''
        middle = self.table.item(row, 3).text() or ''
        org = self.table.item(row, 4).text() or ''

        if org:
            self.selected_client_name = org
        else:
            name_parts = [last, first, middle]
            name_parts = [p for p in name_parts if p]
            self.selected_client_name = ' '.join(name_parts) if name_parts else "Без имени"

        self.accept()