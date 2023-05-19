@echo off 
cls 
python "transcribe_audio.py" --ram 4gb --non_english --translate --device cpu
