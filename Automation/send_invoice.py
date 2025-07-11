import os
import uuid
import logging
from flask import Flask, request, jsonify
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_case_insensitive(data, *keys):
    """Try to get value from JSON data ignoring key case or variants."""
    for key in keys:
        for k, v in data.items():
            if k.lower() == key.lower():
                return v
    return None

@app.route('/send_invoice', methods=['POST'])
def send_invoice():
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")

        # Get fields with fallback on key casing
        customer_email = get_case_insensitive(data, 'email', 'Email')
        customer_name = get_case_insensitive(data, 'name', 'Name')
        appointment_date = get_case_insensitive(data, 'date', 'Date', 'appointment_date')
        car_model = get_case_insensitive(data, 'car_model', 'Car_model', 'Car Model') or 'Unknown Model'
        car_year = get_case_insensitive(data, 'car_year', 'Car_year', 'Car Year') or 'Unknown Year'

        # Hardcoded service details for now
        service_done = "General Maintenance"
        price = "100"
        recommendations = "Check tire pressure next visit."

        if not all([customer_email, customer_name, appointment_date]):
            return jsonify({"error": "Missing required fields"}), 400

        # Generate unique invoice filename
        unique_id = uuid.uuid4().hex
        invoice_path = generate_invoice(customer_name, appointment_date, car_model, car_year, service_done, price, unique_id)

        send_email_with_invoice(customer_email, customer_name, invoice_path, recommendations)

        # Clean up PDF file after sending
        if os.path.exists(invoice_path):
            os.remove(invoice_path)

        return jsonify({"status": "Invoice sent"}), 200

    except Exception as e:
        app.logger.error(f"Error in send_invoice: {e}")
        return jsonify({"error": str(e)}), 500


def generate_invoice(name, date, model, year, service, price, uid):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="AGK Motors - Service Invoice", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=(
        f"Customer: {name}\n"
        f"Date: {date}\n"
        f"Car: {year} {model}\n"
        f"Service Performed: {service}\n"
        f"Total: ${price}"
    ))
    filepath = f"{name.replace(' ', '_')}_{uid}_invoice.pdf"
    pdf.output(filepath)
    return filepath


def send_email_with_invoice(to_email, name, pdf_path, recommendations):
    sender_email = os.getenv("EMAIL_ADDRESS")  # set this in your environment vars on Render
    sender_password = os.getenv("EMAIL_PASSWORD")
    if not sender_email or not sender_password:
        raise Exception("Email credentials not set in environment variables")

    subject = "Your AGK Motors Service Invoice & Recommendations"
    body = f"""
Hi {name},

Thank you for choosing AGK Motors.

Attached is your invoice from your recent service appointment.

🛠️ Recommendations:
{recommendations}

Please reach out if you have any questions!

- AGK Motors
"""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(pdf_path, 'rb') as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_path))
        msg.attach(attach)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())

    app.logger.info(f"Invoice sent to {to_email}")


if __name__ == '__main__':
    app.run(port=5000)
