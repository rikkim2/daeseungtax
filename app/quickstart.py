import os.path
import google.auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient import errors
from googleapiclient.errors import HttpError
from email.message import EmailMessage
import base64
def gmail_authenticate():
    SCOPES = ['https://mail.google.com/']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)
def create_message(sender, to, subject, message_text):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to.split(",")
    message["Subject"] = subject
    message.set_content(message_text)
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}
def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
def show_chatty_threads():
    """Display threads with long conversations(>= 3 messages)
    Return: None

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    # creds, _ = google.auth.default()

    try:
        # create gmail api client
        # service = build('gmail', 'v1', credentials=creds)
        service = gmail_authenticate()
        # pylint: disable=maybe-no-member
        # pylint: disable:R1710
        threads = service.users().threads().list(userId='me').execute().get('threads', [])
        for thread in threads:
            tdata = service.users().threads().get(userId='me', id=thread['id']).execute()
            nmsgs = len(tdata['messages'])
            
            # skip if <3 msgs in thread
            if nmsgs > 2:
                msg = tdata['messages'][0]['payload']
                subject = ''
                for header in msg['headers']:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                if subject:  # skip if no Subject line
                    print(F'- {subject}, {nmsgs}')
            else:
                print(tdata['messages'][0])
        return threads

    except HttpError as error:
        print(F'An error occurred: {error}')
# def main():
#     service = gmail_authenticate()
#     message = create_message("보내는사람", "받는사람", "제목", "내용")
#     send_message(service, "me", message)
# main()


show_chatty_threads()