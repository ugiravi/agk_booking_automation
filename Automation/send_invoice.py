# send_invoice.py
from flask import Flask, request, jsonify
from fpdf import FPDF
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)

@app.route('/send_invoice', methods=['POST'])
def send_invoice():
    data = request.json
    customer_email = data['email']
    customer_name = data['name']
    appointment_date = data['appointment_date']
    car_model = data['car_model']
    car_year = data['car_year']
    service_done = data['service']
    price = data['price']
    recommendations = data['recommendations']

    invoice_path = generate_invoice(customer_name, appointment_date, car_model, car_year, service_done, price)

    send_email_with_invoice(customer_email, customer_name, invoice_path, recommendations)

    return jsonify({"status": "Invoice sent"}), 200


def generate_invoice(name, date, model, year, service, price):
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
    filepath = f"{name.replace(' ', '_')}_invoice.pdf"
    pdf.output(filepath)
    return filepath


def send_email_with_invoice(to_email, name, pdf_path, recommendations):
    sender_email = "your_email@gmail.com"
    sender_password = os.getenv("EMAIL_PASSWORD")

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
        attach.add_header('Content-Disposition', 'attachment', filename=pdf_path)
        msg.attach(attach)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())

    print(f"Invoice sent to {to_email}")


if __name__ == '__main__':
    app.run(port=5000)
