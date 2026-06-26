# unit_dialog.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class UnitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справочник единиц измерения")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_unit)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_unit)
        btn_layout.addWidget(self.delete_btn)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        units = db.get_units()
        self.table.setRowCount(len(units))
        for row, unit in enumerate(units):
            self.table.setItem(row, 0, QTableWidgetItem(str(unit['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(unit['name']))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def add_unit(self):
        name, ok = QInputDialog.getText(self, "Новая единица", "Введите название единицы измерения:")
        if ok and name.strip():
            if db.add_unit(name.strip()):
                self.load_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить единицу!")

    def delete_unit(self):
        unit_id = self.get_selected_id()
        if not unit_id:
            QMessageBox.warning(self, "Ошибка", "Выберите единицу для удаления!")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранную единицу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if db.delete_unit(unit_id):
                self.load_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить единицу!")