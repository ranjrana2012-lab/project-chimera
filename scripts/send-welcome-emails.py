#!/usr/bin/env python3
"""
Personalized Welcome Email Script for Project Chimera

This script reads student information from a CSV file and sends personalized
welcome emails with role assignments and mentor information.
"""

import argparse
import csv
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional


# Role assignments with mentors
ROLE_ASSIGNMENTS: Dict[str, Dict[str, str]] = {
    "frontend_developer": {
        "mentor": "Sarah Chen",
        "mentor_email": "sarah.chen@chimera.dev",
        "title": "Frontend Developer"
    },
    "backend_developer": {
        "mentor": "Marcus Johnson",
        "mentor_email": "marcus.johnson@chimera.dev",
        "title": "Backend Developer"
    },
    "fullstack_developer": {
        "mentor": "Emily Rodriguez",
        "mentor_email": "emily.rodriguez@chimera.dev",
        "title": "Full-Stack Developer"
    },
    "data_engineer": {
        "mentor": "David Kim",
        "mentor_email": "david.kim@chimera.dev",
        "title": "Data Engineer"
    },
    "ml_engineer": {
        "mentor": "Dr. Priya Patel",
        "mentor_email": "priya.patel@chimera.dev",
        "title": "ML Engineer"
    },
    "devops_engineer": {
        "mentor": "Ahmed Hassan",
        "mentor_email": "ahmed.hassan@chimera.dev",
        "title": "DevOps Engineer"
    },
    "security_engineer": {
        "mentor": "Lisa Wong",
        "mentor_email": "lisa.wong@chimera.dev",
        "title": "Security Engineer"
    },
    "qa_engineer": {
        "mentor": "James Miller",
        "mentor_email": "james.miller@chimera.dev",
        "title": "QA Engineer"
    },
    "ui_ux_designer": {
        "mentor": "Maria Garcia",
        "mentor_email": "maria.garcia@chimera.dev",
        "title": "UI/UX Designer"
    },
    "product_manager": {
        "mentor": "Tom Anderson",
        "mentor_email": "tom.anderson@chimera.dev",
        "title": "Product Manager"
    }
}


# Role descriptions for email templates
ROLE_DESCRIPTIONS: Dict[str, str] = {
    "frontend_developer": (
        "As a Frontend Developer, you will be responsible for building and maintaining "
        "the user interface of our web applications. You'll work with modern frameworks "
        "like React and Vue.js to create responsive, accessible, and visually appealing "
        "user experiences."
    ),
    "backend_developer": (
        "As a Backend Developer, you will design and implement server-side logic, APIs, "
        "and database systems. You'll work with Python, Node.js, and PostgreSQL to build "
        "scalable and efficient backend services."
    ),
    "fullstack_developer": (
        "As a Full-Stack Developer, you will work across the entire application stack, "
        "from database design to user interface. You'll gain experience with both frontend "
        "and backend technologies, making you a versatile team member."
    ),
    "data_engineer": (
        "As a Data Engineer, you will design and maintain data pipelines, ETL processes, "
        "and data infrastructure. You'll work with tools like Apache Airflow, Spark, and "
        "various database technologies to ensure reliable data flow."
    ),
    "ml_engineer": (
        "As an ML Engineer, you will develop and deploy machine learning models into "
        "production. You'll work with frameworks like TensorFlow and PyTorch, and learn "
        "MLOps practices for model lifecycle management."
    ),
    "devops_engineer": (
        "As a DevOps Engineer, you will automate deployment processes, manage CI/CD pipelines, "
        "and maintain cloud infrastructure. You'll work with Docker, Kubernetes, and AWS "
        "to ensure reliable and scalable operations."
    ),
    "security_engineer": (
        "As a Security Engineer, you will identify and mitigate security vulnerabilities, "
        "implement security best practices, and conduct security audits. You'll learn about "
        "application security, network security, and compliance."
    ),
    "qa_engineer": (
        "As a QA Engineer, you will develop testing strategies, automate tests, and ensure "
        "product quality. You'll work with testing frameworks and CI/CD tools to maintain "
        "high standards of software quality."
    ),
    "ui_ux_designer": (
        "As a UI/UX Designer, you will create user-centered designs, conduct user research, "
        "and develop design systems. You'll work with Figma and Adobe XD to create intuitive "
        "and accessible user interfaces."
    ),
    "product_manager": (
        "As a Product Manager, you will define product vision, prioritize features, and "
        "coordinate between teams. You'll learn agile methodologies, stakeholder management, "
        "and data-driven decision making."
    )
}


def load_students(csv_path: str) -> List[Dict[str, str]]:
    """
    Load student data from CSV file.

    Args:
        csv_path: Path to the CSV file containing student data

    Returns:
        List of dictionaries containing student information
    """
    students = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Validate required fields
                if not row.get('email'):
                    print(f"Warning: Student {row.get('name', 'Unknown')} missing email, skipping",
                          file=sys.stderr)
                    continue
                students.append(row)
    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    return students


def load_template(template_path: str) -> str:
    """
    Load email template from file.

    Args:
        template_path: Path to the email template file

    Returns:
        Template content as string
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Warning: Template file not found: {template_path}", file=sys.stderr)
        print("Using default welcome template", file=sys.stderr)
        return get_default_template()
    except Exception as e:
        print(f"Error reading template file: {e}", file=sys.stderr)
        return get_default_template()


def get_default_template() -> str:
    """Return default email template."""
    return """Subject: Welcome to Project Chimera - {role_title} Assignment

Dear {preferred_name},

Welcome to Project Chimera! We are thrilled to have you join our team.

Your Role: {role_title}

{role_description}

Your Mentor: {mentor_name}
Email: {mentor_email}

{mentor_name} will be your primary point of contact and will guide you through your journey.
Please feel free to reach out to them with any questions.

Next Steps:
1. Reply to this email to confirm your acceptance
2. Schedule an introductory call with your mentor
3. Complete the onboarding documentation

We're excited to see what you'll accomplish!

Best regards,
The Project Chimera Team
"""


def create_email(template: str, student: Dict[str, str],
                 role_key: str) -> tuple[str, str]:
    """
    Create personalized email from template with placeholder substitutions.

    Args:
        template: Email template string with placeholders
        student: Student data dictionary
        role_key: Key for ROLE_ASSIGNMENTS and ROLE_DESCRIPTIONS

    Returns:
        Tuple of (subject, body) for the email
    """
    # Get role information
    role_info = ROLE_ASSIGNMENTS.get(role_key, ROLE_ASSIGNMENTS["fullstack_developer"])
    role_description = ROLE_DESCRIPTIONS.get(role_key, ROLE_DESCRIPTIONS["fullstack_developer"])

    # Prepare substitution values
    substitutions = {
        "name": student.get("name", student.get("preferred_name", "Student")),
        "preferred_name": student.get("preferred_name", student.get("name", "Student")),
        "email": student.get("email", ""),
        "role_title": role_info["title"],
        "role_key": role_key,
        "role_description": role_description,
        "mentor_name": role_info["mentor"],
        "mentor_email": role_info["mentor_email"]
    }

    # Substitute placeholders in template
    email_content = template.format(**substitutions)

    # Extract subject (first line after "Subject: ")
    lines = email_content.split('\n')
    subject = "Welcome to Project Chimera"
    body = email_content

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body = '\n'.join(lines[i+1:]).strip()
            break

    return subject, body


def send_email(to_email: str, subject: str, body: str,
               smtp_server: str = "localhost", smtp_port: int = 25,
               from_email: str = "noreply@chimera.dev",
               username: Optional[str] = None, password: Optional[str] = None,
               dry_run: bool = False) -> bool:
    """
    Send email via SMTP with dry-run support.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        from_email: Sender email address
        username: SMTP username (optional)
        password: SMTP password (optional)
        dry_run: If True, print email instead of sending

    Returns:
        True if email sent successfully, False otherwise
    """
    if dry_run:
        print("=" * 60)
        print(f"DRY RUN - Email to: {to_email}")
        print("=" * 60)
        print(f"From: {from_email}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)
        return True

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server
        if username and password:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)

        # Send email
        server.send_message(msg)
        server.quit()

        print(f"Successfully sent email to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}", file=sys.stderr)
        return False


def assign_role(student_id: int) -> str:
    """
    Assign a role to a student based on their ID.
    This uses round-robin assignment to distribute students across roles.

    Args:
        student_id: Student ID number

    Returns:
        Role key string
    """
    roles = list(ROLE_ASSIGNMENTS.keys())
    return roles[student_id % len(roles)]


def main():
    """Main function with argument parsing and email sending logic."""
    parser = argparse.ArgumentParser(
        description="Send personalized welcome emails to students",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to test without sending emails
  %(prog)s --dry-run

  # Send emails using custom template
  %(prog)s --template /path/to/template.txt

  # Use specific SMTP server
  %(prog)s --smtp smtp.gmail.com --port 587 --user me@gmail.com

  # Process specific student
  %(prog)s --student-id 3
        """
    )

    parser.add_argument(
        "--csv",
        default="/home/ranj/Project_Chimera/data/students.csv",
        help="Path to CSV file containing student data (default: %(default)s)"
    )

    parser.add_argument(
        "--template",
        default="/home/ranj/Project_Chimera/data/welcome-template.txt",
        help="Path to email template file (default: %(default)s)"
    )

    parser.add_argument(
        "--smtp",
        default="localhost",
        help="SMTP server hostname (default: %(default)s)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=25,
        help="SMTP server port (default: %(default)s)"
    )

    parser.add_argument(
        "--from",
        dest="from_email",
        default="noreply@chimera.dev",
        help="Sender email address (default: %(default)s)"
    )

    parser.add_argument(
        "--user",
        help="SMTP username for authentication"
    )

    parser.add_argument(
        "--password",
        help="SMTP password for authentication"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print emails without sending them"
    )

    parser.add_argument(
        "--student-id",
        type=int,
        help="Only send email to specific student ID"
    )

    parser.add_argument(
        "--role",
        choices=list(ROLE_ASSIGNMENTS.keys()),
        help="Assign specific role to all students (default: round-robin)"
    )

    args = parser.parse_args()

    # Load template
    template = load_template(args.template)

    # Load students
    students = load_students(args.csv)

    if not students:
        print("No students found in CSV file", file=sys.stderr)
        sys.exit(1)

    # Filter by student ID if specified
    if args.student_id is not None:
        students = [s for s in students if int(s.get('id', 0)) == args.student_id]
        if not students:
            print(f"No student found with ID: {args.student_id}", file=sys.stderr)
            sys.exit(1)

    # Send emails
    success_count = 0
    failure_count = 0

    for student in students:
        # Determine role
        if args.role:
            role_key = args.role
        else:
            student_id = int(student.get('id', 0))
            role_key = assign_role(student_id)

        # Create email
        subject, body = create_email(template, student, role_key)

        # Send email
        if send_email(
            student['email'],
            subject,
            body,
            smtp_server=args.smtp,
            smtp_port=args.port,
            from_email=args.from_email,
            username=args.user,
            password=args.password,
            dry_run=args.dry_run
        ):
            success_count += 1
        else:
            failure_count += 1

    # Print summary
    print(f"\nSummary: {success_count} successful, {failure_count} failed")

    if failure_count > 0 and not args.dry_run:
        sys.exit(1)


if __name__ == "__main__":
    main()
