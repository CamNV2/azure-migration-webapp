import azure.functions as func
import logging
import os
from datetime import datetime
import psycopg2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s', notification_id)
 
    # Done: Get connection to database
    connection = psycopg2.connect(dbname="techconfdb", user="azureadmin@techconf-db-server", password="Camnguyen..2603", host="techconf-db-server.postgres.database.azure.com")
    cursor = connection.cursor()
    try:
        # TODO: Get notification message and subject from database using the notification_id
        cursor.execute("SELECT message, subject FROM notification WHERE id = {};".format(notification_id))
        messagePlain, subject = cursor.fetchone()
        # TODO: Get attendees email and name
        cursor.execute("SELECT first_name, last_name, email FROM attendee;")
        attendees = cursor.fetchall()

        # TODO: Loop through each attendee and send an email with a personalized subject
        for attendee in attendees:
          message = Mail(
              from_email='admin@techconf.com',
              to_emails=attendee[0],
              subject='{}: {}'.format(attendee[1], subject),
              html_content=messagePlain)
          try:
              sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
              response = sg.send(message)
              logging.info(response.status_code)
              logging.info(response.body)
          except Exception as e:
              logging.error(str(e))

        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        notification_completed_date = datetime.utcnow()

        notification_status = 'Notified {} attendees'.format(len(attendees))
        cursor.execute("UPDATE notification SET status = '{}', completed_date = '{}' WHERE id = {};".format(notification_status, notification_completed_date, notification_id))        
        connection.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
        # Done: Close connection