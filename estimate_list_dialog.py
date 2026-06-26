from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import db


class EstimateListDialog(QDialog):
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Список смет")
        self.setMinimumSize(800, 400)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Дата", "Клиент", "Сумма"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 250)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.doubleClicked.connect(self.edit_estimate)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_estimate)
        btn_layout.addWidget(self.edit_btn)

        self.view_btn = QPushButton("📋 Просмотр")
        self.view_btn.clicked.connect(self.view_estimate)
        btn_layout.addWidget(self.view_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_estimate)
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
        try:
            estimates = db.get_estimates()
            self.table.setRowCount(len(estimates))
            for row, est in enumerate(estimates):
                self.table.setItem(row, 0, QTableWidgetItem(str(est['id'])))
                self.table.setItem(row, 1, QTableWidgetItem(est['number']))
                self.table.setItem(row, 2, QTableWidgetItem(est['date']))
                self.table.setItem(row, 3, QTableWidgetItem(est['client_name']))
                self.table.setItem(row, 4, QTableWidgetItem(f"{float(est['total_amount']):.2f}"))
            self.table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сметы:\n{e}")

    def get_selected_ids(self):
        """Возвращает список ID выбранных смет"""
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())

        ids = []
        for row in rows:
            id_item = self.table.item(row, 0)
            if id_item:
                try:
                    ids.append(int(id_item.text()))
                except ValueError:
                    pass
        return ids

    def get_selected_id(self):
        """Возвращает ID первой выбранной сметы (для совместимости)"""
        ids = self.get_selected_ids()
        return ids[0] if ids else None

    def edit_estimate(self):
        estimate_id = self.get_selected_id()
        if not estimate_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смету!")
            return

        try:
            from estimate_dialog import EstimateDialog
            import math

            estimate = db.get_estimate_by_id(estimate_id)
            if not estimate:
                QMessageBox.warning(self, "Ошибка", "Смета не найдена!")
                return

            materials = []
            kit_children = {}

            for item in estimate['items']:
                kit_parent_id = item.get('kit_parent_id')
                if kit_parent_id is not None:
                    if kit_parent_id not in kit_children:
                        kit_children[kit_parent_id] = []
                    kit_children[kit_parent_id].append(item)

            for item in estimate['items']:
                kit_parent_id = item.get('kit_parent_id')
                if kit_parent_id is not None:
                    continue

                is_kit = item.get('is_kit', False)
                is_paint = item.get('is_paint', False)

                name = item.get('name', 'Без имени')
                length_mm = float(item.get('length', 0))
                quantity = float(item.get('quantity', 1))
                price = float(item.get('price', 0))
                weight = float(item.get('weight', 0))
                unit = item.get('unit', 'м.п.')

                if not is_kit and not is_paint and length_mm > 0:
                    sticks = max(1, math.ceil(length_mm / 6000))
                    remainder_mm = (sticks * 6000) - length_mm
                    remainder_for_client = remainder_mm % 1000
                    length_for_payment_mm = length_mm + remainder_for_client
                else:
                    sticks = 1
                    remainder_mm = 0
                    remainder_for_client = 0
                    length_for_payment_mm = length_mm

                kit_items_list = []
                if is_kit:
                    children = kit_children.get(item.get('id'), [])
                    for child in children:
                        kit_items_list.append({
                            'material_name': child.get('name', ''),
                            'quantity': float(child.get('quantity', 1)),
                            'unit': child.get('unit', 'шт'),
                            'material_price': float(child.get('price', 0))
                        })

                    if kit_items_list:
                        price = sum(kit['quantity'] * kit['material_price'] for kit in kit_items_list)

                mat = {
                    'name': name,
                    'profile': name,
                    'length_mm': length_mm,
                    'length_for_payment_mm': length_for_payment_mm,
                    'sticks': sticks,
                    'remainder_mm': remainder_mm,
                    'remainder_for_client': remainder_for_client,
                    'weight': weight,
                    'price': price,
                    'unit': unit,
                    'is_paint': is_paint,
                    'is_kit': is_kit,
                    'kit_items': kit_items_list
                }

                materials.append(mat)

            if not materials:
                QMessageBox.warning(self, "Ошибка", "Нет данных для отображения!")
                return

            client_name = estimate.get('client_name', 'Не указан')
            client_address = estimate.get('client_address', 'Не указан')
            client_id = estimate.get('client_id')

            dialog = EstimateDialog(
                materials,
                client_name,
                client_address,
                self,
                client_id=client_id,
                current_user=self.current_user
            )
            dialog.setWindowTitle(f"Смета {estimate['number']} от {estimate['date']}")

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть смету:\n{e}\n\n{traceback.format_exc()}")

    def view_estimate(self):
        estimate_id = self.get_selected_id()
        if not estimate_id:
            QMessageBox.warning(self, "Ошибка", "Выберите смету!")
            return

        try:
            estimate = db.get_estimate_by_id(estimate_id)
            if not estimate:
                QMessageBox.warning(self, "Ошибка", "Смета не найдена!")
                return

            items_text = ""
            for idx, item in enumerate(estimate.get('items', []), 1):
                if item.get('is_kit', False):
                    items_text += f"{idx}. 📦 {item['name']} — {float(item['total']):.2f} руб (комплект)\n"
                elif item.get('kit_parent_id') is not None:
                    items_text += f"    ├── {item['name']} — {float(item['quantity']):.0f} {item['unit']} × {float(item['price']):.2f} = {float(item['total']):.2f} руб\n"
                else:
                    items_text += f"{idx}. {item['name']} — {float(item['quantity']):.0f} {item['unit']} × {float(item['price']):.2f} = {float(item['total']):.2f} руб\n"

            if not items_text:
                items_text = "Нет позиций"

            date_str = estimate['date']
            if hasattr(date_str, 'strftime'):
                date_str = date_str.strftime('%d.%m.%Y')

            QMessageBox.information(
                self,
                f"Смета {estimate['number']}",
                f"Номер: {estimate['number']}\n"
                f"Дата: {date_str}\n"
                f"Клиент: {estimate.get('client_name', 'Не указан')}\n"
                f"Адрес: {estimate.get('client_address', 'Не указан')}\n"
                f"Сумма: {float(estimate['total_amount']):.2f} руб\n"
                f"Кол-во позиций: {len(estimate.get('items', []))}\n\n"
                f"--- Позиции ---\n{items_text}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось показать смету:\n{e}")

    def delete_estimate(self):
        ids = self.get_selected_ids()
        if not ids:
            QMessageBox.warning(self, "Ошибка", "Выберите сметы для удаления!")
            return

        if len(ids) == 1:
            msg = "Удалить выбранную смету?"
        else:
            msg = f"Удалить {len(ids)} выбранных смет?"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            for estimate_id in ids:
                try:
                    if db.delete_estimate(estimate_id):
                        deleted += 1
                except Exception as e:
                    print(f"Ошибка при удалении сметы {estimate_id}: {e}")

            self.load_data()
            QMessageBox.information(self, "Готово", f"Удалено смет: {deleted} из {len(ids)}")