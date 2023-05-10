import argparse
import io
import os
import speech_recognition as sr
import whisper
import torch
import math
import sys
import ctypes
import shutil
import numpy as np
import requests
import json
import re
try:
    import pytz
except:
    print("Installing missing dependencies...")
    os.system("pip install pytz")
    try:
        import pytz
    except:
        print("Failed to install pytz. Please install it manually.")
        print("Use the command: pip install pytz")
        exit()
try:
    import pyaudio
except:
    print("Installing missing dependencies...")
    os.system("pip install pyaudio")
    try:
        import pyaudio
    except:
        print("Failed to install pyaudio. Please install it manually.")
        print("Use the command: pip install pyaudio")
        exit()
try:
    import humanize
except:
    print("Installing missing dependencies...")
    os.system("pip install humanize")
    try:
        import humanize
    except:
        print("Failed to install humanize. Please install it manually.")
        print("Use the command: pip install humanize")
        exit()


from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform
from colorama import Fore, Back, Style, init
from tqdm import tqdm
from datetime import datetime
from numba import cuda
from prettytable import PrettyTable
try:
    from dateutil.tz import tzlocal
except:
    print("Installing missing dependencies...")
    os.system("pip install python-dateutil")
    try:
        from dateutil.tz import tzlocal
    except:
        print("Failed to install python-dateutil. Please install it manually.")
        print("Use the command: pip install python-dateutil")
        exit()
try:
    from tzlocal import get_localzone
except:
    print("Installing missing dependencies...")
    os.system("pip install tzlocal")
    try:
        from tzlocal import get_localzone
    except:
        print("Failed to install tzlocal. Please install it manually.")
        print("Use the command: pip install tzlocal")
        exit()
init()

try:
    cuda_available = torch.cuda.is_available()
except:
    cuda_available = False

# Code is semi documented, but if you have any questions, feel free to ask in the Discussions tab.

def main():

    version = "1.0.994"
    ScriptCreator = "cyberofficial"
    GitHubRepo = "https://github.com/cyberofficial/Real-Time-Synthalingua"
    repo_owner = "cyberofficial"
    repo_name = "Synthalingua"

    def get_remote_version(repo_owner, repo_name, file_path):
        url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/master/{file_path}"
        response = requests.get(url)

        if response.status_code == 200:
            remote_file_content = response.text
            version_search = re.search(r'version\s*=\s*"([\d.]+)"', remote_file_content)
            if version_search:
                remote_version = version_search.group(1)
                return remote_version
            else:
                print("Error: Version not found in the remote file.")
                return None
        else:
            print(f"An error occurred. Status code: {response.status_code}")
            return None

    def check_for_updates():
        local_version = version
        remote_version = get_remote_version(repo_owner, repo_name, "transcribe_audio.py")

        if remote_version is not None:
            if remote_version != local_version:
                print(f"Version mismatch. Local version: {local_version}, remote version: {remote_version}")
                print("Consider updating to the latest version.")
                print(f"Update available at: " + GitHubRepo)
            else:
                print("You are already using the latest version.")
                print(f"Current version: {local_version}")

    check_for_updates()

    def fine_tune_model_dl():
        print("Downloading fine-tuned model... [Via OneDrive (Public)]")
        url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21455917&authkey=AH9uvngPhJlVOg4"
        r = requests.get(url, stream=True)
        total_length = int(r.headers.get('content-length'))
        with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            with open("models/fine_tuned_model.pt", "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(1024)
        print("Fine-tuned model downloaded.")

    def fine_tune_model_dl_compressed():
        print("Downloading fine-tuned compressed model... [Via OneDrive (Public)]")
        url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21455918&authkey=AGS9Zh8NuEo6qn4"
        r = requests.get(url, stream=True)
        total_length = int(r.headers.get('content-length'))
        with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            with open("models/fine_tuned_model_compressed.pt", "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(1024)
        print("Fine-tuned model (compressed) downloaded.")

    def record_callback(_, audio:sr.AudioData) -> None:
        data = audio.get_raw_data()
        data_queue.put(data)

    def set_window_title(detected_language, confidence):
        title = f"Model: {model} - {detected_language} [{confidence:.2f}%]"

        if sys.platform == "win32":
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        else:
            sys.stdout.write(f"\x1b]2;{title}\x1b\x5c")
            sys.stdout.flush()

    def send_to_discord_webhook(webhook_url, text):
        data = {
            "content": text
        }
        headers = {
            "Content-Type": "application/json"
        }
        try:
            if len(text) > 1800:
                for i in range(0, len(text), 1800):
                    data["content"] = text[i:i+1800]
                    response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
                    if response.status_code == 429:
                        print("Discord webhook is being rate limited.")
            else:
                response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
                if response.status_code == 429:
                    print("Discord webhook is being rate limited.")
        except:
            print("Failed to send message to Discord webhook.")
            pass

    def is_input_device(device_index):
        pa = pyaudio.PyAudio()
        device_info = pa.get_device_info_by_index(device_index)
        return device_info['maxInputChannels'] > 0

    def get_microphone_source(args):
        pa = pyaudio.PyAudio()
        available_mics = sr.Microphone.list_microphone_names()

        def is_input_device(device_index):
            device_info = pa.get_device_info_by_index(device_index)
            return device_info['maxInputChannels'] > 0

        if args.set_microphone:
            mic_name = args.set_microphone

            if mic_name.isdigit():
                mic_index = int(mic_name)
                if mic_index in range(len(available_mics)) and is_input_device(mic_index):
                    return sr.Microphone(sample_rate=16000, device_index=mic_index), available_mics[mic_index]
                else:
                    print("Invalid audio source. Please choose a valid microphone.")
                    sys.exit(0)
            else:
                for index, name in enumerate(available_mics):
                    if mic_name == name and is_input_device(index):
                        return sr.Microphone(sample_rate=16000, device_index=index), name

        for index in range(pa.get_device_count()):
            if is_input_device(index):
                return sr.Microphone(sample_rate=16000, device_index=index), "system default"

        raise ValueError("No valid input devices found.")

    def set_model_by_ram(ram, language):
        ram = ram.lower()

        if ram == "1gb":
            model = "tiny"
        elif ram == "2gb":
            model = "base"
        elif ram == "4gb":
            model = "small"
        elif ram == "6gb":
            model = "medium"
        elif ram == "12gb":
            model = "large"
            if language == "en":
                red_text = Fore.RED + Back.BLACK
                green_text = Fore.GREEN + Back.BLACK
                yellow_text = Fore.YELLOW + Back.BLACK
                reset_text = Style.RESET_ALL
                print(f"{red_text}WARNING{reset_text}: {yellow_text}12gb{reset_text} is overkill for English. Do you want to swap to {green_text}6gb{reset_text} model?")
                if input("y/n: ").lower() == "y":
                    model = "medium"
                else:
                    model = "large"
        else:
            raise ValueError("Invalid RAM setting provided")

        return model
        

    parser = argparse.ArgumentParser()
    parser.add_argument("--ram", default="4gb", help="Model to use",
                        choices=["1gb", "2gb", "4gb", "6gb", "12gb"])
    parser.add_argument("--ramforce", action='store_true',
                        help="Force the model to use the RAM setting provided. Warning: This may cause the model to crash.")
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=100,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=1,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=1,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)  
    parser.add_argument("--translate", action='store_true',
                        help="Translate the transcriptions to English.")
    parser.add_argument("--language",
                        help="Language to translate from.", type=str,
                        choices=["af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"])
    parser.add_argument("--auto_model_swap", action='store_true',
                        help="Automatically swap model based on detected language.")
    parser.add_argument("--device", default="cuda",
                        help="Device to use for model. If not specified, will use CUDA if available. Available options: cpu, cuda")
    parser.add_argument("--cuda_device", default=0,
                        help="CUDA device to use for model. If not specified, will use CUDA device 0.", type=int)
    parser.add_argument("--discord_webhook", default=None,
                        help="Discord webhook to send transcription to.", type=str)
    parser.add_argument("--list_microphones", action='store_true',
                        help="List available microphones and exit.")
    parser.add_argument("--set_microphone", default=None,
                        help="Set default microphone to use.", type=str)
    parser.add_argument("--auto_language_lock", action='store_true',
                        help="Automatically locks the language based on the detected language after set ammount of transcriptions.")
    parser.add_argument("--retry", action='store_true',
                        help="Retries the transcription if it fails. May increase output time.")
    parser.add_argument("--use_finetune", action='store_true',
                        help="Use finetuned model.")
    parser.add_argument("--about", action='store_true',
                        help="About the project.")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.about:
        print(f"\033[4m{Fore.GREEN}About the project:{Style.RESET_ALL}\033[0m")
        print(f"This project was created by \033[4m{Fore.GREEN}{ScriptCreator}{Style.RESET_ALL}\033[0m and is licensed under the \033[4m{Fore.GREEN}GPLv3{Style.RESET_ALL}\033[0m license.\n\nYou can find the source code at \033[4m{Fore.GREEN}{GitHubRepo}{Style.RESET_ALL}\033[0m.\nBased on Whisper from OpenAI at \033[4m{Fore.GREEN}https://github.com/openai/whisper{Style.RESET_ALL}\033[0m.\n\n\n\n")
        # contributors #
        print(f"\033[4m{Fore.GREEN}Contributors:{Style.RESET_ALL}\033[0m")
        print("@DaniruKun from https://watsonindustries.live")
        exit()

    model = set_model_by_ram(args.ram, args.language)

    hardmodel = None

    if args.ramforce:
        hardmodel = args.ram

    phrase_time = None
    last_sample = bytes()
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False
    
    valid_languages = ["af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"]

    if args.language:
        if args.language not in valid_languages:
            print("Invalid language. Please choose a valid language from the list below:")
            print(valid_languages)
            return
    
    if args.phrase_timeout > 1 and args.discord_webhook:
        red_text = Fore.RED + Back.BLACK
        print(f"{red_text}WARNING{reset_text}: phrase_timeout is set to {args.phrase_timeout} seconds. This will cause the webhook to send multiple messages. Setting phrase_timeout to 1 second to avoid this.")
        args.phrase_timeout = 1
        
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "cuda" and not torch.cuda.is_available():
            print("WARNING: CUDA was chosen but it is not available. Falling back to CPU.")
    print(f"Using device: {device}")

    if device.type == "cuda":
        # Check if multiple CUDA devices are available
        cuda_device_count = torch.cuda.device_count()
        if cuda_device_count > 1 and args.cuda_device == 0:
            while True:
                print("Multiple CUDA devices detected. Please choose a device:")
                for i in range(cuda_device_count):
                    print(f"{i}: {torch.cuda.get_device_name(i)}, VRAM: {torch.cuda.get_device_properties(i).total_memory / 1024 / 1024} MB")
                try:
                    selected_device = int(input("Enter the device number: "))
                    if 0 <= selected_device < cuda_device_count:
                        break
                    else:
                        print("Invalid device number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a valid device number.")
        else:
            selected_device = args.cuda_device

        torch.cuda.set_device(selected_device)
        print(f"CUDA device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
        print(f"VRAM available: {torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / 1024 / 1024} MB")

 
    if args.list_microphones:
        print("Available microphone devices are: ")
        mic_table = PrettyTable()
        mic_table.field_names = ["Index", "Microphone Name"]

        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if is_input_device(index):
                mic_table.add_row([index, name])

        print(mic_table)
        sys.exit(0)

    try:
        source, mic_name = get_microphone_source(args)
    except ValueError as e:
        print(e)
        sys.exit(0)

    with source as s:
        try:
            recorder.adjust_for_ambient_noise(s)
            print(f"Microphone set to: {mic_name}")
        except AssertionError as e:
            print(e)

    if args.language == "en" or args.language == "English":
        model += ".en"
        if model == "large" or model == "large.en":
            model = "large"

    if not os.path.exists("models"):
        print("Creating models folder...")
        os.makedirs("models")

    def print_warning(old_ram_flag, new_ram_flag, needed_vram, detected_vram):
        print(f"WARNING: CUDA was chosen, but the VRAM available is less than {old_ram_flag}. You have {detected_vram:.2f} MB available, and {needed_vram - detected_vram:.2f} MB additional overhead is needed. Setting ram flag to avoid out of memory errors. New Flag: {new_ram_flag}")
        print(f"Remember that the system will use VRAM for other processes, so you may need to lower the ram flag even more to avoid out of memory errors.")

    if device.type == "cuda":
        cuda_vram = torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / 1024 / 1024
        overhead_buffer = 200

        ram_options = [("12gb", 12000), ("6gb", 6144), ("4gb", 4096), ("2gb", 2048), ("1gb", 1024)]

        found = False
        old_ram_flag = args.ram
        for i, (ram_option, required_vram) in enumerate(ram_options):
            if args.ram == ram_option and cuda_vram < required_vram + overhead_buffer:
                if i + 1 < len(ram_options):
                    args.ram = ram_options[i + 1][0]
                else:
                    args.ram = ram_option
                    device = torch.device("cpu")
                    print("WARNING: CUDA was chosen, but the VRAM available is less than 1 GB. Falling back to CPU.")
                    break
            else:
                found = True
                break

        if not found:
            device = torch.device("cpu")
            print("WARNING: No suitable RAM setting was found. Falling back to CPU.")
        elif old_ram_flag != args.ram:
            print_warning(old_ram_flag, args.ram, required_vram + overhead_buffer, cuda_vram)

    print("Now using ram flag: " + args.ram)

    if args.ram == "1gb" or args.ram == "2gb" or args.ram == "4gb":
        red_text = Style.BRIGHT + Fore.RED
        reset_text = Style.RESET_ALL
        if not os.path.exists("models/fine_tuned_model_compressed.pt"):
            print("Warning - Since you have chosen a low amount of RAM, the fine-tuned model will be downloaded in a compressed format.\nThis will result in a some what faster startup time and a slower inference time, but will also result in slight reduction in accuracy.")
            print("Compressed Fine-tuned model not found. Downloading Compressed fine-tuned model... [Via OneDrive (Public)]")
            fine_tune_model_dl_compressed()
            try:
                if args.use_finetune == True:
                    whisper.load_model("models/fine_tuned_model_compressed.pt", device=device, download_root="models")
                    print("Fine-tuned model loaded into memory.")
                    if device.type == "cuda":
                        max_split_size_mb = 128
            except Exception as e:
                print("Failed to load fine-tuned model. Results may be inaccurate. If you experience issues, please delete the fine-tuned model from the models folder and restart the program. If you still experience issues, please open an issue on GitHub.")
                red_text = Fore.RED + Back.BLACK
                print(f"{red_text}Error: {e}{reset_text}")
                pass
        else:
            try:
                if args.use_finetune == True:
                    whisper.load_model("models/fine_tuned_model_compressed.pt", device=device, download_root="models")
                    print("Fine-tuned model loaded into memory.")
                    if device.type == "cuda":
                        max_split_size_mb = 128
            except Exception as e:
                print("Failed to load fine-tuned model. Results may be inaccurate. If you experience issues, please delete the fine-tuned model from the models folder and restart the program. If you still experience issues, please open an issue on GitHub.")
                red_text = Fore.RED + Back.BLACK
                print(f"{red_text}Error: {e}{reset_text}")
                pass
    else:
        if not os.path.exists("models/fine_tuned_model.pt"):
            print("Fine-tuned model not found. Downloading Fine-tuned model... [Via OneDrive (Public)]")
            fine_tune_model_dl()
            try:
                if args.use_finetune == True:
                    whisper.load_model("models/fine_tuned_model.pt", device=device, download_root="models")
                    print("Fine-tuned model loaded into memory.")
                    if device.type == "cuda":
                        max_split_size_mb = 128
            except Exception as e:
                print("Failed to load fine-tuned model. Results may be inaccurate. If you experience issues, please delete the fine-tuned model from the models folder and restart the program. If you still experience issues, please open an issue on GitHub.")
                red_text = Fore.RED + Back.BLACK
                print(f"{red_text}Error: {e}{reset_text}")
                pass
        else:
            try:
                if args.use_finetune == True:
                    whisper.load_model("models/fine_tuned_model.pt", device=device, download_root="models")
                    print("Fine-tuned model loaded into memory.")
            except Exception as e:
                print("Failed to load fine-tuned model. Results may be inaccurate. If you experience issues, please delete the fine-tuned model from the models folder and restart the program. If you still experience issues, please open an issue on GitHub.")
                red_text = Fore.RED + Back.BLACK
                print(f"{red_text}Error: {e}{reset_text}")
                pass

    if args.ramforce:
        print("Hardmodel parameter detected. Setting ram flag to hardmodel parameter.")
        args.ram = hardmodel


    model = set_model_by_ram(args.ram, args.language)
    print(f"Loading model {model}...")

    audio_model = whisper.load_model(model, device=device, download_root="models")

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    if not os.path.exists("temp"):
        os.makedirs("temp")
    temp_dir = "temp"
    temp_file = NamedTemporaryFile(dir=temp_dir, delete=True, suffix=".ts", prefix="rec_").name
    transcription = ['']
        
    if args.discord_webhook:
        webhook_url = args.discord_webhook
        print(f"Sending console output to Discord webhook that was set in parameters.")

    recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)
    
    print("Model loaded.\n")
    print(f"Using {model} model.")
    if args.non_english:
        print("Using the multi-lingual model.")

    if device.type == "cuda":
        if "AMD" in torch.cuda.get_device_name(torch.cuda.current_device()):
            print("WARNING: You are using an AMD GPU with CUDA. This may not work properly. If you experience issues, try using the CPU instead.")

    english_counter = 0
    language_counters = {}
    last_detected_language = None 

    if args.discord_webhook:
        if args.translate:
            send_to_discord_webhook(webhook_url, f"Transcription started. Translation enabled.\nUsing the {args.ram} ram model.")
        else:
            send_to_discord_webhook(webhook_url, f"Transcription started. Translation disabled.\nUsing the {args.ram} ram model.")
        sleep(0.25)

    if args.auto_language_lock:
        print("Auto language lock enabled. Will auto lock after 5 consecutive detections of the same language.")
        if args.discord_webhook:
            send_to_discord_webhook(webhook_url, "Auto language lock enabled. Will auto lock after 5 consecutive detections of the same language.")

    print("Awaiting audio stream...")

    while True:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                print("\nAudio stream detected...")
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                audio = whisper.load_audio(temp_file)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(device)
                if ".en" in model:
                    detected_language = "English"
                else:
                    _, language_probs = audio_model.detect_language(mel)
                    detected_language = max(language_probs, key=language_probs.get)

                if args.language:
                    detected_language = args.language
                    if args.auto_language_lock:
                        print(f"Language locked to {detected_language}")
                    else:
                        print(f"Language set by argument: {detected_language}")
                else:
                    if ".en" in model:
                        detected_language = "English"
                        print(f"Language set by model: {detected_language}")
                    else:
                        if args.auto_language_lock:
                            if last_detected_language == detected_language:
                                english_counter += 1
                                if english_counter >= 5:
                                    print(f"Language locked to {detected_language}")
                                    args.language = detected_language
                            else:
                                english_counter = 0
                                last_detected_language = detected_language
                        try:
                            confidence = language_probs[detected_language] * 100
                            confidence_color = Fore.GREEN if confidence > 75 else (Fore.YELLOW if confidence > 50 else Fore.RED)
                            set_window_title(detected_language, confidence)
                            print(f"Detected language: {detected_language} {confidence_color}({confidence:.2f}% Accuracy){Style.RESET_ALL}")
                        except:
                            pass
                print("Transcribing...")
                if device == "cuda":
                    result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                else:
                    result = audio_model.transcribe(temp_file)
                print(f"Detected Speech: {result['text']}")
                if result['text'] == "":
                    if args.retry:
                        print("Transcription failed, trying again...")
                        send_to_discord_webhook(webhook_url, "Transcription failed, trying again...")
                        if device == "cuda":
                            result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                        else:
                            result = audio_model.transcribe(temp_file)
                        print(f"Detected Speech: {result['text']}")
                    else:
                        print("Transcription failed, skipping...")
                if args.discord_webhook:
                    send_to_discord_webhook(webhook_url, f"Detected Speech: {result['text']}")
                text = result['text'].strip()
                
                if args.translate:
                    if detected_language != 'en':
                        print("Translating...")
                        if device == "cuda":
                            translated_result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available(), task="translate")
                        else:
                            translated_result = audio_model.transcribe(temp_file, task="translate")
                        translated_text = translated_result['text'].strip()
                        if translated_text == "":
                            if args.retry:
                                print("Translation failed, trying again...")
                                send_to_discord_webhook(webhook_url, "Translation failed, trying again...")
                                if device == "cuda":
                                    translated_result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available(), task="translate")
                                else:
                                    translated_result = audio_model.transcribe(temp_file, task="translate")
                            translated_text = translated_result['text'].strip()
                        if args.discord_webhook:
                            if translated_text == "":
                                send_to_discord_webhook(webhook_url, f"Translation failed")
                            else:
                                send_to_discord_webhook(webhook_url, f"Translated Speech: {translated_text}")

                    else:
                        translated_text = ""
                        if args.discord_webhook:
                            send_to_discord_webhook(webhook_url, "Translation failed")
                
                if args.discord_webhook:
                    message = "----------------"
                    send_to_discord_webhook(webhook_url, message)
                    


                if phrase_complete:
                    transcription.append((text, translated_text if args.translate else None, detected_language))
                else:
                    transcription[-1] = (text, translated_text if args.translate else None, detected_language)

                os.system('cls' if os.name=='nt' else 'clear')
                for original_text, translated_text, language_code in transcription:
                    if not original_text:
                        continue
                    print("=" * shutil.get_terminal_size().columns)
                    print(f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)} Detected - {language_code} {' ' * int((shutil.get_terminal_size().columns - 15) / 2)}")
                    print(f"{original_text}")



                    if language_code == 'en':
                        print('', end='', flush=True)
                    else:
                        if translated_text:
                            print(f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)} Translation {'-' * int((shutil.get_terminal_size().columns - 15) / 2)}")
                            print(f"{translated_text}\n")
                print('', end='', flush=True)

                if args.auto_model_swap:
                    if last_detected_language != detected_language:
                        last_detected_language = detected_language
                        language_counters[detected_language] = 1
                    else:
                        language_counters[detected_language] += 1

                    if language_counters[detected_language] == 5:
                        if detected_language == 'en' and model != 'base':
                            print("Detected English 5 times in a row, changing model to base.")
                            model = 'base'
                            audio_model = whisper.load_model(model, device=device)
                            print("Model was changed to base since English was detected 5 times in a row.")
                        elif detected_language != 'en' and model != 'large':
                            print(f"Detected {detected_language} 5 times in a row, changing model to large.")
                            model = 'large'
                            audio_model = whisper.load_model(model, device=device)
                            print(f"Model was changed to large since {detected_language} was detected 5 times in a row.")
                # Keeping sleep disabled for now will add a flag to enable it later to prevent spamming the API
                # Just here as a reminder
                # sleep(0.25)
        except Exception as e:
            if not isinstance(e, KeyboardInterrupt):
                print(e)
                if os.path.isfile('error_report.txt'):
                    error_report_file = open('error_report.txt', 'a')
                else:
                    error_report_file = open('error_report.txt', 'w')
                error_report_file.write(str(e))
                error_report_file.close()
            pass

        except KeyboardInterrupt:
            print("Exiting...")
            if args.discord_webhook:
                send_to_discord_webhook(webhook_url, "Service has stopped.")
            break

    if not os.path.isdir('out'):
        os.mkdir('out')
    

    if os.path.isfile('out\\transcription.txt'):
        print('out\\transcription.txt already exists, changing the name to transcription_1.txt')
        i = 1
        while os.path.isfile('out\\transcription_' + str(i) + '.txt'):
            i += 1
        transcription_file = open('out\\transcription_' + str(i) + '.txt', 'w', encoding='utf-8')
    else:
        transcription_file = open('out\\transcription.txt', 'w', encoding='utf-8')

    for original_text, translated_text, language_code in transcription:
        transcription_file.write(f"Original ({language_code}): {original_text}\n")
        if translated_text:
            transcription_file.write(f"Translation: {translated_text}\n")
    transcription_file.close()
    print(f"Transcription was saved to out\\transcription{'_' + str(i) if i > 0 else ''}.txt")
    

if __name__ == "__main__":
    main()