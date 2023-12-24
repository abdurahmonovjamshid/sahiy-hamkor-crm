import requests

# Telegram bot token
bot_token = '6499088789:AAGiLIEdOicwRTLXVJTcSlTWm1Jx1Iq3E5w'

# Chat ID of the recipient
chat_id = '6116838287'

# URL of the file you want to send
file_url = 'https://saxiyhamkor.pythonanywhere.com/azamat_seh/sales/export-excel/?'

# Telegram API endpoint for sending a document
url = f'https://api.telegram.org/bot{bot_token}/sendDocument'

# Prepare the request payload
data = {'chat_id': chat_id}

# Send the file directly without downloading
with requests.get(file_url, stream=True) as response:
    response.raise_for_status()
    files = {'document': response.content}
    response = requests.post(url, files=files, data=data)

# Check the response status
if response.ok:
    print('File sent successfully!')
else:
    print('Failed to send the file.')
    print(response.text)