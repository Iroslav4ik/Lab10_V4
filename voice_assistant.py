import os
import json
import random
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer


class VoiceAssistant:
    def __init__(self):
        # Инициализация синтезатора речи
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Скорость речи

        # Инициализация модели Vosk
        self.model_path = "model/vosk-model-small-ru-0.22"
        if not os.path.exists(self.model_path):
            raise ValueError(f"Модель {self.model_path} не найдена!")
        self.model = Model(self.model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)

        # Настройка микрофона
        self.mic = pyaudio.PyAudio()
        self.stream = None

        # API Центробанка РФ
        self.currency_api = "https://www.cbr-xml-daily.ru/daily_json.js"
        self.rates = []

    def speak(self, text):
        """Озвучивание текста"""
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Прослушивание команды"""
        try:
            self.stream = self.mic.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192,
                input_device_index=0
            )
            self.stream.start_stream()

            print("Слушаю...")
            while True:
                data = self.stream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    command = result.get('text', '').lower()
                    print(f"Распознано: {command}")
                    return command
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            return ""
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def get_currency_rate(self, currency_code):
        """Получение курса валюты по коду (USD, EUR и т.д.)"""
        try:
            response = requests.get(self.currency_api, timeout=5)
            response.raise_for_status()
            data = response.json()

            if currency_code in data['Valute']:
                rate = data['Valute'][currency_code]['Value']
                self.rates.append((currency_code, rate))
                return f"Курс рубля к {currency_code}: {1 / rate:.4f}"
            return "Валюта не найдена"

        except requests.exceptions.RequestException as e:
            return f"Ошибка сети: {str(e)}"
        except json.JSONDecodeError:
            return "Ошибка: Некорректные данные"
        except KeyError:
            return "Ошибка: Неверный формат данных"

    def save_to_file(self):
        """Сохранение курсов в файл"""
        try:
            with open('rates.txt', 'w') as f:
                for code, rate in self.rates:
                    f.write(f"{code}: {1 / rate:.4f}\n")
            return "Данные сохранены"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def random_currency(self):
        """Случайная валюта"""
        try:
            response = requests.get(self.currency_api)
            data = response.json()
            currencies = list(data['Valute'].keys())
            random_code = random.choice(currencies)
            rate = data['Valute'][random_code]['Value']
            return f"Случайная валюта {random_code}: {1 / rate:.4f}"
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def run(self):
        """Основной цикл работы"""
        self.speak("Добрый день! Я ваш валютный ассистент.")
        try:
            while True:
                command = self.listen()
                if not command:
                    self.speak("Не расслышала, повторите")
                    continue

                # Обработка команд
                if any(word in command for word in ["доллар", "доллара"]):
                    result = self.get_currency_rate("USD")
                elif any(word in command for word in ["евро", "евра"]):
                    result = self.get_currency_rate("EUR")
                elif "сохранить" in command:
                    result = self.save_to_file()
                elif "случайный" in command:
                    result = self.random_currency()
                elif "стоп" in command:
                    self.speak("До свидания!")
                    break
                else:
                    result = "Команда не распознана"

                print("Результат:", result)
                self.speak(result)
        except KeyboardInterrupt:
            self.speak("Работа завершена")
        finally:
            self.mic.terminate()


if __name__ == "__main__":
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")