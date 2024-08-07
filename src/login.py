from PySide6.QtWidgets import QMainWindow
from ui import login_ui
from discord_integration import login, load_token
import platformdirs


class LoginUI(QMainWindow, login_ui.Ui_MainWindow):
    def __init__(self, switcher, parent=None):
        super().__init__(parent)

        self.ui = login_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.info_frame.hide()

        self.ui.pushButton.clicked.connect(self.switch)
        self.switcher = switcher

        self.ui.password.returnPressed.connect(self.switch)

    def switch(self):
        email = self.ui.email.text()
        password = self.ui.password.text()
        valid = email and password

        if valid:
            # Reset our UI elements
            self.ui.email.setText("")
            self.ui.password.setText("")
            self.ui.info_frame.hide()

            # Get the token from the Discord API using our credentials.
            _token = login(email, password)

            if _token:
                with open(
                    platformdirs.user_config_dir("QTCord") + "/discordauth.txt", "w"
                ) as f:
                    f.write(_token)

                load_token()

                # Switch the page to the chat page
                self.switcher.setCurrentIndex(self.switcher.currentIndex() + 1)
            else:
                # Show the info_frame on login error
                self.ui.info_frame.show()
        else:
            # Show the info_frame if fields are empty
            self.ui.info_frame.show()
