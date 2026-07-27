from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import db


class MaterialTreeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Номенклатура (каталог)")
        self.setMinimumSize(950, 600)

        layout = QVBoxLayout(self)

        hint = QLabel(
            "📁 Жёлтые папки — категории\n"
            "📄 Белые — обычные материалы\n"
            "📦 Зелёные — комплекты\n\n"
            "💡 Кликните на треугольник слева от папки, чтобы раскрыть её"
        )
        hint.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Наименование", "Ед. изм.", "Цена розн.", "Вес"])
        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 80)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        layout.addWidget(self.tree)

        btn_layout = QHBoxLayout()

        self.add_category_btn = QPushButton("📁 Добавить категорию")
        self.add_category_btn.clicked.connect(self.add_category)
        btn_layout.addWidget(self.add_category_btn)

        self.add_material_btn = QPushButton("➕ Добавить материал")
        self.add_material_btn.clicked.connect(self.add_material)
        btn_layout.addWidget(self.add_material_btn)

        self.add_kit_btn = QPushButton("📦 Добавить комплект")
        self.add_kit_btn.clicked.connect(self.add_kit)
        btn_layout.addWidget(self.add_kit_btn)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_item)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_item)
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

    def _get_icon_for_type(self, item_type, is_kit=False):
        """Создаёт иконку для элемента"""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if item_type == 'category':
            # Жёлтая папка
            painter.setBrush(QBrush(QColor(255, 193, 7)))
            painter.setPen(QPen(QColor(255, 160, 0), 1))
            painter.drawRect(2, 5, 16, 12)
            painter.drawLine(2, 5, 6, 2)
            painter.drawLine(6, 2, 18, 2)
        elif is_kit:
            # Зелёный ящик для комплекта
            painter.setBrush(QBrush(QColor(76, 175, 80)))
            painter.setPen(QPen(QColor(46, 125, 50), 1))
            painter.drawRect(3, 4, 14, 12)
            painter.drawLine(3, 8, 17, 8)
            painter.drawArc(7, 2, 6, 4, 0, 180 * 16)
        else:
            # Белый лист для материала
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawRect(3, 3, 14, 14)
            painter.drawLine(5, 8, 15, 8)
            painter.drawLine(5, 12, 13, 12)

        painter.end()
        return QIcon(pixmap)

    def load_data(self):
        """Загружает все материалы, категории и комплекты в дерево"""
        self.tree.clear()

        # Получаем все материалы и категории
        materials = db.get_materials_hierarchy()

        # Получаем все комплекты
        kits = db.get_all_kits()

        # Находим категорию "Комплекты"
        kit_category_id = None
        for mat in materials:
            if mat['name'] == 'Комплекты' and mat.get('is_category', False):
                kit_category_id = mat['id']
                break

        # Разделяем материалы на категории и обычные материалы
        categories = [m for m in materials if m.get('is_category', False)]
        regular_materials = [m for m in materials if not m.get('is_category', False)]

        # Сортируем категории по имени
        categories.sort(key=lambda x: x['name'])
        # Сортируем материалы по имени
        regular_materials.sort(key=lambda x: x['name'])

        # Словарь для хранения элементов
        items_dict = {}

        # Создаём элементы для категорий
        for cat in categories:
            item = QTreeWidgetItem()
            item.setText(0, cat['name'])
            item.setText(1, 'категория')
            item.setText(2, '')
            item.setText(3, '')

            item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'category',
                'id': cat['id']
            })
            item.setIcon(0, self._get_icon_for_type('category'))

            # Проверка на дубликаты
            if cat['id'] not in items_dict:
                items_dict[cat['id']] = item

        # Создаём элементы для материалов
        for mat in regular_materials:
            item = QTreeWidgetItem()
            item.setText(0, mat['name'])
            item.setText(1, mat.get('unit', ''))
            item.setText(2, f"{float(mat.get('retail_price', 0)):.2f}")
            item.setText(3, f"{float(mat.get('weight_per_unit', 0)):.3f}")

            item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'material',
                'id': mat['id']
            })
            item.setIcon(0, self._get_icon_for_type('material'))

            # Проверка на дубликаты
            if mat['id'] not in items_dict:
                items_dict[mat['id']] = item

        # Создаём элементы для комплектов
        kit_items = {}
        for kit in kits:
            kit_item = QTreeWidgetItem()
            kit_item.setText(0, f"📦 {kit['name']}")
            kit_item.setText(1, 'комплект')
            kit_item.setText(2, f"{float(kit.get('retail_price', 0)):.2f}")
            kit_item.setText(3, '')

            kit_item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'kit',
                'id': kit['id']
            })
            kit_item.setIcon(0, self._get_icon_for_type('kit', is_kit=True))

            kit_items[kit['id']] = kit_item

        # --- Прикрепляем элементы к родителям ---

        # 1. Сначала добавляем корневые категории
        for cat in categories:
            if cat['parent_id'] is None:
                if cat['id'] in items_dict:
                    self.tree.addTopLevelItem(items_dict[cat['id']])
            else:
                parent_item = items_dict.get(cat['parent_id'])
                if parent_item and cat['id'] in items_dict:
                    parent_item.addChild(items_dict[cat['id']])

        # 2. Добавляем комплекты в категорию "Комплекты" или в корень
        if kit_category_id and kit_category_id in items_dict:
            parent_item = items_dict[kit_category_id]
            for kit_id, kit_item in kit_items.items():
                parent_item.addChild(kit_item)
        else:
            for kit_id, kit_item in kit_items.items():
                self.tree.addTopLevelItem(kit_item)

        # 3. Добавляем материалы в их категории или в корень
        for mat in regular_materials:
            if mat['parent_id'] is None:
                if mat['id'] in items_dict:
                    self.tree.addTopLevelItem(items_dict[mat['id']])
            else:
                parent_item = items_dict.get(mat['parent_id'])
                if parent_item and mat['id'] in items_dict:
                    parent_item.addChild(items_dict[mat['id']])

        self.tree.expandAll()
        self.tree.resizeColumnToContents(0)

    def get_selected_item(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0]

    def get_selected_id(self):
        item = self.get_selected_item()
        if not item:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return None
        return data.get('id')

    def get_selected_type(self):
        item = self.get_selected_item()
        if not item:
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return None
        return data.get('type')

    def add_category(self):
        parent_item = self.get_selected_item()
        parent_id = None
        parent_name = "корневую"

        if parent_item:
            data = parent_item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('type') in ['category', 'kit']:
                parent_id = data.get('id')
                parent_name = f"категорию '{parent_item.text(0)}'"

        name, ok = QInputDialog.getText(
            self,
            "Новая категория",
            f"Введите название категории (в {parent_name}):"
        )
        if ok and name.strip():
            if db.add_category(name.strip(), parent_id):
                self.load_data()
                QMessageBox.information(self, "Готово", f"Категория '{name.strip()}' создана!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать категорию!")

    def add_material(self):
        from material_dialog import MaterialEditDialog

        parent_id = None
        selected_type = self.get_selected_type()
        if selected_type == 'category':
            parent_id = self.get_selected_id()

        dialog = MaterialEditDialog(self, parent_id=parent_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def add_kit(self):
        name, ok = QInputDialog.getText(self, "Новый комплект", "Введите название комплекта:")
        if not ok or not name.strip():
            return

        kit_id = db.add_kit(name.strip())
        if not kit_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать комплект!")
            return

        self._edit_kit_items(kit_id, name.strip())
        self.load_data()

    def _edit_kit_items(self, kit_id, kit_name):
        dialog = KitItemsDialog(kit_id, kit_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            items = db.get_kit_items(kit_id)
            total_price = sum(item['quantity'] * item['material_price'] for item in items)
            db.update_kit(kit_id, kit_name, '', total_price)

    def edit_item(self):
        item = self.get_selected_item()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите элемент!")
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type = data.get('type')
        item_id = data.get('id')

        if item_type == 'category':
            old_name = item.text(0)
            new_name, ok = QInputDialog.getText(
                self,
                "Переименовать категорию",
                "Введите новое название:",
                text=old_name
            )
            if ok and new_name.strip():
                if db.update_category(item_id, new_name.strip()):
                    self.load_data()
                    QMessageBox.information(self, "Готово", "Категория переименована!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось переименовать категорию!")

        elif item_type == 'material':
            from material_dialog import MaterialEditDialog
            dialog = MaterialEditDialog(self, item_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

        elif item_type == 'kit':
            # Редактируем комплект — сначала переименовываем
            kit = db.get_kit_by_id(item_id)
            if not kit:
                QMessageBox.warning(self, "Ошибка", "Комплект не найден!")
                return

            # Предлагаем переименовать
            new_name, ok = QInputDialog.getText(
                self,
                "Переименовать комплект",
                "Введите новое название:",
                text=kit['name']
            )
            if ok and new_name.strip():
                # Обновляем название
                db.update_kit(item_id, new_name.strip(), kit['description'], kit['retail_price'])
                # Открываем диалог редактирования позиций
                self._edit_kit_items(item_id, new_name.strip())
                self.load_data()

    def delete_item(self):
        item = self.get_selected_item()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите элемент!")
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type = data.get('type')
        item_id = data.get('id')
        item_name = item.text(0)

        if item_type == 'category':
            materials = db.get_materials_by_category(item_id)
            if materials:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    f"В категории '{item_name}' есть {len(materials)} материалов.\n"
                    "Удалить категорию и все материалы в ней?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    f"Удалить категорию '{item_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            if db.delete_category(item_id):
                self.load_data()
                QMessageBox.information(self, "Готово", "Категория удалена!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить категорию!")

        elif item_type == 'material':
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить материал '{item_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if db.delete_material(item_id):
                    self.load_data()
                    QMessageBox.information(self, "Готово", "Материал удалён!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить материал!")

        elif item_type == 'kit':
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить комплект '{item_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if db.delete_kit(item_id):
                    self.load_data()
                    QMessageBox.information(self, "Готово", "Комплект удалён!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить комплект!")


class KitItemsDialog(QDialog):
    """Диалог редактирования позиций комплекта"""

    def __init__(self, kit_id, kit_name, parent=None):
        super().__init__(parent)
        self.kit_id = kit_id
        self.kit_name = kit_name
        self.setWindowTitle(f"Редактирование комплекта: {kit_name}")
        self.setMinimumSize(700, 450)

        layout = QVBoxLayout(self)

        self.info_label = QLabel(f"<b>Комплект:</b> {kit_name}\n<b>Всего позиций:</b> 0")
        self.info_label.setStyleSheet("background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)  # Увеличили количество колонок
        self.table.setHorizontalHeaderLabels(
            ["ID", "Материал", "Кол-во", "Ед.", "Расход", "Тип расчёта", "Сумма"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 50)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 120)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Добавить материал")
        self.add_btn.clicked.connect(self.add_item)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("🗑️ Удалить")
        self.remove_btn.clicked.connect(self.remove_item)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.load_data()

    def load_data(self):
        items = db.get_kit_items_full(self.kit_id)  # Используем новую функцию
        self.table.setRowCount(len(items))

        total_price = 0
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['material_name']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(item['unit'] or item['material_unit']))

            # Показываем расход
            consumption_text = f"{item['consumption_per_unit']:.4f}" if item['consumption_per_unit'] > 0 else "—"
            self.table.setItem(row, 4, QTableWidgetItem(consumption_text))

            # Показываем тип расчета
            calc_types = {
                'fixed': 'Фиксированное',
                'per_m2': 'Расход на м²',
                'per_m': 'Расход на м',
                'area': 'По площади',
                'length': 'По длине'
            }
            self.table.setItem(row, 5, QTableWidgetItem(calc_types.get(item['calculation_type'], 'fixed')))

            subtotal = item['quantity'] * item['material_price']
            self.table.setItem(row, 6, QTableWidgetItem(f"{subtotal:.2f}"))
            total_price += subtotal

        self.table.resizeColumnsToContents()

        self.info_label.setText(
            f"<b>Комплект:</b> {self.kit_name}\n"
            f"<b>Всего позиций:</b> {len(items)}\n"
            f"<b>Общая стоимость:</b> {total_price:.2f} руб"
        )

    def add_item(self):
        dialog = SelectMaterialSimpleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            material = dialog.get_selected_material()
            if not material:
                return

            # Выбираем тип расчета
            calc_types = {
                'fixed': 'Фиксированное количество',
                'per_m2': 'Расход на м² (покраска)',
                'per_m': 'Расход на метр погонный',
                'area': 'Зависит от площади (например, работа)',
                'length': 'Зависит от длины'
            }

            calc_type, ok = QInputDialog.getItem(
                self,
                "Тип расчета",
                "Как будет рассчитываться количество?\n\n"
                "Фиксированное - всегда одно и то же количество\n"
                "Расход на м² - умножается на площадь (для покраски)\n"
                "Расход на м - умножается на длину\n"
                "По площади - равно площади (для работ)\n"
                "По длине - равно длине в метрах",
                list(calc_types.values()),
                0, False
            )
            if not ok:
                return

            # Находим ключ типа расчета
            calc_type_key = {v: k for k, v in calc_types.items()}[calc_type]

            # Запрашиваем дополнительные параметры
            consumption = 0
            quantity = 1

            if calc_type_key == 'fixed':
                quantity, ok = QInputDialog.getDouble(
                    self,
                    "Количество",
                    "Введите фиксированное количество:",
                    1, 0.01, 10000, 2
                )
                if not ok:
                    return

            elif calc_type_key in ['per_m2', 'per_m']:
                consumption, ok = QInputDialog.getDouble(
                    self,
                    "Норма расхода",
                    f"Введите расход на 1 {'м²' if calc_type_key == 'per_m2' else 'метр'}:",
                    0.1, 0.001, 100, 3
                )
                if not ok:
                    return

                # Если это расходный материал, обновляем consumption_per_m2 у материала
                if calc_type_key == 'per_m2' and consumption > 0:
                    db.update_material(
                        material['id'],
                        material['name'],
                        material['unit'],
                        material['weight_per_unit'] or 0,
                        material['purchase_price'] or 0,
                        material['retail_price'] or 0,
                        material.get('sku'),
                        material.get('description', ''),
                        material.get('parent_id'),
                        consumption  # обновляем расход
                    )

            elif calc_type_key in ['area', 'length']:
                # Для этих типов количество будет рассчитываться автоматически
                quantity = 1

            # Сохраняем в комплект с новыми полями
            success = db.add_kit_item_full(
                kit_id=self.kit_id,
                material_id=material['id'],
                quantity=quantity,
                unit=material['unit'],
                consumption_per_unit=consumption,
                calculation_type=calc_type_key
            )

            if success:
                self.load_data()
                QMessageBox.information(self, "Готово", "Материал добавлен в комплект!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить материал!")

    def remove_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите позицию для удаления!")
            return

        item_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить '{name}' из комплекта?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if db.remove_kit_item(item_id):
                self.load_data()
                QMessageBox.information(self, "Готово", "Позиция удалена!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить позицию!")


class SelectMaterialSimpleDialog(QDialog):
    """Простой диалог выбора материала (только материалы, не категории)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор материала")
        self.setMinimumSize(500, 400)
        self.selected_material = None

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название...")
        self.search_input.textChanged.connect(self.filter_materials)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование", "Ед. изм."])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 300)
        self.table.doubleClicked.connect(self.select_material)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("✅ Выбрать")
        self.select_btn.clicked.connect(self.select_material)
        btn_layout.addWidget(self.select_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.all_materials = []
        self.load_materials()

    def load_materials(self):
        self.all_materials = db.get_materials()
        self.filter_materials()

    def filter_materials(self):
        query = self.search_input.text().strip().lower()
        filtered = self.all_materials
        if query:
            filtered = [m for m in self.all_materials if query in m['name'].lower()]

        self.table.setRowCount(len(filtered))
        for row, mat in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(str(mat['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(mat['name']))
            self.table.setItem(row, 2, QTableWidgetItem(mat['unit']))
        self.table.resizeColumnsToContents()

    def select_material(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите материал!")
            return

        mat_id = int(self.table.item(row, 0).text())
        for mat in self.all_materials:
            if mat['id'] == mat_id:
                self.selected_material = mat
                break

        if self.selected_material:
            self.accept()

    def get_selected_material(self):
        return self.selected_material