import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from Utils import email_config


def send_email_report(
    file_path: str,
    recipient: str = None,
    subject: str = None,
    custom_message: str = None,
) -> bool:
    """
    Sends an email with the updated output file attached and its content previewed in the body.

    :param file_path: Path to the OUTPUT_FILE (e.g. 'SavingForCollege_monthly_revenue.txt')
    :param recipient: Recipient email address (defaults to DEFAULT_RECIPIENT)
    :param subject: Custom subject line (optional)
    :param custom_message: Additional message to include in the email body (optional)
    :return: True if sent successfully, False otherwise
    """
    target_recipient = recipient or email_config.DEFAULT_RECIPIENT
    file = Path(file_path)

    # 1. Verify file exists
    if not file.exists():
        print(f"[Email Warning] Output file not found at '{file_path}'. Email skipped.")
        return False

    # 2. Check credentials
    sender = email_config.SENDER_EMAIL or os.getenv("SENDER_EMAIL")
    password = email_config.SENDER_PASSWORD or os.getenv("SENDER_PASSWORD")

    if not sender or not password:
        print("\n" + "=" * 65)
        print("[Email Notification] Output file was updated, but email credentials are not set!")
        print(f"Target Recipient: {target_recipient}")
        print(f"File to send:     {file.resolve()}")
        print("\nTo send emails automatically:")
        print("  1. Create a 16-character App Password in your Google Account:")
        print("     (Google Account -> Security -> 2-Step Verification -> App Passwords)")
        print("  2. Add your sender email and app password to:")
        print("     - .env file (SENDER_EMAIL=... and SENDER_PASSWORD=...)")
        print("     - OR directly in Utils/email_config.py")
        print("=" * 65 + "\n")
        return False

    # 3. Read file content for preview
    try:
        content_preview = file.read_text(encoding="utf-8")
    except Exception as e:
        content_preview = f"(Could not read text preview: {e})"

    # 4. Prepare email message
    if not subject:
        subject = f"[Report Update] {file.name}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = target_recipient

    body_lines = [
        "Hello,",
        "",
        f"The revenue report '{file.name}' has been updated by the automation suite.",
    ]
    if custom_message:
        body_lines.extend(["", custom_message])

    body_lines.extend([
        "",
        "--- File Content Preview ---",
        content_preview.strip(),
        "----------------------------",
        "",
        "The updated file is also attached to this email.",
        "",
        "Best regards,",
        "Sindhu Automation Suite",
    ])
    msg.set_content("\n".join(body_lines))

    # 5. Attach file
    try:
        with open(file, "rb") as f:
            file_data = f.read()
            msg.add_attachment(
                file_data,
                maintype="text",
                subtype="plain",
                filename=file.name,
            )
    except Exception as e:
        print(f"[Email Error] Could not attach file '{file.name}': {e}")
        return False

    # 6. Send via SMTP
    try:
        # Gmail app passwords are displayed with spaces, remove them for SMTP login
        auth_password = password.replace(" ", "")

        if email_config.SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(email_config.SMTP_SERVER, email_config.SMTP_PORT, context=context) as server:
                server.login(sender, auth_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(email_config.SMTP_SERVER, email_config.SMTP_PORT) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(sender, auth_password)
                server.send_message(msg)

        print(f"[Email Success] Sent updated '{file.name}' to {target_recipient}")
        return True
    except Exception as e:
        print(f"[Email Error] Failed to send email to {target_recipient}: {e}")
        return False
