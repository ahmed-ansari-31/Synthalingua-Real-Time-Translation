@echo off
Title Realtime Whipser Translation App
cls

@REM if exist "data_whisper" (
@REM     set /p reinstall="Python environment already exists. Do you want to reinstall? [y/n]: "
@REM     if /i "%reinstall%"=="y" (
@REM         echo Deleting existing environment...
@REM         call data_whisper\Scripts\deactivate.bat
@REM         rmdir /s /q data_whisper
@REM     ) else (
@REM         echo Exiting...
@REM         @REM exit /b
@REM     )
@REM )

@REM Echo Creating python environment...
@REM python -m venv data_whisper

Echo Running file...

@REM call data_whisper\Scripts\activate.bat
@REM Echo Installing Whisper
@REM Echo Updating pip
@REM python.exe -m pip install --upgrade pip

@REM Echo Installing Requirements...
@REM pip install wheel
@REM pip install setuptools-rust
@REM pip install -r requirements.txt

@REM :cuda-patch
@REM Echo Fixing CUDA Since Whisper installs non gpu version.
@REM pip uninstall --yes torch torchvision torchaudio
@REM pip cache purge
@REM pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Echo. Setup Completed!


:creating shortcut
Echo Creating example shortcut in %cd%
Echo You can edit with notepad anytime.
Echo.
Echo @echo off > livetranslation.bat
Echo cls >> livetranslation.bat
@REM Echo call "data_whisper\Scripts\activate.bat" >> livetranslation.bat
Echo python "transcribe_audio.py" --ram 4gb --non_english --translate >> livetranslation.bat
pause

:eof
