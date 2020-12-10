#!/usr/bin/env python3

# Import smtplib for the actual sending function
import smtplib
import ssl
# Import the email modules we'll need
from email.message import EmailMessage


def email_myself():
  # Create a text/plain message
  msg = EmailMessage()
  msg.set_content("Check your latency throughput")

  # me == the sender's email address
  # you == the recipient's email address
  msg['Subject'] = "Check your latency throughput"

  port = 465  # For SSL
  throwaway = "9G31h*vj03G*DpTO"
  # Create a secure SSL context
  context = ssl.create_default_context()

  with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login("72ljennifer72@gmail.com", throwaway)

    # Send email here
    server.send_message(msg, "72ljennifer72@gmail.com", "72ljennifer72@gmail.com")
    server.quit()


if __name__ == "__main__":
  email_myself()
