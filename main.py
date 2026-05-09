# import sys
# import os
# import threading
# from PySide6.QtWidgets import QApplication
# from ui.face_ui import AvatarFace
# from core.assistant_controller import AssistantController
# from utils.logger import logger
# from utils.helpers import load_user_name
# from config.settings import settings
# from core.event_bus import event_bus

import sys, os, threading
from PySide6.QtWidgets import QApplication
from ui.face_ui import AvatarFace
from core.assistant_controller import AssistantController
from utils.logger import logger
from utils.helpers import load_user_name
from config.settings import settings
from core.event_bus import event_bus

def main():
    os.makedirs("data", exist_ok=True)
    app = QApplication(sys.argv)
    face = AvatarFace()
    face.show()

    controller = AssistantController(face)

    def delayed_greeting():
        threading.Event().wait(1.5)
        controller.greet_user()
        threading.Event().wait(1.0)
        controller.stt.start_listening()

    threading.Thread(target=delayed_greeting, daemon=True).start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

# main.py


def main():
    os.makedirs("data", exist_ok=True)
    app = QApplication(sys.argv)
    face = AvatarFace()
    face.show()
    controller = AssistantController(face)

    def delayed_greeting():
        threading.Event().wait(1.5)
        controller.greet_user()
        threading.Event().wait(1.0)
        controller.stt.start_listening()

    threading.Thread(target=delayed_greeting, daemon=True).start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()