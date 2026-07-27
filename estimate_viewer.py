from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class EstimateViewer(QDialog):
    def __init__(self, estimate_id, parent=None):
        super().__init__(parent)
        self.estimate_id = estimate_id
        self.setWindowTitle("Просмотр сметы")
        self.setMinimumSize(900, 500)

        layout = QVBoxLayout(self)

        estimate = db.get_estimate_by_id(estimate_id)
        if not estimate:
            QMessageBox.warning(self, "Ошибка", "Смета не найдена!")
            self.close()
            return

        # Информация о смете
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"<b>Номер:</b> {estimate['number']}"))
        info_layout.addStretch()
        info_layout.addWidget(QLabel(f"<b>Дата:</b> {estimate['date']}"))
        info_layout.addStretch()
        info_layout.addWidget(QLabel(f"<b>Сумма:</b> {float(estimate['total_amount']):.2f} руб"))
        layout.addLayout(info_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["№", "Наименование", "Кол-во", "Ед.", "Цена (руб)", "Сумма (руб)"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 300)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)

        items = estimate.get('items', [])
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(item['name']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(item['unit']))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['price']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item['total']:.2f}"))

        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)