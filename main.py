import sys
import math
import json
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from collections import defaultdict
from material_dialog import MaterialDialog
from material_tree_dialog import MaterialTreeDialog
from unit_dialog import UnitDialog
from client_dialog import ClientDialog
from client_selector import ClientSelector
import config
import db


class GateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(900, 300)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #aaa;")
        self.width_opening = 4000
        self.height_total = 2000
        self.beam_type = "SG01"
        self.sections = 4
        self.diagonals_enabled = False
        self.custom_counterweight = False
        self.custom_counterweight_length = 2000
        self.beam_height = {"SG01": 60, "SG02": 85}
        self.beam_width = {"SG01": 40, "SG02": 60}
        self.client_name = "Не выбран"
        self.client_address = "Не указан"

    def fit_text(self, painter, text, max_width):
        if painter.fontMetrics().horizontalAdvance(text) <= max_width:
            return text
        words = text.split()
        result = ""
        for word in words:
            test = result + word + " "
            if painter.fontMetrics().horizontalAdvance(test + "...") > max_width:
                break
            result = test
        return result.strip() + "..."

    def setParameters(self, width, height, beam_type, sections, diagonals_enabled, custom_cw, custom_cw_length):
        self.width_opening = width
        self.height_total = height
        self.beam_type = beam_type
        self.sections = sections
        self.diagonals_enabled = diagonals_enabled
        self.custom_counterweight = custom_cw
        self.custom_counterweight_length = custom_cw_length
        self.update()

    def setClientInfo(self, name, address):
        self.client_name = name
        self.client_address = address
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin_left = 100
        margin_right = 60
        margin_top = 30
        margin_bottom = 60
        available_width = self.width() - margin_left - margin_right
        available_height = self.height() - margin_top - margin_bottom
        H_beam_mm = self.beam_height[self.beam_type]
        H_frame_mm = self.height_total - H_beam_mm
        outer_width_mm = self.width_opening + 2 * self.beam_width[self.beam_type]
        if self.custom_counterweight:
            counterweight_length_mm = self.custom_counterweight_length
        else:
            counterweight_length_mm = self.width_opening / 2
        total_length_mm = outer_width_mm + counterweight_length_mm
        scale_x = available_width / total_length_mm
        scale_y = available_height / self.height_total
        scale = min(scale_x, scale_y)
        outer_w_px = outer_width_mm * scale
        frame_w_px = self.width_opening * scale
        counterweight_w_px = counterweight_length_mm * scale
        total_width_px = outer_w_px + counterweight_w_px
        frame_h_px = H_frame_mm * scale
        beam_h_px = max(5, H_beam_mm * scale)
        total_drawing_height = frame_h_px + beam_h_px
        base_x = margin_left
        base_y = margin_top + (available_height - total_drawing_height) / 2
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        outer_left_offset = (outer_w_px - frame_w_px) / 2
        outer_x = base_x + outer_left_offset
        painter.drawRect(int(outer_x), int(base_y), int(outer_w_px), int(frame_h_px))
        counterweight_x = outer_x + outer_w_px
        painter.drawRect(int(counterweight_x), int(base_y), int(counterweight_w_px), int(frame_h_px))
        beam_y = base_y + frame_h_px
        beam_start_x = outer_x
        beam_width_px = outer_w_px + counterweight_w_px
        painter.fillRect(int(beam_start_x), int(beam_y), int(beam_width_px), int(beam_h_px), QColor(70, 100, 200))
        painter.setPen(QPen(QColor(50, 70, 150), 1))
        painter.drawRect(int(beam_start_x), int(beam_y), int(beam_width_px), int(beam_h_px))
        if self.diagonals_enabled:
            painter.setPen(QPen(Qt.GlobalColor.black, 3))
            painter.drawLine(int(counterweight_x), int(base_y), int(counterweight_x + counterweight_w_px),
                             int(base_y + frame_h_px))
        painter.setPen(QPen(QColor(200, 0, 0), 2))
        inner_w_px = frame_w_px
        inner_h_mm = H_frame_mm - 2 * self.beam_width[self.beam_type]
        inner_h_px = inner_h_mm * scale
        inner_x = outer_x + (outer_w_px - inner_w_px) / 2
        inner_y_offset = self.beam_width[self.beam_type] * scale
        inner_y = base_y + inner_y_offset
        painter.drawRect(int(inner_x), int(inner_y), int(inner_w_px), int(inner_h_px))
        if self.sections > 0:
            step = inner_w_px / self.sections
            for i in range(self.sections + 1):
                x = inner_x + i * step
                painter.drawLine(int(x), int(inner_y), int(x), int(inner_y + inner_h_px))
        center_y = inner_y + inner_h_px / 2
        painter.drawLine(int(inner_x), int(center_y), int(inner_x + inner_w_px), int(center_y))
        if self.diagonals_enabled and self.sections > 0:
            bottom_y = inner_y + inner_h_px
            for i in range(self.sections):
                x1 = inner_x + i * step
                x2 = inner_x + (i + 1) * step
                if i % 2 == 0:
                    painter.drawLine(int(x1), int(bottom_y), int(x2), int(center_y))
                else:
                    painter.drawLine(int(x1), int(center_y), int(x2), int(bottom_y))
        if self.diagonals_enabled:
            cw_x = counterweight_x
            cw_w_px = counterweight_w_px
            cw_h_px = frame_h_px
            cw_center_y = base_y + cw_h_px / 2
            intersection_x = cw_x + cw_w_px / 2
            painter.drawLine(int(cw_x), int(cw_center_y), int(intersection_x), int(cw_center_y))
            painter.drawLine(int(intersection_x), int(cw_center_y), int(intersection_x), int(base_y + cw_h_px))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.save()
        painter.translate(margin_left - 25, base_y + frame_h_px / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, f"Общая: {self.height_total} мм")
        painter.restore()
        painter.save()
        painter.translate(margin_left - 25 + 16, base_y + frame_h_px / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, f"Рама: {H_frame_mm} мм")
        painter.restore()
        painter.save()
        painter.translate(margin_left - 25, beam_y + beam_h_px / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, f"Балка: {H_beam_mm} мм")
        painter.restore()
        painter.drawText(int(inner_x + inner_w_px / 2 - 30), int(beam_y + beam_h_px + 18),
                         f"Проём: {self.width_opening} мм")
        cw_text = f"Противовес: {counterweight_length_mm:.0f} мм"
        if self.custom_counterweight:
            cw_text += " (вручную)"
        painter.drawText(int(counterweight_x + counterweight_w_px / 2 - 35), int(beam_y + beam_h_px + 18), cw_text)
        total_beam_length = self.width_opening + counterweight_length_mm
        painter.drawText(int(base_x + total_width_px / 2 - 45), int(beam_y + beam_h_px + 35),
                         f"Общая длина балки: {total_beam_length:.0f} мм")
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        font_info = QFont("Arial", 9)
        font_info.setBold(True)
        painter.setFont(font_info)
        x_offset = 15
        y_offset = 20
        client_text = f"👤 Клиент: {self.client_name}"
        client_text = self.fit_text(painter, client_text, 400)
        painter.drawText(x_offset, y_offset, client_text)
        painter.setFont(QFont("Arial", 8))
        address_text = f"📍 Адрес: {self.client_address}"
        address_text = self.fit_text(painter, address_text, 400)
        painter.drawText(x_offset, y_offset + 20, address_text)
        painter.end()

    def sizeHint(self):
        return QSize(950, 350)


class CuttingWindow(QDialog):
    def __init__(self, cutting_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Раскрой по хлыстам 6 метров")
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text_edit)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.display_cutting(cutting_data)

    def display_cutting(self, cutting_data):
        text = ""
        total_sticks_all = 0
        total_cuts_all = 0
        total_splices_all = 0
        total_beams = 0
        profile_sticks = {}
        beam_sticks = {}
        for profile, data in cutting_data.items():
            if profile.startswith("Балка"):
                total_beams += data['total_sticks']
                beam_sticks[profile] = data['total_sticks']
            else:
                total_sticks_all += data['total_sticks']
                total_cuts_all += data['total_cuts']
                total_splices_all += data['total_splices']
                profile_sticks[profile] = data['total_sticks']
            text += f"\n{'=' * 60}\n"
            text += f"ПРОФИЛЬ: {profile}\n"
            text += f"{'=' * 60}\n"
            text += f"Всего деталей: {data['total_parts']}\n"
            text += f"Всего резов: {data['total_cuts']}\n"
            text += f"Всего хлыстов (6000 мм): {data['total_sticks']} шт\n"
            if data['total_splices'] > 0:
                text += f"⚠️ Стыков: {data['total_splices']}\n"
            text += f"\nСписок хлыстов:\n"
            text += f"{'-' * 40}\n"
            for i, stick in enumerate(data['sticks'], 1):
                used = 6000 - stick['remainder']
                text += f"  Хлыст №{i}: использовано {used:.0f} мм, остаток {stick['remainder']:.0f} мм\n"
            text += f"\nРаспил:\n"
            text += f"{'-' * 40}\n"
            for i, stick in enumerate(data['sticks'], 1):
                text += f"\nХлыст №{i} (6000 мм):\n"
                for part in stick['parts']:
                    text += f"  └─ {part['name']}: {part['length']:.0f} мм\n"
                text += f"  Остаток: {stick['remainder']:.0f} мм\n"
            text += f"\n"
        text += f"\n{'=' * 60}\n"
        text += f"ОБЩИЙ ИТОГ:\n"
        text += f"{'=' * 60}\n"
        for profile, sticks_count in beam_sticks.items():
            text += f"  {profile}: {sticks_count} шт\n"
        for profile, sticks_count in profile_sticks.items():
            text += f"  {profile}: {sticks_count} шт\n"
        text += f"{'-' * 60}\n"
        text += f"Всего балок: {total_beams} шт\n"
        text += f"Всего хлыстов 6000 мм (трубы): {total_sticks_all} шт\n"
        text += f"Всего резов: {total_cuts_all}\n"
        if total_splices_all > 0:
            text += f"Всего стыков: {total_splices_all}\n"
        self.text_edit.setText(text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конструктор откатных ворот")
        self.setMinimumSize(1200, 800)
        db.init_db()
        self.current_project_file = None
        self.current_client_id = None
        self.current_client_name = "Не выбран"
        self.current_client_address = "Не указан"
        self.current_user = None
        self.current_paint_enabled = False
        self.current_estimate_dialog = None
        self.estimate_buffer = None
        self.create_menu()
        self.init_ui()
        self.update_all()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        left_panel = QWidget()
        left_panel.setMaximumWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.setSpacing(12)
        title = QLabel("⚙️ ПАРАМЕТРЫ ВОРОТ")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(title)
        self.select_client_btn = QPushButton("👤 Выбрать клиента")
        self.select_client_btn.clicked.connect(self.select_client)
        left_layout.addWidget(self.select_client_btn)
        self.clear_client_btn = QPushButton("🗑️ Сбросить клиента")
        self.clear_client_btn.clicked.connect(self.clear_client)
        left_layout.addWidget(self.clear_client_btn)
        self.address_combo = QComboBox()
        self.address_combo.setEnabled(False)
        self.address_combo.addItem("Нет адресов")
        self.address_combo.currentIndexChanged.connect(self.on_address_changed)
        left_layout.addWidget(QLabel("Адрес:"))
        left_layout.addWidget(self.address_combo)
        left_layout.addWidget(QLabel("Ширина проёма (мм):"))
        self.width_input = QLineEdit("4000")
        left_layout.addWidget(self.width_input)
        left_layout.addWidget(QLabel("Общая высота ворот (мм):"))
        self.height_input = QLineEdit("2000")
        left_layout.addWidget(self.height_input)
        left_layout.addWidget(QLabel("Тип направляющей балки:"))
        self.beam_combo = QComboBox()
        self.beam_combo.addItems(["SG01", "SG02"])
        left_layout.addWidget(self.beam_combo)
        left_layout.addWidget(QLabel("Количество секций:"))
        self.sections_spin = QSpinBox()
        self.sections_spin.setRange(1, 10)
        self.sections_spin.setValue(4)
        left_layout.addWidget(self.sections_spin)
        self.custom_cw_check = QCheckBox("Своя длина противовеса")
        self.custom_cw_check.toggled.connect(self.on_custom_cw_toggled)
        left_layout.addWidget(self.custom_cw_check)
        self.custom_cw_input = QLineEdit("2000")
        self.custom_cw_input.setEnabled(False)
        self.custom_cw_input.setPlaceholderText("Длина противовеса (мм)")
        left_layout.addWidget(self.custom_cw_input)
        self.diagonals_check = QCheckBox("Диагонали (ферма)")
        left_layout.addWidget(self.diagonals_check)
        self.paint_check = QCheckBox("🎨 Покраска")
        left_layout.addWidget(self.paint_check)
        self.update_btn = QPushButton("🔄 РАССЧИТАТЬ")
        self.update_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.update_btn.clicked.connect(self.update_all)
        left_layout.addWidget(self.update_btn)
        self.cutting_btn = QPushButton("📊 ПОКАЗАТЬ РАСКРОЙ")
        self.cutting_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        self.cutting_btn.clicked.connect(self.show_cutting)
        left_layout.addWidget(self.cutting_btn)
        left_layout.addStretch()
        self.gate_widget = GateWidget()
        top_layout.addWidget(left_panel)
        top_layout.addWidget(self.gate_widget, 1)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(
            ["Деталь", "Профиль", "Длина (мм)", "Кол-во", "Вес (кг)", "Площадь (м²)", "Примечание"])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(top_widget, 2)
        main_layout.addWidget(self.table_widget, 2)
        self.current_materials = []

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        new_action = QAction("Новый проект", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        open_action = QAction("Открыть проект...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        save_action = QAction("Сохранить проект", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        export_excel_action = QAction("Экспорт сметы в Excel", self)
        export_excel_action.triggered.connect(self.export_excel)
        file_menu.addAction(export_excel_action)
        export_pdf_action = QAction("Экспорт чертежа в PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_action)
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        user_menu = menubar.addMenu("Пользователь")
        user_info_action = QAction("👤 Информация о пользователе", self)
        user_info_action.triggered.connect(self.show_user_info)
        user_menu.addAction(user_info_action)
        change_user_action = QAction("🔄 Сменить пользователя", self)
        change_user_action.triggered.connect(self.change_user)
        user_menu.addAction(change_user_action)
        user_menu.addSeparator()
        user_manager_action = QAction("👥 Управление пользователями", self)
        user_manager_action.triggered.connect(self.open_user_manager)
        user_menu.addAction(user_manager_action)

        db_menu = menubar.addMenu("База данных")
        connect_action = QAction("Подключиться к БД...", self)
        connect_action.triggered.connect(self.connect_db)
        db_menu.addAction(connect_action)
        disconnect_action = QAction("Отключиться от БД", self)
        disconnect_action.triggered.connect(self.disconnect_db)
        db_menu.addAction(disconnect_action)
        db_menu.addSeparator()
        backup_action = QAction("Резервная копия БД", self)
        backup_action.triggered.connect(self.backup_db)
        db_menu.addAction(backup_action)
        restore_action = QAction("Восстановить из резервной копии", self)
        restore_action.triggered.connect(self.restore_db)
        db_menu.addAction(restore_action)

        ref_menu = menubar.addMenu("Справочники")
        clients_action = QAction("Клиенты", self)
        clients_action.triggered.connect(self.open_clients)
        ref_menu.addAction(clients_action)
        addresses_action = QAction("Адреса", self)
        addresses_action.triggered.connect(self.open_addresses)
        ref_menu.addAction(addresses_action)
        materials_action = QAction("Номенклатура", self)
        materials_action.triggered.connect(self.open_materials)
        ref_menu.addAction(materials_action)
        units_action = QAction("Единицы измерения", self)
        units_action.triggered.connect(self.open_units)
        ref_menu.addAction(units_action)
        beam_types_action = QAction("Типы балок", self)
        beam_types_action.triggered.connect(self.open_beam_types)
        ref_menu.addAction(beam_types_action)

        doc_menu = menubar.addMenu("Документы")
        estimate_action = QAction("Смета", self)
        estimate_action.triggered.connect(self.open_estimate)
        doc_menu.addAction(estimate_action)
        estimate_list_action = QAction("Список смет", self)
        estimate_list_action.triggered.connect(self.open_estimate_list)
        doc_menu.addAction(estimate_list_action)
        invoice_action = QAction("Счёт", self)
        invoice_action.triggered.connect(self.open_invoice)
        doc_menu.addAction(invoice_action)
        waybill_action = QAction("Товарная накладная", self)
        waybill_action.triggered.connect(self.open_waybill)
        doc_menu.addAction(waybill_action)
        act_action = QAction("Акт выполненных работ", self)
        act_action.triggered.connect(self.open_act)
        doc_menu.addAction(act_action)

        report_menu = menubar.addMenu("Отчёты")
        report_clients_action = QAction("По клиентам", self)
        report_clients_action.triggered.connect(self.report_clients)
        report_menu.addAction(report_clients_action)
        report_materials_action = QAction("По материалам", self)
        report_materials_action.triggered.connect(self.report_materials)
        report_menu.addAction(report_materials_action)
        report_orders_action = QAction("По заказам", self)
        report_orders_action.triggered.connect(self.report_orders)
        report_menu.addAction(report_orders_action)

        help_menu = menubar.addMenu("Справка")
        help_action = QAction("Руководство пользователя", self)
        help_action.triggered.connect(self.open_help)
        help_menu.addAction(help_action)
        help_menu.addSeparator()
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_user_info(self):
        if self.current_user:
            QMessageBox.information(
                self, "Текущий пользователь",
                f"Логин: {self.current_user['login']}\n"
                f"ФИО: {self.current_user['full_name']}\n"
                f"Должность: {self.current_user['position'] or '—'}\n"
                f"Роль: {self.current_user['role']}"
            )
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не определён!")

    def change_user(self):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Закрыть программу для смены пользователя?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()

    def open_user_manager(self):
        from user_dialog import UserDialog
        if self.current_user and self.current_user.get('role') == 'admin':
            dialog = UserDialog(self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Доступ ограничен", "Управление пользователями доступно только администратору.")

    def new_project(self):
        if self.current_materials and not self.confirm_discard():
            return
        self.clear_all()
        self.current_project_file = None
        QMessageBox.information(self, "Новый проект", "Создан новый проект")

    def open_project(self):
        if self.current_materials and not self.confirm_discard():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", "", "JSON files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            project = data["project"]
            self.width_input.setText(str(project["width_opening"]))
            self.height_input.setText(str(project["height_total"]))
            self.beam_combo.setCurrentText(project["beam_type"])
            self.sections_spin.setValue(project["sections"])
            self.diagonals_check.setChecked(project["diagonals_enabled"])
            self.custom_cw_check.setChecked(project["custom_counterweight"])
            if project["custom_counterweight"]:
                self.custom_cw_input.setText(str(project["custom_counterweight_length"]))
            self.current_client_id = project.get("client_id")
            self.current_client_name = project.get("client_name", "Не выбран")
            self.current_client_address = project.get("client_address", "Не указан")
            self.gate_widget.setClientInfo(self.current_client_name, self.current_client_address)
            if self.current_client_id:
                self.load_client_addresses(self.current_client_id)
            self.update_all()
            self.current_project_file = file_path
            QMessageBox.information(self, "Готово", f"Проект загружен:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть проект:\n{e}")

    def save_project(self):
        if self.current_project_file:
            self.save_project_to_file(self.current_project_file)
        else:
            self.save_project_as()

    def save_project_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект", "project.json", "JSON files (*.json)")
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            self.save_project_to_file(file_path)

    def save_project_to_file(self, file_path):
        try:
            data = {
                "project": {
                    "client_id": self.current_client_id,
                    "client_name": self.current_client_name,
                    "client_address": self.current_client_address,
                    "width_opening": int(self.width_input.text()),
                    "height_total": int(self.height_input.text()),
                    "beam_type": self.beam_combo.currentText(),
                    "sections": self.sections_spin.value(),
                    "diagonals_enabled": self.diagonals_check.isChecked(),
                    "custom_counterweight": self.custom_cw_check.isChecked(),
                    "custom_counterweight_length": int(
                        self.custom_cw_input.text()) if self.custom_cw_check.isChecked() else None,
                    "created_at": datetime.now().isoformat()
                },
                "materials": self.current_materials,
                "cutting": self.calculate_cutting(self.current_materials) if self.current_materials else {}
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.current_project_file = file_path
            QMessageBox.information(self, "Готово", f"Проект сохранён:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить проект:\n{e}")

    def confirm_discard(self):
        reply = QMessageBox.question(self, "Подтверждение", "Текущие изменения будут потеряны. Продолжить?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def clear_all(self):
        self.width_input.setText("4000")
        self.height_input.setText("2000")
        self.beam_combo.setCurrentIndex(0)
        self.sections_spin.setValue(4)
        self.diagonals_check.setChecked(False)
        self.custom_cw_check.setChecked(False)
        self.custom_cw_input.setEnabled(False)
        self.custom_cw_input.setText("2000")
        self.paint_check.setChecked(False)
        self.clear_client()
        self.current_materials = []
        self.table_widget.setRowCount(0)
        self.gate_widget.setParameters(4000, 2000, "SG01", 4, False, False, 2000)

    def on_custom_cw_toggled(self, checked):
        self.custom_cw_input.setEnabled(checked)

    def select_client(self):
        dialog = ClientSelector(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client_id = dialog.selected_client_id
            client_name = dialog.selected_client_name
            self.current_client_id = client_id
            self.current_client_name = client_name
            self.load_client_addresses(client_id)
            self.update_client_info()

    def clear_client(self):
        self.current_client_id = None
        self.current_client_name = "Не выбран"
        self.current_client_address = "Не указан"
        self.address_combo.clear()
        self.address_combo.addItem("Нет адресов")
        self.address_combo.setEnabled(False)
        self.update_client_info()

    def load_client_addresses(self, client_id):
        addresses = db.get_client_addresses(client_id)
        self.address_combo.clear()
        if addresses:
            self.address_combo.setEnabled(True)
            for addr in addresses:
                text = f"{addr['city']}, {addr['street']}, {addr['house']}"
                if addr['apartment']:
                    text += f", кв.{addr['apartment']}"
                self.address_combo.addItem(text, addr['id'])
            self.address_combo.setCurrentIndex(0)
            first_addr = addresses[0]
            self.current_client_address = f"{first_addr['city']}, {first_addr['street']}, {first_addr['house']}"
            if first_addr['apartment']:
                self.current_client_address += f", кв.{first_addr['apartment']}"
        else:
            self.address_combo.addItem("Нет адресов")
            self.address_combo.setEnabled(False)
            self.current_client_address = "Не указан"
        self.update_client_info()

    def on_address_changed(self):
        if self.address_combo.isEnabled() and self.address_combo.currentIndex() >= 0:
            current_text = self.address_combo.currentText()
            if current_text and current_text != "Нет адресов":
                self.current_client_address = current_text
            else:
                self.current_client_address = "Не указан"
        else:
            self.current_client_address = "Не указан"
        self.update_client_info()

    def update_client_info(self):
        self.gate_widget.setClientInfo(self.current_client_name, self.current_client_address)

    def calculate_materials(self):
        width = int(self.width_input.text())
        height = int(self.height_input.text())
        beam_type = self.beam_combo.currentText()
        sections = self.sections_spin.value()
        diagonals = self.diagonals_check.isChecked()
        custom_cw = self.custom_cw_check.isChecked()
        if custom_cw:
            try:
                counterweight_length = int(self.custom_cw_input.text())
            except ValueError:
                counterweight_length = width // 2
        else:
            counterweight_length = width // 2
        beam_h = {"SG01": 60, "SG02": 85}[beam_type]
        beam_w = {"SG01": 40, "SG02": 60}[beam_type]
        beam_weight = {"SG01": 5.8, "SG02": 11.2}[beam_type]
        beam_perimeter = {"SG01": 0.26, "SG02": 0.358}
        frame_tube = {"SG01": "60×40×2", "SG02": "80×40×2"}[beam_type]
        frame_weight = {"SG01": 2.96, "SG02": 3.59}[beam_type]
        frame_perimeter = {"SG01": 0.2, "SG02": 0.24}
        inner_perimeter = 0.12
        inner_weight = 1.31
        H_frame = height - beam_h
        H_vert_frame = H_frame - 2 * beam_w
        vertical_height = H_vert_frame - 2 * beam_w
        beam_length = width + counterweight_length
        frame_horiz_length = beam_length
        inner_width = width
        inner_height = H_frame - 2 * beam_w
        horiz_cut_length = (inner_width - (sections + 1) * beam_w) / sections
        step = inner_width / sections
        details = []
        beam_area = beam_length / 1000 * beam_perimeter[beam_type]
        details.append(
            ["Балка", f"Балка SG{beam_type}", f"{beam_length:.0f}", 1, beam_length * beam_weight / 1000, beam_area, ""])
        frame_diag_length = math.sqrt(counterweight_length ** 2 + H_frame ** 2)
        details.append([f"Труба {frame_tube} (верх)", frame_tube, f"{frame_horiz_length:.0f}", 1,
                        frame_horiz_length * frame_weight / 1000,
                        frame_horiz_length / 1000 * frame_perimeter[beam_type], ""])
        details.append([f"Труба {frame_tube} (низ)", frame_tube, f"{frame_horiz_length:.0f}", 1,
                        frame_horiz_length * frame_weight / 1000,
                        frame_horiz_length / 1000 * frame_perimeter[beam_type], ""])
        details.append([f"Труба {frame_tube} (левая стойка)", frame_tube, f"{H_vert_frame:.0f}", 1,
                        H_vert_frame * frame_weight / 1000, H_vert_frame / 1000 * frame_perimeter[beam_type], "рама"])
        details.append([f"Труба {frame_tube} (правая стойка/левая противовеса)", frame_tube, f"{H_vert_frame:.0f}", 1,
                        H_vert_frame * frame_weight / 1000, H_vert_frame / 1000 * frame_perimeter[beam_type],
                        "рама/противовес"])
        details.append([f"Труба {frame_tube} (правая стойка противовеса)", frame_tube, f"{H_vert_frame:.0f}", 1,
                        H_vert_frame * frame_weight / 1000, H_vert_frame / 1000 * frame_perimeter[beam_type], ""])
        if diagonals:
            details.append([f"Труба {frame_tube} (диагональ противовеса)", frame_tube, f"{frame_diag_length:.0f}", 1,
                            frame_diag_length * frame_weight / 1000,
                            frame_diag_length / 1000 * frame_perimeter[beam_type], ""])
        details.append([f"Труба 40×20×1.5 (верх наполнения)", "40×20×1.5", f"{inner_width:.0f}", 1,
                        inner_width * inner_weight / 1000, inner_width / 1000 * inner_perimeter, ""])
        details.append([f"Труба 40×20×1.5 (низ наполнения)", "40×20×1.5", f"{inner_width:.0f}", 1,
                        inner_width * inner_weight / 1000, inner_width / 1000 * inner_perimeter, ""])
        vert_count = sections + 1
        details.append([f"Труба 40×20×1.5 (вертикали)", "40×20×1.5", f"{vertical_height:.0f}", vert_count,
                        vertical_height * inner_weight / 1000 * vert_count,
                        vertical_height / 1000 * inner_perimeter * vert_count, f"{vert_count} шт"])
        details.append([f"Труба 40×20×1.5 (горизонталь по центру)", "40×20×1.5", f"{horiz_cut_length:.0f}", sections,
                        horiz_cut_length * inner_weight / 1000 * sections,
                        horiz_cut_length / 1000 * inner_perimeter * sections, f"{sections} отрезков"])
        if diagonals:
            diagonal_length = math.sqrt(step ** 2 + (H_frame / 2) ** 2)
            details.append([f"Труба 40×20×1.5 (диагонали)", "40×20×1.5", f"{diagonal_length:.0f}", sections,
                            diagonal_length * inner_weight / 1000 * sections,
                            diagonal_length / 1000 * inner_perimeter * sections, f"{sections} шт, внизу"])
            cw_horiz = counterweight_length / 2
            cw_vert = inner_height / 2
            details.append([f"Труба 40×20×1.5 (противовес горизонталь)", "40×20×1.5", f"{cw_horiz:.0f}", 1,
                            cw_horiz * inner_weight / 1000, cw_horiz / 1000 * inner_perimeter, ""])
            details.append([f"Труба 40×20×1.5 (противовес вертикаль)", "40×20×1.5", f"{cw_vert:.0f}", 1,
                            cw_vert * inner_weight / 1000, cw_vert / 1000 * inner_perimeter, ""])
        return details

    def calculate_cutting(self, materials):
        profile_groups = {}
        for mat in materials:
            profile = mat[1]
            length = float(mat[2])
            quantity = int(mat[3])
            name = mat[0]
            if profile not in profile_groups:
                profile_groups[profile] = []
            for _ in range(quantity):
                if length > 6000:
                    remaining = length
                    segment_num = 1
                    total_segments = math.ceil(length / 6000)
                    while remaining > 0:
                        segment_length = min(remaining, 6000)
                        if total_segments == 1:
                            segment_name = name
                        elif segment_num == 1:
                            segment_name = f"{name} (сегмент 1)"
                        else:
                            segment_name = f"{name} (сегмент {segment_num})"
                        needs_cut = (segment_num > 1)
                        profile_groups[profile].append(
                            {'name': segment_name, 'length': segment_length, 'profile': profile, 'needs_cut': needs_cut,
                             'is_splice': segment_num > 1})
                        remaining -= segment_length
                        segment_num += 1
                else:
                    needs_cut = (length < 6000)
                    profile_groups[profile].append(
                        {'name': name, 'length': length, 'profile': profile, 'needs_cut': needs_cut,
                         'is_splice': False})
        cutting_result = {}
        for profile, parts in profile_groups.items():
            parts_sorted = sorted(parts, key=lambda x: x['length'], reverse=True)
            sticks = []
            long_parts = [p for p in parts_sorted if p['length'] >= 6000]
            short_parts = [p for p in parts_sorted if p['length'] < 6000]
            for part in long_parts:
                sticks.append({'remainder': 6000 - part['length'], 'parts': [part]})
            length_groups = defaultdict(list)
            for part in short_parts:
                length_groups[part['length']].append(part)
            for length_val in sorted(length_groups.keys(), reverse=True):
                group_parts = length_groups[length_val]
                total_length = length_val * len(group_parts)
                if total_length <= 6000:
                    best_stick_idx = -1
                    best_remainder = 6001
                    for idx, stick in enumerate(sticks):
                        if stick['remainder'] >= total_length:
                            new_remainder = stick['remainder'] - total_length
                            if new_remainder < best_remainder:
                                best_remainder = new_remainder
                                best_stick_idx = idx
                    if best_stick_idx >= 0:
                        for part in group_parts:
                            sticks[best_stick_idx]['parts'].append(part)
                        sticks[best_stick_idx]['remainder'] -= total_length
                    else:
                        new_stick = {'remainder': 6000 - total_length, 'parts': group_parts.copy()}
                        sticks.append(new_stick)
                else:
                    for part in group_parts:
                        best_stick_idx = -1
                        best_remainder = 6001
                        for idx, stick in enumerate(sticks):
                            if stick['remainder'] >= part['length']:
                                new_remainder = stick['remainder'] - part['length']
                                if new_remainder < best_remainder:
                                    best_remainder = new_remainder
                                    best_stick_idx = idx
                        if best_stick_idx >= 0:
                            sticks[best_stick_idx]['parts'].append(part)
                            sticks[best_stick_idx]['remainder'] -= part['length']
                        else:
                            sticks.append({'remainder': 6000 - part['length'], 'parts': [part]})
            total_cuts = sum(1 for p in parts_sorted if p['needs_cut'])
            total_splices = sum(1 for p in parts_sorted if p['is_splice'])
            cutting_result[profile] = {'sticks': sticks, 'total_parts': len(parts_sorted), 'total_cuts': total_cuts,
                                       'total_sticks': len(sticks), 'total_splices': total_splices}
        return cutting_result

    def show_cutting(self):
        if not self.current_materials:
            QMessageBox.warning(self, "Предупреждение", "Сначала выполните расчёт!")
            return
        cutting_data = self.calculate_cutting(self.current_materials)
        cutting_window = CuttingWindow(cutting_data, self)
        cutting_window.exec()

    def update_all(self):
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())
            beam = self.beam_combo.currentText()
            sections = self.sections_spin.value()
            diagonals = self.diagonals_check.isChecked()
            custom_cw = self.custom_cw_check.isChecked()
            paint_enabled = self.paint_check.isChecked()
            if custom_cw:
                custom_cw_length = int(self.custom_cw_input.text())
            else:
                custom_cw_length = width // 2
            if width <= 0 or height <= 0:
                QMessageBox.warning(self, "Ошибка", "Размеры должны быть больше 0!")
                return
            beam_h = 60 if beam == "SG01" else 85
            if height <= beam_h:
                QMessageBox.warning(self, "Ошибка", f"Общая высота должна быть больше {beam_h} мм!")
                return
            if custom_cw and custom_cw_length <= 0:
                QMessageBox.warning(self, "Ошибка", "Длина противовеса должна быть больше 0!")
                return
            self.gate_widget.setParameters(width, height, beam, sections, diagonals, custom_cw, custom_cw_length)
            self.current_materials = self.calculate_materials()
            self.current_paint_enabled = paint_enabled
            materials = self.current_materials
            self.table_widget.setRowCount(len(materials))
            total_weight = 0.0
            total_area = 0.0
            for row, mat in enumerate(materials):
                self.table_widget.setItem(row, 0, QTableWidgetItem(mat[0]))
                self.table_widget.setItem(row, 1, QTableWidgetItem(mat[1]))
                self.table_widget.setItem(row, 2, QTableWidgetItem(mat[2]))
                self.table_widget.setItem(row, 3, QTableWidgetItem(str(mat[3])))
                self.table_widget.setItem(row, 4, QTableWidgetItem(
                    f"{mat[4]:.2f}" if isinstance(mat[4], (int, float)) else mat[4]))
                self.table_widget.setItem(row, 5, QTableWidgetItem(
                    f"{mat[5]:.2f}" if isinstance(mat[5], (int, float)) else mat[5]))
                self.table_widget.setItem(row, 6, QTableWidgetItem(mat[6]))
                if isinstance(mat[4], (int, float)):
                    total_weight += mat[4]
                if isinstance(mat[5], (int, float)):
                    total_area += mat[5]
            self.table_widget.setRowCount(len(materials) + 1)
            self.table_widget.setItem(len(materials), 0, QTableWidgetItem("ИТОГО:"))
            self.table_widget.setItem(len(materials), 4, QTableWidgetItem(f"{total_weight:.2f} кг"))
            self.table_widget.setItem(len(materials), 5, QTableWidgetItem(f"{total_area:.2f} м²"))
            self.table_widget.resizeColumnsToContents()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Введите корректные числа!\n{e}")

    def _prepare_estimate_items(self):
        """Подготавливает список позиций из текущего расчёта"""
        cutting_data = self.calculate_cutting(self.current_materials)

        profile_groups = {}
        for mat in self.current_materials:
            profile = mat[1]
            length_mm = float(mat[2])
            quantity = int(mat[3])
            weight = float(mat[4])
            area = float(mat[5]) if len(mat) > 5 and mat[5] else 0

            if profile not in profile_groups:
                profile_groups[profile] = {
                    'total_length_mm': 0,
                    'total_weight': 0,
                    'total_area': 0,
                    'name': mat[0]
                }

            profile_groups[profile]['total_length_mm'] += length_mm * quantity
            profile_groups[profile]['total_weight'] += weight
            profile_groups[profile]['total_area'] += area

        estimate_items = []
        materials_db = db.get_materials()

        for profile, data in profile_groups.items():
            price = 0.0
            for m in materials_db:
                if m['name'] in profile or profile in m['name']:
                    price = float(m['retail_price']) if m['retail_price'] else 0.0
                    break

            if price == 0.0 and ('Балка' in profile or 'SG0' in profile):
                import re
                match = re.search(r'SG\d+', profile)
                if match:
                    beam_name = match.group(0)
                    beam = db.get_beam_by_name(beam_name)
                    if beam:
                        price = float(beam['retail_price']) if beam['retail_price'] else 0.0

            total_length_mm = data['total_length_mm']

            if profile in cutting_data:
                sticks_data = cutting_data[profile]['sticks']
                total_paid_length = 0
                total_remainder = 0

                for stick in sticks_data:
                    remainder = stick['remainder']
                    used_length = 6000 - remainder
                    total_remainder += remainder
                    paid_for_this_stick = used_length + (remainder % 1000)
                    total_paid_length += paid_for_this_stick

                sticks = len(sticks_data)
                remainder_for_client = sum(s['remainder'] % 1000 for s in sticks_data)
            else:
                sticks = 1
                total_paid_length = total_length_mm
                total_remainder = 0
                remainder_for_client = 0

            estimate_items.append({
                'name': data['name'],
                'profile': profile,
                'length_mm': total_length_mm,
                'length_for_payment_mm': total_paid_length,
                'sticks': sticks,
                'remainder_mm': total_remainder,
                'remainder_for_client': remainder_for_client,
                'weight': data['total_weight'],
                'price': price,
                'unit': 'м.п.'
            })

        # Покраска
        paint_enabled = self.paint_check.isChecked()
        total_paint_area = sum(data['total_area'] for data in profile_groups.values())

        if paint_enabled and total_paint_area > 0:
            paint_price = 0.0
            for m in materials_db:
                if 'покраск' in m['name'].lower():
                    paint_price = float(m['retail_price']) if m['retail_price'] else 0.0
                    break

            if paint_price > 0:
                estimate_items.append({
                    'name': 'Покраска',
                    'profile': 'Покраска',
                    'length_mm': total_paint_area * 1000,
                    'length_for_payment_mm': total_paint_area * 1000,
                    'sticks': 1,
                    'remainder_mm': 0,
                    'remainder_for_client': 0,
                    'weight': 0,
                    'price': paint_price,
                    'unit': 'м²',
                    'is_paint': True
                })
            else:
                QMessageBox.warning(self, "Внимание",
                                    "В справочнике материалов не задана цена на покраску!\n"
                                    "Покраска не будет добавлена в смету.")

        return estimate_items

    def open_estimate(self):
        from estimate_dialog import EstimateDialog
        if not self.current_materials:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните расчёт!")
            return

        # Если буфера нет — создаём из текущего расчёта
        if not hasattr(self, 'estimate_buffer') or not self.estimate_buffer:
            self.estimate_buffer = self._prepare_estimate_items()
        else:
            # Буфер уже есть — обновляем только расчётные позиции, сохраняя ручные
            new_calc = self._prepare_estimate_items()
            # Удаляем старые расчётные позиции (у них нет is_kit)
            # и оставляем ручные (добавленные через каталог)
            manual_items = [m for m in self.estimate_buffer if m.get('is_kit', False)]
            # Заменяем буфер: новый расчёт + старые ручные
            self.estimate_buffer = new_calc + manual_items

        dialog = EstimateDialog(
            self.estimate_buffer,
            self.current_client_name,
            self.current_client_address,
            self,
            cutting_data=self.calculate_cutting(self.current_materials),
            paint_enabled=self.paint_check.isChecked(),
            current_user=self.current_user
        )
        dialog.exec()

        dialog.sync_materials_from_table()
        self.estimate_buffer = dialog.materials

    def open_estimate_list(self):
        from estimate_list_dialog import EstimateListDialog
        dialog = EstimateListDialog(self, current_user=self.current_user)
        dialog.exec()

    def open_invoice(self):
        QMessageBox.information(self, "Счёт", "Функция в разработке")

    def open_waybill(self):
        QMessageBox.information(self, "Товарная накладная", "Функция в разработке")

    def open_act(self):
        QMessageBox.information(self, "Акт выполненных работ", "Функция в разработке")

    def report_clients(self):
        QMessageBox.information(self, "Отчёт по клиентам", "Функция в разработке")

    def report_materials(self):
        QMessageBox.information(self, "Отчёт по материалам", "Функция в разработке")

    def report_orders(self):
        QMessageBox.information(self, "Отчёт по заказам", "Функция в разработке")

    def export_excel(self):
        QMessageBox.information(self, "Экспорт в Excel", "Функция в разработке")

    def export_pdf(self):
        QMessageBox.information(self, "Экспорт в PDF", "Функция в разработке")

    def connect_db(self):
        QMessageBox.information(self, "Подключение к БД", "Функция в разработке")

    def disconnect_db(self):
        QMessageBox.information(self, "Отключение от БД", "Функция в разработке")

    def backup_db(self):
        QMessageBox.information(self, "Резервная копия", "Функция в разработке")

    def restore_db(self):
        QMessageBox.information(self, "Восстановление", "Функция в разработке")

    def open_clients(self):
        dialog = ClientDialog(self)
        dialog.exec()

    def open_addresses(self):
        QMessageBox.information(self, "Адреса", "Открывается из карточки клиента")

    def open_materials(self):
        dialog = MaterialTreeDialog(self)
        dialog.exec()

    def open_units(self):
        dialog = UnitDialog(self)
        dialog.exec()

    def open_beam_types(self):
        dialog = BeamTypesDialog(self)
        dialog.exec()

    def open_help(self):
        QMessageBox.information(self, "Руководство пользователя", "Функция в разработке")

    def show_about(self):
        user_info = ""
        if self.current_user:
            user_info = f"\n\n👤 Текущий пользователь:\n{self.current_user['full_name']}"
        QMessageBox.about(
            self, "О программе",
            "Конструктор откатных ворот\n\n"
            "Версия: 1.0\n\n"
            "💡 Автор идеи:\nВольперт Сергей Сергеевич\n\n"
            "🔧 Ему немного помогал:\nКосарев Константин\n\n"
            "🤖 Разработка при участии AI-ассистентов:\nDeepSeek, Qwen\n\n"
            "📅 2026 год\n\n"
            "🐍 Python 3.11 + PyQt6 + PostgreSQL\n\n"
            "Программа разработана для расчёта материалов,\n"
            "раскроя профилей и составления смет\n"
            "для откатных ворот." + user_info
        )


class BeamTypesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Типы направляющих балок")
        self.setMinimumSize(700, 300)
        self._closed = False
        layout = QVBoxLayout(self)
        hint = QLabel("💡 Здесь можно задать цены на направляющие балки.\nЦены автоматически подтянутся в смету.")
        hint.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Марка", "Высота (мм)", "Ширина (мм)", "Вес (кг/м)", "Цена закуп.", "Цена розн.", "Описание"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 110)
        self.table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        self.close_btn = QPushButton("❌ Закрыть")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        self.load_data()

    def closeEvent(self, event):
        self._closed = True
        super().closeEvent(event)

    def load_data(self):
        self.table.blockSignals(True)
        try:
            beams = db.get_all_beam_types_full()
            self.table.setRowCount(len(beams))
            for row, beam in enumerate(beams):
                name_item = QTableWidgetItem(beam['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, name_item)
                h_item = QTableWidgetItem(str(beam['height_mm']))
                h_item.setFlags(h_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, h_item)
                w_item = QTableWidgetItem(str(beam['width_mm']))
                w_item.setFlags(w_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, w_item)
                weight_item = QTableWidgetItem(f"{beam['weight_kg_per_m']:.2f}")
                weight_item.setFlags(weight_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, weight_item)
                purchase_item = QTableWidgetItem(f"{beam['purchase_price']:.2f}")
                self.table.setItem(row, 4, purchase_item)
                retail_item = QTableWidgetItem(f"{beam['retail_price']:.2f}")
                self.table.setItem(row, 5, retail_item)
                desc_item = QTableWidgetItem(f"Направляющая балка {beam['name']}")
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 6, desc_item)
        finally:
            self.table.blockSignals(False)

    def on_cell_changed(self, row, col):
        if col not in [4, 5]:
            return
        try:
            beam_name = self.table.item(row, 0).text()
            try:
                purchase = float(self.table.item(row, 4).text() or 0)
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Цена закупки должна быть числом!")
                return
            try:
                retail = float(self.table.item(row, 5).text() or 0)
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Розничная цена должна быть числом!")
                return
            self.table.blockSignals(True)
            try:
                success = db.update_beam_prices(beam_name, purchase, retail)
                if success:
                    item = self.table.item(row, col)
                    item.setBackground(QColor(200, 255, 200))
                    QTimer.singleShot(1500, lambda: self._safe_reset_color(item))
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить цену!")
            finally:
                self.table.blockSignals(False)
        except Exception as e:
            print(f"Ошибка при сохранении цены балки: {e}")

    def _safe_reset_color(self, item):
        if self._closed:
            return
        try:
            if item and item.tableWidget() is not None:
                item.setBackground(QColor(255, 255, 255))
        except RuntimeError:
            pass


def main():
    from login_dialog import LoginDialog
    app = QApplication(sys.argv)

    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    app.setPalette(palette)

    try:
        print("🔄 Проверка подключения к БД...")
        if not db.init_db():
            QMessageBox.critical(None, "Ошибка",
                                 "Не удалось инициализировать базу данных!\n\n"
                                 "Проверьте:\n"
                                 "1. Запущен ли PostgreSQL\n"
                                 "2. Правильность настроек в config.py\n"
                                 "3. Пароль пользователя postgres")
            sys.exit(1)
        print("✅ БД готова к работе")
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД",
                             f"Не удалось подключиться к базе данных:\n\n{e}")
        sys.exit(1)

    while True:
        login_dialog = LoginDialog()
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

        user = login_dialog.get_current_user()

        window = MainWindow()
        window.current_user = user
        window.showMaximized()

        result = app.exec()
        if result != 0:
            sys.exit(result)


if __name__ == "__main__":
    main()