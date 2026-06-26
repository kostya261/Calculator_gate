from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class AddressDialog(QDialog):
    def __init__(self, client_id, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle("Адреса клиента")
        self.setMinimumSize(750, 300)

        layout = QVBoxLayout(self)

        client = db.get_client_by_id(client_id)
        if client:
            info_text = f"Клиент: "
            if client['type'] == 'individual':
                info_text += f"{client['last_name']} {client['first_name']} {client['middle_name']}".strip()
            else:
                info_text += client['organization_name']
            self.info_label = QLabel(info_text)
            self.info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Индекс", "Область", "Город", "Улица", "Дом", "Строение", "Квартира"]
        )
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 70)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Добавить адрес")
        self.add_btn.clicked.connect(self.add_address)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_address)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_address)
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
        addresses = db.get_addresses(self.client_id)
        self.table.setRowCount(len(addresses))
        for row, addr in enumerate(addresses):
            self.table.setItem(row, 0, QTableWidgetItem(str(addr['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(addr['index']))
            self.table.setItem(row, 2, QTableWidgetItem(addr['region']))
            self.table.setItem(row, 3, QTableWidgetItem(addr['city']))
            self.table.setItem(row, 4, QTableWidgetItem(addr['street']))
            self.table.setItem(row, 5, QTableWidgetItem(addr['house']))
            self.table.setItem(row, 6, QTableWidgetItem(addr['building']))
            self.table.setItem(row, 7, QTableWidgetItem(addr['apartment']))
        self.table.resizeRowsToContents()

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def add_address(self):
        dialog = AddressEditDialog(self.client_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_address(self):
        address_id = self.get_selected_id()
        if address_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите адрес!")
            return
        dialog = AddressEditDialog(self.client_id, self, address_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def delete_address(self):
        address_id = self.get_selected_id()
        if address_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите адрес!")
            return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранный адрес?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if db.delete_address(address_id):
                self.load_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить адрес!")


class AddressEditDialog(QDialog):
    def __init__(self, client_id, parent=None, address_id=None):
        super().__init__(parent)
        self.client_id = client_id
        self.address_id = address_id
        self.setWindowTitle("Редактирование адреса" if address_id else "Новый адрес")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.index_edit = QLineEdit()
        self.index_edit.setPlaceholderText("123456")
        form_layout.addRow("Индекс:", self.index_edit)

        self.region_edit = QLineEdit()
        self.region_edit.setPlaceholderText("Московская область")
        form_layout.addRow("Область:", self.region_edit)

        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("Москва")
        form_layout.addRow("Город:", self.city_edit)

        self.street_edit = QLineEdit()
        self.street_edit.setPlaceholderText("ул. Ленина")
        form_layout.addRow("Улица:", self.street_edit)

        self.house_edit = QLineEdit()
        self.house_edit.setPlaceholderText("10")
        form_layout.addRow("Дом:", self.house_edit)

        self.building_edit = QLineEdit()
        self.building_edit.setPlaceholderText("строение 1 (опционально)")
        form_layout.addRow("Строение:", self.building_edit)

        self.apartment_edit = QLineEdit()
        self.apartment_edit.setPlaceholderText("5 (опционально)")
        form_layout.addRow("Квартира:", self.apartment_edit)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        if address_id:
            self.load_data()

    def load_data(self):
        address = db.get_address_by_id(self.address_id)
        if address:
            self.index_edit.setText(address['index'])
            self.region_edit.setText(address['region'])
            self.city_edit.setText(address['city'])
            self.street_edit.setText(address['street'])
            self.house_edit.setText(address['house'])
            self.building_edit.setText(address['building'])
            self.apartment_edit.setText(address['apartment'])

    def save(self):
        index = self.index_edit.text().strip()
        region = self.region_edit.text().strip()
        city = self.city_edit.text().strip()
        street = self.street_edit.text().strip()
        house = self.house_edit.text().strip()
        building = self.building_edit.text().strip()
        apartment = self.apartment_edit.text().strip()

        if not city or not street or not house:
            QMessageBox.warning(self, "Ошибка", "Город, улица и дом обязательны!")
            return

        if self.address_id:
            success = db.update_address(self.address_id, index, region, city, street, house, building, apartment)
        else:
            success = db.add_address(self.client_id, index, region, city, street, house, building, apartment)

        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить адрес!")