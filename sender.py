from smtplib import SMTP

with SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
    print("+"*100)
    smtp.ehlo()  # send the extended hello to our server
    smtp.starttls()  # tell server we want to communicate with TLS encryption
    smtp.sendmail(from_addr='earth@brokencosmos.com', to_addrs=['asherjamesmkt@gmail.com'], msg='Your message')
    smtp.quit()
