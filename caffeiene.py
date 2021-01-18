import urllib.request
try :
    urllib.request.urlopen('https://inhabit-bot.herokuapp.com/').read()
except: 
    print('Keeping app awake ☕...')
