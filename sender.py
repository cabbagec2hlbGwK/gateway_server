from smtplib import SMTP

def main():
    with smtplib.SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.send_message(message, mailfrom, rcpttos)
        smtp.quit()
    return '250 OK' ### ADDED RETURN

