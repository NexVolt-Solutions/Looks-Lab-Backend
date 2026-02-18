"""
Legal routes.
Handles Privacy Policy and Terms of Service endpoints.
"""
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# ── Constants ─────────────────────────────────────────────────────

SUPPORT_EMAIL = "support@looks-lab.com"
APP_NAME = "Looks Lab"
LAST_UPDATED = date(2026, 2, 17)


# ── Schemas ───────────────────────────────────────────────────────

class LegalSection(BaseModel):
    title: str | None = None
    content: str
    points: list[str] | None = None


class PrivacyPolicyOut(BaseModel):
    title: str
    last_updated: date
    app_name: str
    sections: list[LegalSection]


class TermsOfServiceOut(BaseModel):
    title: str
    last_updated: date
    app_name: str
    intro: str
    sections: list[LegalSection]


# ── Routes ────────────────────────────────────────────────────────

@router.get("/privacy-policy", response_model=PrivacyPolicyOut)  # ✅ Added response_model
async def get_privacy_policy():
    """Get Privacy Policy for Looks Lab app."""
    return PrivacyPolicyOut(
        title="Privacy Policy",
        last_updated=LAST_UPDATED,
        app_name=APP_NAME,
        sections=[
            LegalSection(content=(
                "Looks Lab values your privacy and is committed to protecting your personal information. "
                "When you use our app, we may collect certain personal information such as your name, "
                "email address, username, and account details to allow you to sign up, log in, and "
                "personalize your experience."
            )),
            LegalSection(content=(
                "We may also collect non-personal information including device type, operating system, "
                "language preferences, and app usage data to improve app performance and stability. "
                "Any prompts, preferences, or content you submit within the app may be temporarily "
                "stored for processing and service improvement, but will not be shared with third "
                "parties for advertising or resale."
            )),
            LegalSection(content=(
                "We do not sell, trade, or rent your personal information. Your data may only be "
                "shared with trusted service providers that help operate the app or if required by law. "
                "Data is retained only as long as necessary to provide the service, after which it is "
                "securely deleted. You can request deletion of your account and related data at any "
                "time by contacting us."
            )),
            LegalSection(content=(
                "We take appropriate technical and organizational measures to protect your information "
                "from unauthorized access, loss, or misuse, but please understand that no digital "
                "system can be completely secure."
            )),
            LegalSection(content=(
                f"{APP_NAME} is intended for general audiences and does not knowingly collect data from "
                "children under 13 years of age. If such data is discovered, it will be deleted immediately."
            )),
            LegalSection(content=(
                f"By using {APP_NAME}, you consent to the collection and use of information as described "
                "in this policy. We may update this Privacy Policy periodically, and the updated version "
                "will be available in the app. Continued use of the app after updates means you accept "
                "the revised terms."
            )),
            LegalSection(content=(
                f"For any questions, concerns, or requests regarding your privacy, please contact us at "
                f"{SUPPORT_EMAIL}."
            )),
        ]
    )


@router.get("/terms-of-service", response_model=TermsOfServiceOut)
async def get_terms_of_service():
    """Get Terms of Service for Looks Lab app."""
    return TermsOfServiceOut(
        title="Terms of Service",
        last_updated=LAST_UPDATED,
        app_name=APP_NAME,
        intro=(
            f"Welcome to {APP_NAME} ('we', 'our', 'us'). These Terms of Use govern your use of our mobile "
            "application (the 'Service'). By accessing or using Looks Lab, you agree to be bound by these Terms."
        ),
        sections=[
            LegalSection(
                title="Acceptance of Terms",
                content=(
                    "By registering or using our Service, you confirm that you are at least 13 years of age "
                    "and you agree to these Terms and our Privacy Policy. If you do not agree, please "
                    "discontinue use of the Service."
                )
            ),
            LegalSection(
                title="Description of Service",
                content=(
                    f"{APP_NAME} is an AI-powered personal transformation app that provides personalized "
                    "recommendations for skincare, hair care, fitness, diet, fashion, and more based on "
                    "your unique profile and goals."
                ),
                points=[
                    "Get AI-powered personalized recommendations",
                    "Track your transformation progress over time",
                    "Access domain-specific routines and product recommendations",
                    "Upload photos for AI analysis and personalized insights",
                    "Access premium features with an active subscription"
                ]
            ),
            LegalSection(
                title="User Accounts",
                content=(
                    "When creating an account, you must provide accurate and complete information. "
                    "You are responsible for maintaining the confidentiality of your login credentials "
                    "and all activity conducted under your account."
                )
            ),
            LegalSection(
                title="Intellectual Property",
                content=(
                    "All content, design, branding, and features within Looks Lab are the exclusive "
                    "property of our company. You may not copy, modify, reverse engineer, or redistribute "
                    "any part of the Service without prior permission."
                )
            ),
            LegalSection(
                title="User Content",
                content=(
                    "Any content you create remains yours. However, by using Looks Lab, you grant us "
                    "permission to store, process, and use anonymized data to improve the Service. "
                    "You are responsible for:"
                ),
                points=[
                    "Ensuring your content does not violate laws or third-party rights",
                    "Not generating harmful, illegal, or offensive content",
                    "Avoiding false or misleading information",
                    "Not uploading content that violates others' privacy"
                ]
            ),
            LegalSection(
                title="Subscription & Payments",
                content=(
                    "Access to premium features requires an active subscription. Subscriptions are billed "
                    "on a weekly, monthly, or yearly basis depending on your selected plan. All payments "
                    "are non-refundable unless required by law. You may cancel your subscription at any "
                    "time through the app settings."
                )
            ),
            LegalSection(
                title="Privacy",
                content=(
                    "Your use of the Service is also governed by our Privacy Policy, which is incorporated "
                    "into these Terms by reference. Please review our Privacy Policy to understand our practices."
                )
            ),
            LegalSection(
                title="Termination",
                content=(
                    "We reserve the right to suspend or terminate your account if you violate these Terms "
                    "or engage in any activity that harms the Service or other users. You may delete your "
                    "account at any time through the app settings."
                )
            ),
            LegalSection(
                title="Limitation of Liability",
                content=(
                    f"{APP_NAME} is provided 'as is' without warranties of any kind. We are not liable for "
                    "any indirect, incidental, or consequential damages arising from your use of the Service. "
                    "AI recommendations are for informational purposes only and should not replace "
                    "professional medical or health advice."
                )
            ),
            LegalSection(
                title="Changes to Terms",
                content=(
                    "We may update these Terms from time to time. The updated version will be available "
                    "in the app. Continued use of the Service after changes means you accept the revised Terms."
                )
            ),
            LegalSection(
                title="Contact Us",
                content=(
                    f"For any questions or concerns about these Terms, please contact us at {SUPPORT_EMAIL}."
                )
            ),
        ]
    )

