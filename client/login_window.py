import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amiral Battı - Giriş")
        self.setGeometry(300, 200, 400, 250)

        self.init_ui()

    def init_ui(self):
        title_label = QLabel("Amiral Battı")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        username_label = QLabel("Kullanıcı Adı:")
        self.username_input = QLineEdit()

        ip_label = QLabel("Sunucu IP:")
        self.ip_input = QLineEdit()
        self.ip_input.setText("127.0.0.1")

        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setText("5000")

        self.connect_button = QPushButton("Bağlan")
        self.exit_button = QPushButton("Çıkış")

        self.connect_button.clicked.connect(self.connect_to_server)
        self.exit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(ip_label)
        layout.addWidget(self.ip_input)
        layout.addWidget(port_label)
        layout.addWidget(self.port_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.exit_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def connect_to_server(self):
        username = self.username_input.text().strip()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        if not username:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı boş olamaz.")
            return

        if not ip:
            QMessageBox.warning(self, "Hata", "IP adresi boş olamaz.")
            return

        if not port.isdigit():
            QMessageBox.warning(self, "Hata", "Port sayısal olmalıdır.")
            return

        QMessageBox.information(
            self,
            "Bilgi",
            f"Bağlantı bilgileri:\nKullanıcı: {username}\nIP: {ip}\nPort: {port}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())