import pyttsx3
import threading
import queue
import time
import winsound
import os
import re

## Text-to-speech engine that run in another thread
class TTSThread(threading.Thread):

    ##auto start and loop until application close
    def __init__(self):
        threading.Thread.__init__(self)
        self.importance = False
        self.queue = queue.Queue()
        self.daemon = True
        self.rate = 200  #setting interval 100 to 300
        self.volume = 0.7
        self.tts_engine = pyttsx3.init("sapi5")    ## sapi5 for Windows, nsss for Mac, espeak for others
        self.tts_engine.setProperty("rate", self.rate)
        self.tts_engine.setProperty("volume", self.volume)

        self.default_voice_id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"
        self.voice_language_map = {
            "en": ["en-us", "en_us", "en-gb", "en_gb", "english"],
            "zh-CN": ["zh-cn", "zh_cn", "cmn", "mandarin", "hanyu", "chinese"],
            "zh-TW": ["zh-hk", "zh_hk", "yue", "cantonese", "hongkong"],
        }

        self._voices = []
        try:
            self._voices = self.tts_engine.getProperty("voices") or []
        except Exception:
            self._voices = []

        self.current_language = "en"
        self.update_language("en")

        self.tts_engine.startLoop(False)
        self.start()

    def run(self):
        print("TTS running")
        self.tts_engine.iterate()
        t_running = True
        while t_running:
            try:
                data = self.queue.get_nowait()
            except queue.Empty:
                self.tts_engine.iterate()
                time.sleep(0.02)
                continue

            self.tts_engine.stop()
            self.tts_engine.say(data[0])
            self.tts_engine.iterate()

            ##when the message's important flag = true -> can not be interrupt
            if data[1] == True:
                time.sleep(2)

        self.tts_engine.endLoop()

    def setRateValue(self, rate):
        self.rate = rate
        self.tts_engine.setProperty("rate", rate)

    def getRateValue(self):
        return self.rate

    def setVolumeValue(self, volume):
        self.volume = volume
        self.tts_engine.setProperty("volume", volume)

    def getVolumeValue(self):
        return self.volume

    def _normalize_lang(self, lang: str) -> str:
        value = str(lang or "en").strip().lower()
        if value in ["zh-tw", "zh_hk", "zh-hk", "zh_tw", "tw", "hk", "yue"]:
            return "zh-TW"
        if value in ["zh-cn", "zh_cn", "cn", "cmn", "zh"]:
            return "zh-CN"
        return "en"

    def _voice_matches_lang(self, voice, lang_key: str) -> bool:
        hints = [h.lower() for h in self.voice_language_map.get(lang_key, [])]

        tokens = []
        try:
            tokens.append(str(getattr(voice, "id", "")))
            tokens.append(str(getattr(voice, "name", "")))
        except Exception:
            pass

        try:
            langs = getattr(voice, "languages", []) or []
            for raw_lang in langs:
                try:
                    if isinstance(raw_lang, bytes):
                        decoded = raw_lang.decode("utf-8", errors="ignore")
                    else:
                        decoded = str(raw_lang)
                except Exception:
                    decoded = str(raw_lang)
                decoded = re.sub(r"[^a-zA-Z\-_]", "", decoded)
                if decoded:
                    tokens.append(decoded)
        except Exception:
            pass

        search_space = " ".join(tokens).lower()
        return any(h in search_space for h in hints)

    def _pick_voice_id_for_lang(self, lang_key: str):
        # first pass: strict mapping
        for voice in self._voices:
            if self._voice_matches_lang(voice, lang_key):
                return getattr(voice, "id", None)

        # fallback by major language
        if lang_key.startswith("zh"):
            for voice in self._voices:
                if self._voice_matches_lang(voice, "zh-CN") or self._voice_matches_lang(voice, "zh-TW"):
                    return getattr(voice, "id", None)

        if lang_key == "en":
            for voice in self._voices:
                if self._voice_matches_lang(voice, "en"):
                    return getattr(voice, "id", None)

        return self.default_voice_id

    def update_language(self, lang: str):
        normalized_lang = self._normalize_lang(lang)
        self.current_language = normalized_lang

        voice_id = self._pick_voice_id_for_lang(normalized_lang)
        if not voice_id:
            return False

        try:
            self.tts_engine.setProperty("voice", voice_id)
            return True
        except Exception as e:
            print(f"Failed to set TTS voice for {normalized_lang}: {e}")
            return False

    def interrupt_now(self, clear_queue=True):
        """Immediately stop current TTS and optionally clear queued speeches."""
        try:
            self.tts_engine.stop()
        except Exception:
            pass

        # Also stop any async wav that may still be playing
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

        if clear_queue:
            try:
                while True:
                    self.queue.get_nowait()
            except queue.Empty:
                pass

    def play_sound(self, sound_file):
        """Play a .wav sound file asynchronously"""
        try:
            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Error playing sound {sound_file}: {e}")
