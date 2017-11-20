import sqlite3
import smtplib
from email.mime.text import MIMEText
import configInfo
import datetime


conn = sqlite3.connect("data.sqlite3")


class Email:


    def __init__(self,id):
        self.id = id
        cur = conn.cursor()
        cur.execute("SELECT * FROM EmailArchive WHERE id = :id",{"id": self.id})
        try:
            full = cur.fetchone()
            self.recipient = full[1]
            self.subj = full[2]
            self.body = full[3]
            self.status = full[5]
        except:
            quit()

        cur.execute("SELECT email_to FROM Users WHERE id = :rec",{"rec": self.recipient})
        try:
            self.recipient = cur.fetchone()[0]
        except:
            quit()

        cur.close()


    def send(self):
        EMAIL_TO = self.recipient
        msg = MIMEText(self.body)
        msg["Subject"] = self.subj
        msg["From"] = configInfo.EMAIL_FROM
        msg["To"] = EMAIL_TO
        debuglevel = True
        try:
            mail = smtplib.SMTP(configInfo.SMTP_SERVER, configInfo.SMTP_PORT)
            mail.set_debuglevel(debuglevel)
            mail.starttls()
            mail.login(configInfo.SMTP_USERNAME, configInfo.SMTP_PASSWORD)
            mail.sendmail(configInfo.EMAIL_FROM, EMAIL_TO, msg.as_string())
            mail.quit()
            self.status = "sent "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        except smtplib.SMTPException as err:
            self.status = err

        cur = conn.cursor()
        cur.execute("UPDATE EmailArchive SET status = :stat WHERE id = :id",{"stat": self.status, "id": self.id})
        conn.commit()
        cur.close()
