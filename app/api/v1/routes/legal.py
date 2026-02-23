"""
Legal routes.
Returns Privacy Policy and Terms of Service in structured JSON format.
"""
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────

SUPPORT_EMAIL = "support@lookslab.com"
APP_NAME = "Looks Lab"
COMPANY_NAME = "Looks Lab"
WEBSITE = "https://lookslab.com"
LAST_UPDATED = "February 2025"


# ── Schemas ───────────────────────────────────────────────────────

class LegalSection(BaseModel):
    """Individual section in legal document."""
    id: str
    title: str
    body: str


class PrivacyPolicyOut(BaseModel):
    """Privacy Policy response structure."""
    version: str
    lastUpdated: str
    sections: list[LegalSection]


class TermsOfServiceOut(BaseModel):
    """Terms of Service response structure."""
    version: str
    lastUpdated: str
    sections: list[LegalSection]


# ── Routes ────────────────────────────────────────────────────────

@router.get("/privacy-policy", response_model=PrivacyPolicyOut)
async def get_privacy_policy():
    """
    Get Privacy Policy for Looks Lab app.
    Returns structured JSON with sections array.
    """
    return PrivacyPolicyOut(
        version="1.0",
        lastUpdated=LAST_UPDATED,
        sections=[
            LegalSection(
                id="intro",
                title="",
                body=(
                    f'{APP_NAME} ("we", "our", "us") is committed to protecting your privacy. '
                    "This Privacy Policy explains how we collect, use, store, and share information "
                    "when you use our mobile application and related services."
                )
            ),

            LegalSection(
                id="information-we-collect",
                title="Information We Collect",
                body=(
                    "• Account & profile: When you sign in with Google or Apple, we receive your name, "
                    "email address, and profile photo. We may also store a user ID and optional phone "
                    "number on our servers.\n\n"

                    "• Health & lifestyle: To personalize your experience, we collect your choices from "
                    "our onboarding and profile flows, such as diet type (e.g. balanced, protein, vegetarian), "
                    "workout frequency, gender, age, height, weight, and answers to questions about energy, "
                    "mood, sleep, stress, screen time, and lifestyle.\n\n"

                    "• Photos & scans: If you use our skin, hair, facial, fashion, or food analysis features, "
                    "you may upload or capture photos. These are used to generate personalized routines and "
                    "recommendations and may be processed on our servers or by trusted service providers "
                    "(Google Gemini AI, AWS S3).\n\n"

                    "• Subscription & payment: When you subscribe, payment processing is handled by Apple "
                    "App Store or Google Play Store. We do not store payment card details. We receive "
                    "subscription status and transaction confirmations from the app stores."
                )
            ),

            LegalSection(
                id="how-we-use",
                title="How We Use Your Information",
                body=(
                    "We use your information to: create and manage your account; provide personalized "
                    "skincare, haircare, fitness, diet, height, facial, fashion, and quit porn support "
                    "routines; analyze your photos to deliver AI-based recommendations using Google Gemini; "
                    "process subscriptions and validate payment receipts; track your progress across multiple "
                    "wellness domains; send you important updates and notifications (if enabled); improve our "
                    "app and services; and provide customer support. We do not sell your personal information "
                    "to third parties for advertising or marketing."
                )
            ),

            LegalSection(
                id="data-storage",
                title="Data Storage and Retention",
                body=(
                    "Your data is stored on secure servers (PostgreSQL database, AWS S3 for images) and may "
                    "be processed in regions where our service providers operate. We retain your information "
                    "for as long as your account is active or as needed to provide the service, comply with "
                    "law, or resolve disputes. Account data is retained until deletion; images until you "
                    "delete them or your account; usage logs for 90 days; transaction records for 7 years "
                    "for legal compliance. You can request deletion of your account and associated data at "
                    f"any time via app settings or by contacting {SUPPORT_EMAIL}; we will delete or anonymize "
                    "it within 30 days in line with our legal obligations."
                )
            ),

            LegalSection(
                id="third-party",
                title="Third-Party Services",
                body=(
                    "We use third-party services that may collect or process data: Google Sign-In (for "
                    "authentication and account info); Apple Sign-In (for authentication); Google Gemini API "
                    "(for AI-powered image analysis and recommendations); AWS S3 (for secure image storage); "
                    "Apple App Store and Google Play Store (for payment processing). These providers have "
                    "their own privacy policies. We only share data necessary for them to perform their "
                    "services and require they protect your information appropriately."
                )
            ),

            LegalSection(
                id="photos-and-ai",
                title="Photos and AI Analysis",
                body=(
                    "Photos you provide for skin, hair, facial, food, or body/style analysis are used solely "
                    "to generate your personalized routines and recommendations using Google Gemini AI. They "
                    "are stored securely on AWS S3 with encryption and access controls. Images are not used "
                    "for advertising, not sold to third parties, and not used to train AI models. You can "
                    "delete images at any time through the app. We use technical and organizational measures "
                    "including HTTPS/TLS encryption, secure authentication (OAuth 2.0, JWT tokens), and "
                    "role-based access controls to protect your images."
                )
            ),

            LegalSection(
                id="your-rights",
                title="Your Rights",
                body=(
                    "Depending on your location, you may have the right to access, correct, or delete your "
                    "personal data, object to or restrict certain processing, and data portability. You can "
                    "update profile information in the app settings, delete individual images or insights, "
                    "export your data, and request full account deletion. For California residents (CCPA) "
                    "and European residents (GDPR), you have additional rights including right to know what "
                    "data is collected, right to opt-out of data sales (we don't sell data), and right to "
                    f"non-discrimination. Contact us at {SUPPORT_EMAIL} to exercise your rights. We will "
                    "respond to valid requests in line with applicable law within 30 days."
                )
            ),

            LegalSection(
                id="security",
                title="Security",
                body=(
                    "We use industry-standard measures to protect your data from unauthorized access, loss, "
                    "or misuse including: end-to-end encryption for data transmission (HTTPS/TLS), encrypted "
                    "storage for images and sensitive data, secure authentication using OAuth 2.0, JWT tokens "
                    "with expiration, regular security audits and updates, access controls and user "
                    "authentication, and secure database with parameterized queries. No system is completely "
                    "secure; we encourage you to keep your login credentials safe, use strong passwords, "
                    "enable two-factor authentication on your Google/Apple account, and use a secure connection "
                    "when using the app."
                )
            ),

            LegalSection(
                id="children",
                title="Children",
                body=(
                    f"{APP_NAME} is not intended for users under 13. We do not knowingly collect personal "
                    "information from children under 13. If we learn that we have collected such data, we "
                    "will delete it promptly. If you are a parent or guardian and believe your child has "
                    f"provided us data, please contact us at {SUPPORT_EMAIL}."
                )
            ),

            LegalSection(
                id="changes",
                title="Changes to This Policy",
                body=(
                    'We may update this Privacy Policy from time to time. The "Last updated" date at the '
                    "top will change when we do. We may notify you of significant changes in the app, by "
                    "email, or through an in-app notification. Continued use of the app after changes means "
                    "you accept the updated policy. Material changes will be highlighted and you may be asked "
                    "to review and accept them."
                )
            ),

            LegalSection(
                id="contact",
                title="Contact Us",
                body=(
                    "For privacy-related questions, requests (e.g. access, correction, deletion), or "
                    f"complaints, contact us at {SUPPORT_EMAIL}. You can also visit our website at "
                    f"{WEBSITE}. We aim to respond within 48 hours and will address your request in "
                    "accordance with applicable law. For account deletion requests, please include your "
                    "registered email address and user ID (found in app settings)."
                )
            ),
        ]
    )


@router.get("/terms-of-service", response_model=TermsOfServiceOut)
async def get_terms_of_service():
    """
    Get Terms of Service for Looks Lab app.
    Returns structured JSON with sections array.
    """
    return TermsOfServiceOut(
        version="1.0",
        lastUpdated=LAST_UPDATED,
        sections=[
            LegalSection(
                id="intro",
                title="",
                body=(
                    f'Welcome to {APP_NAME} ("we", "our", "us"). These Terms of Use govern your use of '
                    'our mobile application (the "Service"). By accessing or using Looks Lab, you agree '
                    "to be bound by these Terms."
                )
            ),

            LegalSection(
                id="acceptance",
                title="Acceptance of Terms",
                body=(
                    "By registering or using our Service, you confirm that you are at least 13 years of age "
                    "and you agree to these Terms and our Privacy Policy. If you are between 13 and 18, you "
                    "must have parental or guardian consent to use the Service. If you do not agree, please "
                    "discontinue use of the Service."
                )
            ),

            LegalSection(
                id="description",
                title="Description of Service",
                body=(
                    f"{APP_NAME} is an AI-powered personal wellness and transformation app that provides "
                    "personalized routines and recommendations for skincare, haircare, fitness, diet, height "
                    "optimization, facial improvement, fashion, and behavioral support. Users can: complete "
                    "anonymous onboarding before account creation; sign in with Google or Apple; set health "
                    "and lifestyle preferences through detailed questionnaires; upload or capture photos for "
                    "skin, hair, facial, food, or body analysis using AI; receive AI-based personalized routines "
                    "and product recommendations powered by Google Gemini; track nutrition, workouts, and progress "
                    "across 8 wellness domains; view daily wellness metrics (height, weight, sleep, water intake); "
                    "and subscribe to access premium features including unlimited AI analysis, advanced insights, "
                    "and ad-free experience."
                )
            ),

            LegalSection(
                id="user-accounts",
                title="User Accounts",
                body=(
                    "When creating an account, you must provide accurate and complete information through "
                    "Google Sign-In or Apple Sign-In. You are responsible for maintaining the confidentiality "
                    "of your login credentials and all activity conducted under your account. You may not share "
                    "your account with others, transfer your account to another person, or create multiple accounts. "
                    "You must notify us immediately of any unauthorized access to your account."
                )
            ),

            LegalSection(
                id="intellectual-property",
                title="Intellectual Property",
                body=(
                    f"All content, design, branding, features, AI models, and technology within {APP_NAME} are "
                    f"the exclusive property of {COMPANY_NAME} or our licensors and are protected by copyright, "
                    "trademark, patent, and trade secret laws. You may not copy, modify, reverse engineer, "
                    "decompile, disassemble, or redistribute any part of the Service without prior written permission. "
                    f"The {APP_NAME} name and logo are trademarks of {COMPANY_NAME}."
                )
            ),

            LegalSection(
                id="subscription",
                title="Subscription and Payment",
                body=(
                    "Access to premium features requires an active subscription. We offer monthly and yearly "
                    "subscription plans with pricing displayed in the app (prices may vary by region). By subscribing, "
                    "you agree to the pricing and billing terms shown at the time of purchase. Subscriptions are "
                    "processed through Apple App Store (iOS) or Google Play Store (Android). Fees are charged in "
                    "accordance with your chosen plan and automatically renew unless canceled at least 24 hours "
                    "before the renewal date. You may cancel subscriptions through your App Store or Play Store "
                    "account settings. Cancellation takes effect at the end of the current billing period. Refunds "
                    "are subject to Apple's and Google's refund policies; generally, no refunds are provided for "
                    "partial subscription periods. We reserve the right to change pricing with advance notice; "
                    "continued use after a price change constitutes acceptance."
                )
            ),

            LegalSection(
                id="user-content",
                title="User Content and Conduct",
                body=(
                    "You are responsible for any content you submit, including photos, profile information, and "
                    "responses to questionnaires. You retain ownership of your content, but grant us a license to "
                    "store, process, and use it to provide the Service and generate recommendations. You must not: "
                    "use the Service for any illegal purpose; upload content that is offensive, abusive, defamatory, "
                    "or pornographic; upload images of other people without their consent; upload images of minors; "
                    "attempt to reverse engineer or hack the Service; use automated systems (bots) to access the "
                    "Service; abuse, harass, or threaten other users; impersonate another person; distribute spam or "
                    "viruses; violate intellectual property rights; or interfere with the Service's operation. We may "
                    "remove content or suspend or terminate accounts that breach these rules. You are solely responsible "
                    "for your content and its legality."
                )
            ),

            LegalSection(
                id="disclaimers",
                title="Disclaimers",
                body=(
                    'The Service and all content, routines, and recommendations are provided "as is" for general '
                    "wellness and informational purposes only. They are not a substitute for professional medical, "
                    "nutritional, dermatological, or fitness advice. AI recommendations are based on limited data and "
                    "may occasionally produce inaccurate results. Consult a qualified healthcare professional before "
                    "starting any new diet, exercise, skincare regimen, or health program, especially if you have "
                    "pre-existing conditions, are pregnant, or taking medications. We do not guarantee specific results "
                    f"from using the app. {APP_NAME} is not a medical device and is not intended to diagnose, treat, "
                    "cure, or prevent any disease. We disclaim all warranties, express or implied, including warranties "
                    "of merchantability, fitness for a particular purpose, accuracy, and non-infringement."
                )
            ),

            LegalSection(
                id="limitation",
                title="Limitation of Liability",
                body=(
                    f"To the fullest extent permitted by law, {COMPANY_NAME.upper()} and its officers, directors, "
                    "employees, and agents shall not be liable for any indirect, incidental, special, consequential, "
                    "or punitive damages, or any loss of profits, revenue, data, or business opportunities, personal "
                    "injury, or property damage arising from your use of the Service. This includes damages from "
                    "reliance on AI recommendations, unauthorized access to your data, third-party conduct, or service "
                    "interruptions. Our total liability shall not exceed the amount you paid us in the twelve months "
                    "before the claim, or $100 (whichever is greater). Some jurisdictions do not allow certain "
                    "limitations; in such cases our liability is limited to the maximum permitted by law."
                )
            ),

            LegalSection(
                id="termination",
                title="Termination",
                body=(
                    "We may suspend or terminate your access to the Service immediately, without prior notice, if you "
                    "violate these Terms, engage in fraudulent or illegal activity, abuse other users or staff, or if "
                    "your payment fails. You may stop using the Service at any time by deleting your account in app "
                    f"settings or contacting {SUPPORT_EMAIL}. Upon termination, your access ceases immediately, your "
                    "subscription is canceled (no refund for partial periods), and your data will be deleted within 30 "
                    "days except where required by law. Provisions that by their nature should survive (including "
                    "intellectual property rights, disclaimers, and limitation of liability) will remain in effect after "
                    "termination."
                )
            ),

            LegalSection(
                id="governing-law",
                title="Governing Law and Disputes",
                body=(
                    "These Terms are governed by the laws of [Your Jurisdiction], without regard to conflict of law "
                    "principles. Any disputes arising from these Terms or the Service will be resolved through binding "
                    "arbitration rather than in court, except that you may assert claims in small claims court if they "
                    "qualify, and either party may seek injunctive relief for intellectual property disputes. You agree "
                    "that disputes will be resolved individually, not as part of a class action. You waive any right to "
                    f"a jury trial. Before filing arbitration, contact us at {SUPPORT_EMAIL} to attempt informal resolution."
                )
            ),

            LegalSection(
                id="changes-to-terms",
                title="Changes to Terms",
                body=(
                    "We may update these Terms from time to time to reflect changes in our practices, features, or legal "
                    'requirements. The "Last updated" date will change when we do. We will notify you of material changes '
                    "by posting the updated Terms in the app, sending an email notification, or displaying an in-app "
                    "notification. Your continued use of the Service after changes constitutes acceptance of the updated "
                    "Terms. If you do not agree to the updated Terms, you must stop using the Service and delete your account."
                )
            ),

            LegalSection(
                id="general",
                title="General Provisions",
                body=(
                    "These Terms, together with our Privacy Policy, constitute the entire agreement between you and us. "
                    "If any provision is found unenforceable, the remaining provisions remain in effect. Our failure to "
                    "enforce any right or provision does not constitute a waiver. You may not assign these Terms or your "
                    f"account. {COMPANY_NAME} may assign these Terms without restriction. No agency, partnership, or "
                    "employment relationship is created by these Terms."
                )
            ),

            LegalSection(
                id="contact",
                title="Contact Us",
                body=(
                    f"For questions about these Terms of Service, contact us at {SUPPORT_EMAIL} or visit our website "
                    f"at {WEBSITE}. We aim to respond within 48 hours. For technical support, account issues, or "
                    f"feature requests, please also use {SUPPORT_EMAIL}."
                )
            ),
        ]
    )

