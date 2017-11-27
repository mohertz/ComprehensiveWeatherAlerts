import sqlite3
import smtplib
from email.mime.text import MIMEText
import logging
import configInfo
import datetime


logging.basicConfig(filename="weatherlogs.log",format="%(asctime)s | %(filename)s , %(lineno)d| %(levelname)s: %(message)s",level=logging.DEBUG)
conn = sqlite3.connect("data.sqlite3")


class Email:
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    def __init__(self,id):
        self.id = id
        cur = conn.cursor()
        cur.execute("SELECT * FROM EmailArchive WHERE id = :id",{"id": self.id})
        try:
            full = cur.fetchone()
            self.recipID = full[1]
            self.subj = full[2]
            self.body = full[3]
            self.status = full[5]
            logging.info("Creating email instance: %s" % str(self.id))
        except:
            logging.warning("Failed to create email instance: %s" % str(self.id))
            quit()

        cur.execute("SELECT email_to FROM Users WHERE id = :rec",{"rec": self.recipID})
        try:
            self.recipient = cur.fetchone()[0]
            logging.info("Adding email address: %s" % self.recipient)
        except:
            logging.warning("Failed to add email address: %s" % str(self.recipID))
            quit()

        cur.close()


    def send(self):
        logging.info("Initiating email: %s" % str(self.id))

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
            logging.info("Message sent: %s" % self.status)
        except smtplib.SMTPException as err:
            self.status = err
            logging.warning("Failed to send message: %s" % self.status)

        cur = conn.cursor()
        cur.execute("UPDATE EmailArchive SET status = :stat WHERE id = :id",{"stat": self.status, "id": self.id})
        logging.info("Updated email archive for %s" % str(self.id))
        cur.execute("UPDATE Users SET last_update = :t WHERE id = :r",{"t": self.today, "r": self.recipID})
        logging.info("Updated user archive for %s" % str(self.recipID))
        conn.commit()
        cur.close()
