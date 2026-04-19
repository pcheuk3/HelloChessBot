from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QSlider,
    QHBoxLayout,
    QDialog,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence

from Utils.i18n import t


class CustomButton(QPushButton):
    def keyPressEvent(self, event):
        # Only ignore arrow keys for this button
        if event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            event.ignore()
        else:
            super().keyPressEvent(event)


class CustomComboBox(QComboBox):


    def __init__(self, parent=None):
        super(CustomComboBox, self).__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            if not self.view().isVisible():
                # if the dropdown menu is not opened, open it
                self.showPopup()
            # move to the previous option
            current_index = self.currentIndex()
            if current_index > 0:
                self.setCurrentIndex(current_index - 1)
            else:
                self.setCurrentIndex(self.count() - 1)
            # trigger the highlighted signal to read the current option
            self.highlighted.emit(self.currentIndex())
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            if not self.view().isVisible():
                # if the dropdown menu is not opened, open it
                self.showPopup()
            # move to the next option
            current_index = self.currentIndex()
            if current_index < self.count() - 1:
                self.setCurrentIndex(current_index + 1)
            else:
                self.setCurrentIndex(0)
            # trigger the highlighted signal to read the current option
            self.highlighted.emit(self.currentIndex())
            event.accept()
        elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            # Enter key confirm the selection
            if self.view().isVisible():
                self.hidePopup()
                self.currentIndexChanged.emit(self.currentIndex())
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Escape:
            # Escape key close the dropdown menu but not change the selection
            if self.view().isVisible():
                self.hidePopup()
            else:
                event.ignore()
        else:
            # other keys use the default behavior
            super().keyPressEvent(event)


class SettingMenu(QDialog):
    @staticmethod
    def _normalize_volume_to_slider_value(volume) -> int:
        """
        Accept either 0.0-1.0 float volume or 0-100 percent volume.
        Always return an int in [0, 100] for QSlider.
        """
        try:
            v = float(volume)
        except (TypeError, ValueError):
            v = 0.7

        if v <= 1.0:
            v *= 100.0
        v = round(v)
        return int(max(0, min(100, v)))

    @staticmethod
    def _normalize_rate_to_slider_value(rate) -> int:
        try:
            r = float(rate)
        except (TypeError, ValueError):
            r = 50.0
        r = round(r)
        return int(max(0, min(100, r)))

    def __init__(self, parent=None, rate=50, volume=0.7, engine=True, language: str = "en", font_size=22, speak_func=None, language_change_callback=None):
        super().__init__(parent)
        self._speak_func = speak_func
        self._language_value = str(language or "en")
        self._language_change_callback = language_change_callback
        # Set window title and size
        self.setWindowTitle(t("settings.title"))
        # self.setGeometry(200, 200, 400, 200)
        self.setMinimumSize(500, 500)

        # Create layout
        layout = QVBoxLayout()
        language_layout = QHBoxLayout()
        rate_layout = QHBoxLayout()
        volume_layout = QHBoxLayout()
        font_size_layout = QHBoxLayout()
        voice_trigger_layout = QHBoxLayout()

        # Language dropdown
        self.language_label = QLabel(t("settings.language.label"))
        self.language_label.setMinimumWidth(100)
        self.language_combo = CustomComboBox()
        self.language_combo.setAccessibleName(t("settings.language.label"))
        self.language_combo.setAccessibleDescription(t("settings.language.desc"))
        self.language_combo.addItem(t("settings.language.en"), "en")
        self.language_combo.addItem(t("settings.language.zh_tw"), "zh-TW")
        self.language_combo.addItem(t("settings.language.zh_cn"), "zh-CN")
        idx = self.language_combo.findData(self._language_value)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

        # bind the speech hint: read the current option when the option is changed
        self.language_combo.highlighted.connect(lambda idx: self._speak(self.language_combo.itemText(idx)))
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)

        # Create checkbox
        self.engine_value = engine
        self.screen_reader_checkBox = QCheckBox(t("settings.engine.checkbox"))
        self.screen_reader_checkBox.setChecked(engine)
        self.screen_reader_checkBox.setAccessibleName(t("settings.engine.checkbox"))
        self.screen_reader_checkBox.setAccessibleDescription(
            t("settings.engine.checkbox.desc")
        )
        layout.addWidget(self.screen_reader_checkBox)

        # Create font size slider
        self.font_size_label = QLabel(t("settings.font_size.label"))
        self.font_size_label.setMinimumWidth(100)

        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(10)
        self.font_size_slider.setMaximum(40)
        self.font_size_slider.setValue(int(font_size))
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.font_size_slider.setTickInterval(5)
        self.font_size_slider.setAccessibleName(t("settings.font_size.label"))
        self.font_size_slider.setAccessibleDescription(t("settings.font_size.desc"))

        self.font_size_value_label = QLabel()
        self.font_size_value_label.setText(str(int(font_size)))

        font_size_layout.addWidget(self.font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value_label)
        layout.addLayout(font_size_layout)

        # Voice trigger mode selection
        self.voice_trigger_label = QLabel(t("settings.voice_trigger.label"))
        self.voice_trigger_label.setMinimumWidth(100)
        self.voice_trigger_combo = CustomComboBox()
        self.voice_trigger_combo.setAccessibleName(t("settings.voice_trigger.label"))
        self.voice_trigger_combo.setAccessibleDescription(
            t("settings.voice_trigger.desc")
        )
        self.voice_trigger_combo.addItem(t("settings.voice_trigger.toggle"), "toggle")
        self.voice_trigger_combo.addItem(t("settings.voice_trigger.hold"), "hold")
        self.voice_trigger_combo.highlighted.connect(
            lambda idx: self._announce_voice_trigger_current()
        )
        voice_trigger_layout.addWidget(self.voice_trigger_label)
        voice_trigger_layout.addWidget(self.voice_trigger_combo)
        layout.addLayout(voice_trigger_layout)

        # Create slider
        self.rate_label = QLabel(t("settings.rate.label"))
        self.rate_label.setMinimumWidth(100)

        self.speech_rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.speech_rate_slider.setMinimum(0)
        self.speech_rate_slider.setMaximum(100)
        rate_slider_value = self._normalize_rate_to_slider_value(rate)
        self.speech_rate_slider.setValue(rate_slider_value)
        self.speech_rate_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.speech_rate_slider.setTickInterval(10)
        self.speech_rate_slider.setAccessibleName(t("settings.rate.label"))
        self.speech_rate_slider.setAccessibleDescription(t("settings.rate.desc"))

        self.speech_rate_value_label = QLabel()
        self.speech_rate_value_label.setText(str(rate_slider_value))

        rate_layout.addWidget(self.rate_label)
        rate_layout.addWidget(self.speech_rate_slider)
        rate_layout.addWidget(self.speech_rate_value_label)

        self.volume_label = QLabel(t("settings.volume.label"))
        self.volume_label.setMinimumWidth(100)  # Set minimum width for consistent alignment

        self.speech_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.speech_volume_slider.setMinimum(0)
        self.speech_volume_slider.setMaximum(100)
        volume_slider_value = self._normalize_volume_to_slider_value(volume)
        self.speech_volume_slider.setValue(volume_slider_value)
        self.speech_volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.speech_volume_slider.setTickInterval(10)
        self.speech_volume_slider.setAccessibleName(t("settings.volume.label"))
        self.speech_volume_slider.setAccessibleDescription(t("settings.volume.desc"))

        self.volume_value_label = QLabel()
        self.volume_value_label.setText(str(volume_slider_value))

        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.speech_volume_slider)
        volume_layout.addWidget(self.volume_value_label)

        # Connect slider value change to update label
        self.font_size_slider.valueChanged.connect(self.font_size_changed)
        self.speech_rate_slider.valueChanged.connect(self.rate_changed)
        self.speech_volume_slider.valueChanged.connect(self.volume_changed)
        self.screen_reader_checkBox.stateChanged.connect(self.checkBoxStateChanged)

        layout.addLayout(rate_layout)
        layout.addLayout(volume_layout)

        # Create OK button to close the dialog
        ok_button = CustomButton(t("settings.ok"))
        ok_button.setAccessibleName(t("settings.ok"))
        ok_button.setAccessibleDescription(t("settings.ok.desc"))
        ok_button.clicked.connect(self.OK_pressed)
        layout.addWidget(ok_button)

        self.setting_layout = []
        self.setting_layout.append(self.language_combo)
        self.setting_layout.append(self.screen_reader_checkBox)
        self.setting_layout.append(self.font_size_slider)
        self.setting_layout.append(self.voice_trigger_combo)
        self.setting_layout.append(self.speech_rate_slider)
        self.setting_layout.append(self.speech_volume_slider)
        self.setting_layout.append(ok_button)

        # Set layout
        self.setLayout(layout)

        self.currentfocus = 0  # start from the first one
        self._allow_voice_trigger_announce = False

        tab = QShortcut(QKeySequence("tab"), self)
        tab.activated.connect(self.tabHandler)

    def _speak(self, sentence):
        if callable(self._speak_func):
            self._speak_func(sentence)

    def _on_language_changed(self, idx):
        lang = self.get_language_value()
        if callable(self._language_change_callback):
            try:
                self._language_change_callback(lang)
            except Exception:
                pass

        self._speak(
            f"{t('settings.language.label')} {self.language_combo.itemText(idx)}"
        )

    def checkBoxStateChanged(self, state):
        print(state)
        if state == 2:
            self.engine_value = True
            self._speak(t("speak.settings.engine_on"))
        else:
            self.engine_value = False
            self._speak(t("speak.settings.engine_off"))

    def get_engine_value(self):
        return self.engine_value

    def get_language_value(self) -> str:
        return str(self.language_combo.currentData() or "en")

    def set_voice_trigger_mode(self, mode: str):
        target = "toggle" if str(mode).lower() == "toggle" else "hold"
        idx = self.voice_trigger_combo.findData(target)
        if idx >= 0:
            self.voice_trigger_combo.setCurrentIndex(idx)

    def get_voice_trigger_mode(self) -> str:
        return str(self.voice_trigger_combo.currentData() or "toggle")

    def OK_pressed(self):
        self._speak(t("speak.settings.saved"))
        self.accept()

    def font_size_changed(self, value):
        self._speak(str(value))
        self.font_size_value_label.setText(str(value))

    def rate_changed(self, value):
        self._speak(str(value))
        self.speech_rate_value_label.setText(str(value))

    def volume_changed(self, value):
        self._speak(str(value))
        self.volume_value_label.setText(str(value))

    def get_rate_value(self):
        return self.speech_rate_slider.value()

    def get_font_size_value(self) -> int:
        return int(self.font_size_slider.value())

    def get_volume_value(self):
        return self.speech_volume_slider.value() / 100.0

    def _announce_voice_trigger_current(self):
        if not getattr(self, "_allow_voice_trigger_announce", False):
            return
        try:
            idx = self.voice_trigger_combo.currentIndex()
        except Exception:
            return
        if idx < 0:
            return
        self._speak(f"{t('settings.voice_trigger.label')} {self.voice_trigger_combo.itemText(idx)}")

    def tabHandler(self, arrow=None):
        print("tab")
        if arrow == "down":
            self.currentfocus -= 1
            if self.currentfocus < 0:
                self.currentfocus = len(self.setting_layout) - 1
        else:
            self.currentfocus += 1
            if self.currentfocus > len(self.setting_layout) - 1:
                self.currentfocus = 0
            self.setting_layout[self.currentfocus].setFocus()
        intro = self.setting_layout[self.currentfocus].accessibleDescription()
        self._speak(intro)
        if self.setting_layout[self.currentfocus] is self.voice_trigger_combo:
            self._allow_voice_trigger_announce = True
            self._announce_voice_trigger_current()
