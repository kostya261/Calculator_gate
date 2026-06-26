import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Тест PyQt6")
window.setGeometry(300, 300, 400, 200)

label = QLabel("✅ PyQt6 работает!", parent=window)
label.move(100, 80)

window.show()
sys.exit(app.exec())