import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QTextEdit, QMessageBox, QFileDialog, QGroupBox, QDoubleSpinBox, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# База стандартных материалов (Название: (длина_мм, ширина_мм, цена_руб))
MATERIALS_DB = {
    "Фанера ФК (1525 x 1525 мм)": (1525, 1525, 1450.0),
    "ЛДСП ламинированная (2750 x 1830 мм)": (2750, 1830, 3200.0),
    "Оргстекло / Акрил (2050 x 3050 мм)": (2050, 3050, 4800.0),
    "Лист стальной х/к (2500 x 1250 мм)": (2500, 1250, 3900.0),
    "Свой материал (ввести вручную)": (1000, 1000, 1000.0)
}


class MasterSmetaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.last_report = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("МастерСмета v1.0 — Расчёт материалов и себестоимости")
        self.setFixedSize(680, 720)

        # Главный виджет и основной вертикальный слой
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)

        # Заголовок программы
        title_label = QLabel("Калькулятор раскроя листовых материалов и себестоимости")
        title_font = QFont("Arial", 13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # --- БЛОК 1: Данные об изделии и листе материала ---
        sheet_group = QGroupBox("1. Параметры изделия и исходного листа")
        sheet_form = QFormLayout()

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Например: Полка настенная или Ящик для инструментов")
        sheet_form.addRow("Название изделия:", self.project_name_input)

        self.material_combo = QComboBox()
        self.material_combo.addItems(MATERIALS_DB.keys())
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        sheet_form.addRow("Тип материала:", self.material_combo)

        # Габариты листа в одну строку
        sheet_dims_layout = QHBoxLayout()
        self.sheet_len_input = QDoubleSpinBox()
        self.sheet_len_input.setRange(10, 10000)
        self.sheet_len_input.setSuffix(" мм")

        self.sheet_wid_input = QDoubleSpinBox()
        self.sheet_wid_input.setRange(10, 10000)
        self.sheet_wid_input.setSuffix(" мм")

        sheet_dims_layout.addWidget(QLabel("Длина:"))
        sheet_dims_layout.addWidget(self.sheet_len_input)
        sheet_dims_layout.addWidget(QLabel("Ширина:"))
        sheet_dims_layout.addWidget(self.sheet_wid_input)
        sheet_form.addRow("Размеры листа:", sheet_dims_layout)

        self.sheet_price_input = QDoubleSpinBox()
        self.sheet_price_input.setRange(1, 1000000)
        self.sheet_price_input.setDecimals(2)
        self.sheet_price_input.setSuffix(" руб.")
        sheet_form.addRow("Цена 1 листа:", self.sheet_price_input)

        sheet_group.setLayout(sheet_form)
        main_layout.addWidget(sheet_group)

        # --- БЛОК 2: Параметры деталей и доп. расходов ---
        parts_group = QGroupBox("2. Параметры заготовок и дополнительные затраты")
        parts_form = QFormLayout()

        part_dims_layout = QHBoxLayout()
        self.part_len_input = QDoubleSpinBox()
        self.part_len_input.setRange(1, 10000)
        self.part_len_input.setValue(400)
        self.part_len_input.setSuffix(" мм")

        self.part_wid_input = QDoubleSpinBox()
        self.part_wid_input.setRange(1, 10000)
        self.part_wid_input.setValue(250)
        self.part_wid_input.setSuffix(" мм")

        part_dims_layout.addWidget(QLabel("Длина:"))
        part_dims_layout.addWidget(self.part_len_input)
        part_dims_layout.addWidget(QLabel("Ширина:"))
        part_dims_layout.addWidget(self.part_wid_input)
        parts_form.addRow("Размер одной детали:", part_dims_layout)

        self.parts_count_input = QSpinBox()
        self.parts_count_input.setRange(1, 1000)
        self.parts_count_input.setValue(4)
        self.parts_count_input.setSuffix(" шт.")
        parts_form.addRow("Количество деталей:", self.parts_count_input)

        self.waste_percent_input = QSpinBox()
        self.waste_percent_input.setRange(0, 50)
        self.waste_percent_input.setValue(15)
        self.waste_percent_input.setSuffix(" %")
        parts_form.addRow("Припуск на пропил и обрезки:", self.waste_percent_input)

        self.extra_cost_input = QDoubleSpinBox()
        self.extra_cost_input.setRange(0, 100000)
        self.extra_cost_input.setValue(120.0)
        self.extra_cost_input.setDecimals(2)
        self.extra_cost_input.setSuffix(" руб.")
        parts_form.addRow("Фурнитура, клей, электроэнергия:", self.extra_cost_input)

        parts_group.setLayout(parts_form)
        main_layout.addWidget(parts_group)

        # --- БЛОК 3: Кнопки управления ---
        btn_layout = QHBoxLayout()

        self.calc_btn = QPushButton("Рассчитать смету")
        self.calc_btn.setStyleSheet(
            "background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;"
        )
        self.calc_btn.clicked.connect(self.calculate)

        self.save_btn = QPushButton("Сохранить смету в файл (.txt)")
        self.save_btn.setStyleSheet("padding: 8px;")
        self.save_btn.clicked.connect(self.save_to_file)

        self.about_btn = QPushButton("О проекте")
        self.about_btn.setStyleSheet("padding: 8px;")
        self.about_btn.clicked.connect(self.show_about)

        btn_layout.addWidget(self.calc_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.about_btn)
        main_layout.addLayout(btn_layout)

        # --- БЛОК 4: Поле вывода результата ---
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setFont(QFont("Consolas", 10))
        self.result_output.setPlaceholderText("Здесь появится готовая технологическая смета...")
        main_layout.addWidget(self.result_output)

        # Заполняем начальные значения для первого материала из списка
        self.on_material_changed(self.material_combo.currentText())

    def on_material_changed(self, material_name):
        """Автоматически подставляет стандартные габариты и цену выбранного листа."""
        length, width, price = MATERIALS_DB[material_name]
        self.sheet_len_input.setValue(length)
        self.sheet_wid_input.setValue(width)
        self.sheet_price_input.setValue(price)

    def calculate(self):
        """Основной алгоритм расчёта площади, расхода материала и себестоимости."""
        project_name = self.project_name_input.text().strip() or "Без названия"
        material_name = self.material_combo.currentText()

        s_len = self.sheet_len_input.value()
        s_wid = self.sheet_wid_input.value()
        s_price = self.sheet_price_input.value()

        p_len = self.part_len_input.value()
        p_wid = self.part_wid_input.value()
        p_count = self.parts_count_input.value()
        waste_pct = self.waste_percent_input.value()
        extra_cost = self.extra_cost_input.value()

        # Проверка: помещается ли хотя бы одна деталь на лист по габаритам
        fits_normal = (p_len <= s_len and p_wid <= s_wid)
        fits_rotated = (p_len <= s_wid and p_wid <= s_len)
        if not (fits_normal or fits_rotated):
            QMessageBox.warning(
                self,
                "Ошибка габаритов",
                "Размеры одной детали превышают габариты целого листа! Проверьте ввод."
            )
            return

        # Перевод площади из мм² в м² (1 м² = 1 000 000 мм²)
        sheet_area_m2 = (s_len * s_wid) / 1_000_000
        clean_parts_area_m2 = ((p_len * p_wid) * p_count) / 1_000_000

        # Учёт технологических припусков (на пропил, шлифовку и обрезки)
        waste_factor = 1 + (waste_pct / 100.0)
        total_required_area_m2 = clean_parts_area_m2 * waste_factor

        # Расчёт необходимого количества листов и стоимости материала
        sheets_fraction = total_required_area_m2 / sheet_area_m2
        material_cost = sheets_fraction * s_price
        total_cost = material_cost + extra_cost

        status_msg = "Одного стандартного листа ДОСТАТОЧНО."
        if sheets_fraction > 1.0:
            needed_whole_sheets = int(sheets_fraction) + (1 if sheets_fraction % 1 > 0 else 0)
            status_msg = f"ВНИМАНИЕ: Одного листа НЕ ХВАТИТ! Для закупки потребуется листов: {needed_whole_sheets} шт."

        report = (
            f"==========================================================\n"
            f"ТЕХНОЛОГИЧЕСКАЯ СМЕТА И РАСЧЁТ СЕБЕСТОИМОСТИ\n"
            f"Дата расчёта: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"==========================================================\n"
            f"Изделие: {project_name}\n"
            f"Материал: {material_name}\n"
            f"Габариты листа: {s_len:.0f} x {s_wid:.0f} мм (Площадь: {sheet_area_m2:.3f} м²)\n"
            f"Детали: {p_count} шт. размером {p_len:.0f} x {p_wid:.0f} мм\n"
            f"----------------------------------------------------------\n"
            f"1. Чистая площадь деталей:          {clean_parts_area_m2:.4f} м²\n"
            f"2. Площадь с припуском ({waste_pct}%):       {total_required_area_m2:.4f} м²\n"
            f"3. Доля расхода от одного листа:    {sheets_fraction * 100:.1f} %\n"
            f"4. Статус обеспечения материалом:   {status_msg}\n"
            f"----------------------------------------------------------\n"
            f"ФИНАНСОВЫЙ РАСЧЁТ:\n"
            f"• Затраты на основной материал:     {material_cost:.2f} руб.\n"
            f"• Доп. расходы (фурнитура, эл-во):  {extra_cost:.2f} руб.\n"
            f"• ИТОГОВАЯ СЕБЕСТОИМОСТЬ ИЗДЕЛИЯ:   {total_cost:.2f} руб.\n"
            f"=========================================================="
        )
        self.last_report = report
        self.result_output.setText(report)

    def save_to_file(self):
        """Сохраняет сформированную смету в текстовый файл."""
        if not self.last_report:
            QMessageBox.information(self, "Нет данных", "Сначала нажмите кнопку «Рассчитать смету».")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить смету",
            "smeta_izdeliya.txt",
            "Текстовые файлы (.txt);;Все файлы ()"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.last_report)
                QMessageBox.information(self, "Успешно", f"Смета сохранена в файл:\n{file_path}")

    def show_about(self):
        """Окно с информацией об авторе проекта для жюри."""
        QMessageBox.about(
            self,
            "О программе",
            "Программный модуль «МастерСмета v1.0»\n\n"
            "Проект для муниципального этапа ВсОШ по труду (технологии).\n"
            "Назначение: автоматизация расчёта раскроя листовых материалов "
            "с учётом технологических припусков и расчёта себестоимости.\n\n"
            "Стек технологий: Python 3, PyQt6."
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MasterSmetaApp()
    window.show()
    sys.exit(app.exec())
    