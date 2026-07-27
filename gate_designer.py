import sys
import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


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

    def setParameters(self, width, height, beam_type, sections, diagonals_enabled, custom_cw, custom_cw_length):
        self.width_opening = width
        self.height_total = height
        self.beam_type = beam_type
        self.sections = sections
        self.diagonals_enabled = diagonals_enabled
        self.custom_counterweight = custom_cw
        self.custom_counterweight_length = custom_cw_length
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

        # Внешняя рама
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        outer_left_offset = (outer_w_px - frame_w_px) / 2
        outer_x = base_x + outer_left_offset
        painter.drawRect(int(outer_x), int(base_y), int(outer_w_px), int(frame_h_px))

        counterweight_x = outer_x + outer_w_px
        painter.drawRect(int(counterweight_x), int(base_y), int(counterweight_w_px), int(frame_h_px))

        # Балка
        beam_y = base_y + frame_h_px
        beam_start_x = outer_x
        beam_width_px = outer_w_px + counterweight_w_px

        painter.fillRect(int(beam_start_x), int(beam_y), int(beam_width_px), int(beam_h_px), QColor(70, 100, 200))
        painter.setPen(QPen(QColor(50, 70, 150), 1))
        painter.drawRect(int(beam_start_x), int(beam_y), int(beam_width_px), int(beam_h_px))

        # Диагональ противовеса
        if self.diagonals_enabled:
            painter.setPen(QPen(Qt.GlobalColor.black, 3))
            painter.drawLine(int(counterweight_x), int(base_y), int(counterweight_x + counterweight_w_px),
                             int(base_y + frame_h_px))

        # Наполнение
        painter.setPen(QPen(QColor(200, 0, 0), 2))

        inner_w_px = frame_w_px
        inner_h_mm = H_frame_mm - 2 * self.beam_width[self.beam_type]
        inner_h_px = inner_h_mm * scale

        inner_x = outer_x + (outer_w_px - inner_w_px) / 2
        inner_y_offset = self.beam_width[self.beam_type] * scale
        inner_y = base_y + inner_y_offset

        painter.drawRect(int(inner_x), int(inner_y), int(inner_w_px), int(inner_h_px))

        # Вертикальные стойки
        if self.sections > 0:
            step = inner_w_px / self.sections
            for i in range(self.sections + 1):
                x = inner_x + i * step
                painter.drawLine(int(x), int(inner_y), int(x), int(inner_y + inner_h_px))

        # Горизонталь по центру
        center_y = inner_y + inner_h_px / 2
        painter.drawLine(int(inner_x), int(center_y), int(inner_x + inner_w_px), int(center_y))

        # Диагонали в раме
        if self.diagonals_enabled and self.sections > 0:
            bottom_y = inner_y + inner_h_px
            for i in range(self.sections):
                x1 = inner_x + i * step
                x2 = inner_x + (i + 1) * step
                if i % 2 == 0:
                    painter.drawLine(int(x1), int(bottom_y), int(x2), int(center_y))
                else:
                    painter.drawLine(int(x1), int(center_y), int(x2), int(bottom_y))

        # Наполнение противовеса
        if self.diagonals_enabled:
            cw_x = counterweight_x
            cw_w_px = counterweight_w_px
            cw_h_px = frame_h_px
            cw_center_y = base_y + cw_h_px / 2
            intersection_x = cw_x + cw_w_px / 2
            painter.drawLine(int(cw_x), int(cw_center_y), int(intersection_x), int(cw_center_y))
            painter.drawLine(int(intersection_x), int(cw_center_y), int(intersection_x), int(base_y + cw_h_px))

        # Размеры
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

        # Общий итог
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

        # Ручная длина противовеса
        self.custom_cw_check = QCheckBox("Своя длина противовеса")
        self.custom_cw_check.toggled.connect(self.on_custom_cw_toggled)
        left_layout.addWidget(self.custom_cw_check)

        self.custom_cw_input = QLineEdit("2000")
        self.custom_cw_input.setEnabled(False)
        self.custom_cw_input.setPlaceholderText("Длина противовеса (мм)")
        left_layout.addWidget(self.custom_cw_input)

        self.diagonals_check = QCheckBox("Диагонали (ферма)")
        left_layout.addWidget(self.diagonals_check)

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
        self.update_all()

    def on_custom_cw_toggled(self, checked):
        self.custom_cw_input.setEnabled(checked)

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

        # Балка
        beam_area = beam_length / 1000 * beam_perimeter[beam_type]
        details.append(
            ["Балка", f"Балка SG{beam_type}", f"{beam_length:.0f}", 1, beam_length * beam_weight / 1000, beam_area, ""])

        # Каркас
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

        # Наполнение
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

                        profile_groups[profile].append({
                            'name': segment_name,
                            'length': segment_length,
                            'profile': profile,
                            'needs_cut': needs_cut,
                            'is_splice': segment_num > 1
                        })
                        remaining -= segment_length
                        segment_num += 1
                else:
                    needs_cut = (length < 6000)
                    profile_groups[profile].append({
                        'name': name,
                        'length': length,
                        'profile': profile,
                        'needs_cut': needs_cut,
                        'is_splice': False
                    })

        cutting_result = {}

        for profile, parts in profile_groups.items():
            parts_sorted = sorted(parts, key=lambda x: x['length'], reverse=True)
            sticks = []

            # Длинные детали (>= 6000 мм) — в отдельные хлысты
            long_parts = [p for p in parts_sorted if p['length'] >= 6000]
            short_parts = [p for p in parts_sorted if p['length'] < 6000]

            for part in long_parts:
                sticks.append({
                    'remainder': 6000 - part['length'],
                    'parts': [part]
                })

            # Группируем короткие детали по длине
            from collections import defaultdict
            length_groups = defaultdict(list)
            for part in short_parts:
                length_groups[part['length']].append(part)

            # Сортируем группы по убыванию длины
            for length_val in sorted(length_groups.keys(), reverse=True):
                group_parts = length_groups[length_val]
                # Пытаемся упаковать группу в один хлыст
                total_length = length_val * len(group_parts)
                if total_length <= 6000:
                    # Все детали группы помещаются в один хлыст
                    # Ищем хлыст с наименьшим остатком после добавления
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
                        # Новый хлыст
                        new_stick = {
                            'remainder': 6000 - total_length,
                            'parts': group_parts.copy()
                        }
                        sticks.append(new_stick)
                else:
                    # Группа не помещается в один хлыст — упаковываем по отдельности
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
                            sticks.append({
                                'remainder': 6000 - part['length'],
                                'parts': [part]
                            })

            total_cuts = sum(1 for p in parts_sorted if p['needs_cut'])
            total_splices = sum(1 for p in parts_sorted if p['is_splice'])

            cutting_result[profile] = {
                'sticks': sticks,
                'total_parts': len(parts_sorted),
                'total_cuts': total_cuts,
                'total_sticks': len(sticks),
                'total_splices': total_splices
            }

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


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()