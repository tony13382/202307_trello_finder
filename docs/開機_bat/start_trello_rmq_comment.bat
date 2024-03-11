cd "C:\Users\vm\Desktop\呂亮進工作區\trello_finder"
call conda activate liang_trello_finder
timeout /t 90
python rmq_comment_service.py
pause