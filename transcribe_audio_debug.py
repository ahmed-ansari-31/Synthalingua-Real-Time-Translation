try:
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
    try:
        import pytz
    except:
        # install pytz if it's not installed
        os.system("pip install pytz")
        try:
            import pytz
        except:
            print("Failed to install pytz. Please install it manually.")
            print("Use the command: pip install pytz")
            exit()
except:
    print("Error Code: 1")
    print("Failed to import required modules.")
    sys.exit()

try:
    from datetime import datetime, timedelta
    from queue import Queue
    from tempfile import NamedTemporaryFile
    from time import sleep
    from sys import platform
    from colorama import Fore, Back, Style, init
    from tqdm import tqdm
    from datetime import datetime
    try:
        from dateutil.tz import tzlocal
    except:
        # install dateutil if it's not installed
        os.system("pip install python-dateutil")
        try:
            from dateutil.tz import tzlocal
        except:
            print("Failed to install python-dateutil. Please install it manually.")
            print("Use the command: pip install python-dateutil")
            exit()
except:
    print("Error Code: 2")
    print("Failed to import required modules.")
    sys.exit()

try:
    init()
except:
    print("Error Code: 3")
    print("Failed to initialize colorama.")
    sys.exit()

try:
    try:
        cuda_available = torch.cuda.is_available()
    except:
        cuda_available = False
except:
    print("Error Code: 4")
    print("Failed to check if CUDA is available.")
    sys.exit()

# Code is semi documented, but if you have any questions, feel free to ask in the Discussions tab.

def main():

    version = "1.0.0"
    ScriptCreator = "cyberofficial"
    GitHubRepo = "https://github.com/cyberofficial/Real-Time-Translation"
    repo_owner = "cyberofficial"
    repo_name = "Real-Time-Translation"

    def get_last_updated(repo_owner, repo_name):
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
            response = requests.get(url)
            repo_data = response.json()

            if response.status_code == 200:
                last_updated = repo_data["updated_at"]
                last_updated_dt = datetime.fromisoformat(last_updated.strip("Z"))

                # Convert to the user's local timezone
                utc_timezone = pytz.timezone("UTC")
                local_timezone = tzlocal()
                last_updated_local = last_updated_dt.replace(tzinfo=utc_timezone).astimezone(local_timezone)

                print(f"The repository {repo_owner}/{repo_name} was last updated on {last_updated_local}.")
            else:
                print(f"An error occurred. Status code: {response.status_code}")
        except:
            print("Error Code: 5")
            print("Failed to get last updated date.")
            sys.exit()
    try:
        print(f"Laster updated: {get_last_updated(repo_owner, repo_name)}")
    except:
        print("Error Code: 6")
        print("Failed to get last updated date.")
        sys.exit()

    def fine_tune_model_dl():
        try:
            # download the fine-tuned model
            print("Downloading fine-tuned model... [Via OneDrive (Public)]")
            url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21455917&authkey=AH9uvngPhJlVOg4"
            # show progress bar as the file is being downloaded
            r = requests.get(url, stream=True)
            total_length = int(r.headers.get('content-length'))
            with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                with open("models/fine_tuned_model.pt", "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            pbar.update(1024)
            print("Fine-tuned model downloaded.")
        except:
            print("Error Code: 7")
            print("Failed to download fine-tuned model.")
            sys.exit()

    def record_callback(_, audio:sr.AudioData) -> None:
        try:
            data = audio.get_raw_data()
            data_queue.put(data)
        except:
            print("Error Code: 8")
            print("Failed to record audio.")
            sys.exit()

    def set_window_title(detected_language, confidence):
        try:
            title = f"Model: {model} - {detected_language} [{confidence:.2f}%]"

            if sys.platform == "win32":
                ctypes.windll.kernel32.SetConsoleTitleW(title)
            else:
                sys.stdout.write(f"\x1b]2;{title}\x1b\x5c")
                sys.stdout.flush()
        except:
            print("Error Code: 9")
            print("Failed to set window title.")
            sys.exit()

    def send_to_discord_webhook(webhook_url, text):
        try:
            data = {
                "content": text
            }
            headers = {
                "Content-Type": "application/json"
            }
            try:
                # if text is longer than 2000 characters, then split it into multiple messages
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
        except:
            print("Error Code: 10")
            print("Failed to send message to Discord webhook.")
            sys.exit()

    parser = argparse.ArgumentParser()
#    parser.add_argument("--model", default="medium", help="Model to use",
#                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--ram", default="4gb", help="Model to use",
                        choices=["1gb", "2gb", "4gb", "6gb", "12gb"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=100,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
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
    parser.add_argument("--about", action='store_true',
                        help="About the project.")
    args = parser.parse_args()

    # if no arguments are given, print help
    try:
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)
    except:
        print("Error Code 11: Error while parsing arguments.")
        sys.exit(1)

    try:
        if args.about:
            print(f"\033[4m{Fore.GREEN}About the project:{Style.RESET_ALL}\033[0m")
            print(f"This project was created by \033[4m{Fore.GREEN}{ScriptCreator}{Style.RESET_ALL}\033[0m and is licensed under the \033[4m{Fore.GREEN}GPLv3{Style.RESET_ALL}\033[0m license.\n\nYou can find the source code at \033[4m{Fore.GREEN}{GitHubRepo}{Style.RESET_ALL}\033[0m.\nBased on Whisper from OpenAI at \033[4m{Fore.GREEN}https://github.com/openai/whisper{Style.RESET_ALL}\033[0m.\n\n\n\n")
            # contributors
            print(f"\033[4m{Fore.GREEN}Contributors:{Style.RESET_ALL}\033[0m")
            print("None yet. If you want to be a contributor, then just make a pull request on GitHub and make some changes to the code that are useful/helpful.")
            exit()
    except:
        print("Error Code 12: Error while printing about section.")
        sys.exit(1)

    try:
        if args.ram == "1gb":
            model = "tiny"
        elif args.ram == "2gb":
            model = "base"
        elif args.ram == "4gb":
            model = "small"
        elif args.ram == "6gb":
            model = "medium"
        elif args.ram == "12gb":
            model = "large"
            if args.language == "en":
                red_text = Fore.RED + Back.BLACK
                green_text = Fore.GREEN + Back.BLACK
                yellow_text = Fore.YELLOW + Back.BLACK
                reset_text = Style.RESET_ALL
                print(f"{red_text}WARNING{reset_text}: {yellow_text}12gb{reset_text} is overkill for English. Do you want swap to {green_text}6gb{reset_text} model?")          
                if input("y/n: ").lower() == "y":
                    model = "medium"
                else:
                    model = "large"
    except:
        print("Error Code 13: Error while setting model.")
        sys.exit(1)

    try:
        phrase_time = None
        last_sample = bytes()
        data_queue = Queue()
        recorder = sr.Recognizer()
        recorder.energy_threshold = args.energy_threshold
        recorder.dynamic_energy_threshold = False
    except:
        print("Error Code 14: Error while setting up speech recognition.")
        sys.exit(1)
        
    # create a dictionary of valid languages
    valid_languages = ["af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"]

    try:
        # check language for valid language
        if args.language:
            if args.language not in valid_languages:
                print("Invalid language. Please choose a valid language from the list below:")
                print(valid_languages)
                return
    except:
        print("Error Code 15: Error while checking language.")
        sys.exit(1)
    
    try:
    # if phrase_timeout is greater than 1 and discord webhook is set, tell the user the phrase_timeout will be set to 1 to avoid repeated messages
        if args.phrase_timeout > 1 and args.discord_webhook:
            red_text = Fore.RED + Back.BLACK
            print(f"{red_text}WARNING{reset_text}: phrase_timeout is set to {args.phrase_timeout} seconds. This will cause the webhook to send multiple messages. Setting phrase_timeout to 1 second to avoid this.")
            args.phrase_timeout = 1
            
        if args.device:
            device = torch.device(args.device)
        else:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # if cuda was chosen and it's not available, fall back to cpu
            if args.device == "cuda" and not torch.cuda.is_available():
                print("WARNING: CUDA was chosen but it is not available. Falling back to CPU.")
        print(f"Using device: {device}")
    except:
        print("Error Code 16: Error while setting device.")
        sys.exit(1)

    try:
    # if cuda was chosen then set device number to use
        if device.type == "cuda":
            torch.cuda.set_device(args.cuda_device)
            print(f"CUDA device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
            print(f"VRAM available: {torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / 1024 / 1024} MB")
    except:
        print("Error Code 17: Error while setting CUDA device.")
        sys.exit(1)

    try:
        # list all microphones that are available then set the source to desired microphone
        if args.list_microphones:
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found, the device index is {index}")
                # exit program
            sys.exit(0)
    except:
        print("Error Code 18: Error while listing microphones.")
        sys.exit(1)


    try:
        if args.set_microphone:
            mic_name = args.set_microphone

            # if the microphone arg is set to a number, then set the source to the microphone with that index number if it exists
            if mic_name.isdigit():
                if int(mic_name) in range(len(sr.Microphone.list_microphone_names())):
                    source = sr.Microphone(sample_rate=16000, device_index=int(mic_name))
                    print(f"Microphone set to: {sr.Microphone.list_microphone_names()[int(mic_name)]}")
                else:
                    print("Microphone not found. Please choose a valid microphone.")
                    # exit program
                    sys.exit(0)
            else:
                # if the microphone arg is set to a string, then set the source to the microphone with that name if it exists
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    if mic_name == name:
                        source = sr.Microphone(sample_rate=16000, device_index=index)
                        print(f"Microphone set to: {name}")
                        break
                else:
                    print("Microphone not found. Please choose a valid microphone.")
                    # exit program
                    sys.exit(0)
        else:
            source = sr.Microphone(sample_rate=16000)
            print(f"Microphone set to system default.")
    except:
        print("Error Code 19: Error while setting microphone.")
        sys.exit(1)
        
    try:
        # if the language is set to english, then add .en to the model name
        if args.language == "en" or args.language == "English":
            model += ".en"
            # if the large model is chosen, then remove the .en from the model name
            if model == "large" or model == "large.en":
                model = "large"
    except:
        print("Error Code 20: Error while setting language.")
        sys.exit(1)

    try:
        # download the fine-tuned model if it doesn't exist
        if not os.path.exists("models"):
            print("Creating models folder...")
            os.makedirs("models")
        if not os.path.exists("models/fine_tuned_model.pt"):
            print("Fine-tuned model not found. Downloading fine-tuned model... [Via OneDrive (Public)]")
            fine_tune_model_dl()
        else:
            # load the fine-tuned model into memory
            try:
                whisper.load_model("models/fine_tuned_model.pt", device=device, download_root="models")
                print("Fine-tuned model loaded into memory.")
            except Exception as e:
                print("Failed to load fine-tuned model. Results may be inaccurate. If you experience issues, please delete the fine-tuned model from the models folder and restart the program. If you still experience issues, please open an issue on GitHub.")
                red_text = Fore.RED + Back.BLACK
                print(f"{red_text}Error: {e}")
                pass
    except:
        print("Error Code 21: Error while loading fine-tuned model.")
        sys.exit(1)
    
    try:
        audio_model = whisper.load_model(model, device=device, download_root="models")
    except:
        print("Error Code 22: Error while loading model.")
        sys.exit(1)

    try:
        record_timeout = args.record_timeout
        phrase_timeout = args.phrase_timeout
    except:
        print("Error Code 23: Error while setting timeout.")
        sys.exit(1)

    try:
        # create a folder temp if it doesn't exist
        if not os.path.exists("temp"):
            os.makedirs("temp")
        temp_dir = "temp"
        temp_file = NamedTemporaryFile(dir=temp_dir, delete=True, suffix=".ts", prefix="rec_").name
        transcription = ['']
    except:
        print("Error Code 24: Error while creating temp folder.")
        sys.exit(1)

    try:
        with source:
            recorder.adjust_for_ambient_noise(source)
    except:
        print("Error Code 25: Error while adjusting for ambient noise.")
        sys.exit(1)
    
    try:
        if args.discord_webhook:
            webhook_url = args.discord_webhook
            print(f"Sending console output to Discord webhook that was set in parameters.")
    except:
        print("Error Code 26: Error while setting Discord webhook.")
        sys.exit(1)

    try:
        recorder.listen_in_background(source, record_callback, phrase_time_limit=record_timeout)
    except:
        print("Error Code 27: Error while listening in background.")
        sys.exit(1)
    
    try:
        print("Model loaded.\n")
        print(f"Using {model} model.")
        if args.non_english:
            print("Using the multi-lingual model.")
    except:
        print("Error Code 28: Error while printing model info.")

    try:
        # warn the user if they are using AMD that CUDA may not work properly, if they are using CUDA
        if device.type == "cuda":
            if "AMD" in torch.cuda.get_device_name(torch.cuda.current_device()):
                print("WARNING: You are using an AMD GPU with CUDA. This may not work properly. If you experience issues, try using the CPU instead.")
    except:
        print("Error Code 29: Error while checking for AMD GPU.")
        sys.exit(1)

    try:
        english_counter = 0
        language_counters = {}
        last_detected_language = None 
    except:
        print("Error Code 30: Error while setting language counters.")
        sys.exit(1)

    try:
        # send a message to discord saying that the program has started, if translation is enabled then say that it is enabled
        if args.discord_webhook:
            if args.translate:
                send_to_discord_webhook(webhook_url, f"Transcription started. Translation enabled.\nUsing the {args.ram} ram model.")
            else:
                send_to_discord_webhook(webhook_url, f"Transcription started. Translation disabled.\nUsing the {args.ram} ram model.")
            sleep(0.25)
    except:
        print("Error Code 31: Error while sending Discord webhook message.")
        sys.exit(1)

    try:
        if args.auto_language_lock:
            print("Auto language lock enabled. Will auto lock after 5 consecutive detections of the same language.")
            if args.discord_webhook:
                send_to_discord_webhook(webhook_url, "Auto language lock enabled. Will auto lock after 5 consecutive detections of the same language.")
    except:
        print("Error Code 32: Error while setting auto language lock.")
        sys.exit(1)
        
    print("Awaiting audio stream...")

    while True:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                print("\nAudio stream detected...")
                try:
                    phrase_complete = False
                    if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                        last_sample = bytes()
                        phrase_complete = True
                    phrase_time = now
                except:
                    print("Error Code 33: Error while setting phrase time.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

                while not data_queue.empty():
                    try:
                        data = data_queue.get()
                        last_sample += data
                    except:
                        print("Error Code 34: Error while getting data from queue.")
                        # press any key to continue
                        input("Press any key to continue...")
                        pass
                try:
                    audio_data = sr.AudioData(last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                    wav_data = io.BytesIO(audio_data.get_wav_data())
                except:
                    print("Error Code 35: Error while getting audio data.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

                try:
                    with open(temp_file, 'w+b') as f:
                        f.write(wav_data.read())
                except:
                    print("Error Code 36: Error while writing to temp file.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass


                try:
                    audio = whisper.load_audio(temp_file)
                    audio = whisper.pad_or_trim(audio)
                    mel = whisper.log_mel_spectrogram(audio).to(device)
                    # if model name has .en in it, then skip _,
                    if ".en" in model:
                        detected_language = "English"
                    else:
                        _, language_probs = audio_model.detect_language(mel)
                        detected_language = max(language_probs, key=language_probs.get)
                except:
                    print("Error Code 37: Error while detecting language.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

                #check arguments for language preference sett by --language if it set with argument then we dont need to auto detect language
                try:
                    if args.language:
                        detected_language = args.language
                        # if the language was locked by the auto language lock, then print saying Locked to language if not then print set by argument
                        if args.auto_language_lock:
                            print(f"Language locked to {detected_language}")
                        else:
                            print(f"Language set by argument: {detected_language}")
                    else:
                        # if the language model has .en in the name, then it is the english model and we don't need to detect the language
                        if ".en" in model:
                            detected_language = "English"
                            print(f"Language set by model: {detected_language}")
                        else:
                            # if they use --auto_language_lock then lock the language after it has been detected 5 times in a row
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
                except:
                    print("Error Code 38: Error while setting language.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

                print("Transcribing...")
                try:
                    if device == "cuda":
                        result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available())
                    else:
                        result = audio_model.transcribe(temp_file)
                    print(f"Detected Speech: {result['text']}")
                    # if result is empty then try again
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
                except:
                    print("Error Code 39: Error while transcribing.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

                try:
                    if args.discord_webhook:
                        send_to_discord_webhook(webhook_url, f"Detected Speech: {result['text']}")
                    text = result['text'].strip()
                except:
                    print("Error Code 40: Error while sending to discord webhook.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass
                
                if args.translate:
                    try:
                        if detected_language != 'en':
                            print("Translating...")
                            if device == "cuda":
                                translated_result = audio_model.transcribe(temp_file, fp16=torch.cuda.is_available(), task="translate")
                            else:
                                translated_result = audio_model.transcribe(temp_file, task="translate")
                            translated_text = translated_result['text'].strip()
                            # if result is empty then try again
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
                    except:
                        print("Error Code 41: Error while translating.")
                        # press any key to continue
                        input("Press any key to continue...")
                        pass
                try:
                    if args.discord_webhook:
                        message = "----------------"
                        send_to_discord_webhook(webhook_url, message)
                except:
                    print("Error Code 42: Error while sending to discord webhook.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass
                        

                try:
                    if phrase_complete:
                        transcription.append((text, translated_text if args.translate else None, detected_language))
                    else:
                        transcription[-1] = (text, translated_text if args.translate else None, detected_language)
                except:
                    print("Error Code 43: Error while appending transcription.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass
                try:
                    os.system('cls' if os.name=='nt' else 'clear')
                    for original_text, translated_text, language_code in transcription:
                        # if there is no text in the transcription then skip it
                        if not original_text:
                            continue
                        # if language code is en no need to show translation
                        # print a bunch of "=" to make it look nice to fill the width of the terminal
                        print("=" * shutil.get_terminal_size().columns)
                        print(f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)} Detected - {language_code} {' ' * int((shutil.get_terminal_size().columns - 15) / 2)}")
                        # print(f"Original ({language_code}):\n")
                        print(f"{original_text}")



                        if language_code == 'en':
                            print('', end='', flush=True)
                        else:
                            if translated_text:
                                # print "-" in the center of the terminal with Translation in the middle
                                print(f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)} Translation {'-' * int((shutil.get_terminal_size().columns - 15) / 2)}")
                                print(f"{translated_text}\n")
                    print('', end='', flush=True)
                except:
                    print("Error Code 44: Error while printing transcription.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass
                try:
                    # change the model to base if the detected language is english
                    # if --auto-model-swap is set tru then we will change the model to base if the detected language is english
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
                except:
                    print("Error Code 45: Error while changing model.")
                    # press any key to continue
                    input("Press any key to continue...")
                    pass

        except Exception as e:
            # print error to file as error_report.txt, if it's a keyboard interrupt then don't print it.
            # also if the file already exist, then append to end of file
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
            # send a message to discord webhook if --discord-webhook is set saying that the program has stopped
            if args.discord_webhook:
                send_to_discord_webhook(webhook_url, "Service has stopped.")
            break

    # create out folder if it doesn't exist
    try:
        if not os.path.isdir('out'):
            os.mkdir('out')
    except:
        print("Error Code 46: Error while creating out folder.")
        # press any key to continue
        input("Press any key to continue...")
        pass
    
    try:
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
    except:
        print("Error Code 47: Error while saving transcription.")
        # press any key to continue
        input("Press any key to continue...")
        pass

if __name__ == "__main__":
    main()