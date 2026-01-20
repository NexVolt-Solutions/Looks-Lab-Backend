import os

# Base folder where domain modules will be created
BASE_DIR = os.path.join("app", "ai")

# Domains you want to scaffold
VALID_DOMAINS = {
    "skincare",
    "hair care",
    "fashion",
    "workout",
    "quit porn",
    "diet",
    "height",
    "facial",
}

# Files to create inside each domain folder
FILES = {
    "__init__.py": "# Package init for {domain}\n",
    "prompts.py": "# Prompts for {domain}\n\n{domain_upper}_PROMPTS = {{}}\n",
    "processor.py": (
        "# Processor for {domain}\n\n"
        "def process_{domain_clean}_answers(answers: dict) -> dict:\n"
        "    # TODO: implement domain-specific logic\n"
        "    return {{\"message\": f\"Processed answers for {domain}\"}}\n"
    ),
    "config.py": "# Config for {domain}\n\nDOMAIN_NAME = \"{domain}\"\n",
}

def normalize_name(name: str) -> str:
    """Convert domain name to a valid folder name (snake_case)."""
    return name.lower().replace(" ", "_")

def scaffold_domains():
    os.makedirs(BASE_DIR, exist_ok=True)

    for domain in VALID_DOMAINS:
        folder_name = normalize_name(domain)
        folder_path = os.path.join(BASE_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        for filename, template in FILES.items():
            file_path = os.path.join(folder_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(template.format(
                        domain=domain,
                        domain_upper=domain.upper().replace(" ", "_"),
                        domain_clean=folder_name
                    ))
        print(f" Created module for domain: {domain} → {folder_path}")

if __name__ == "__main__":
    scaffold_domains()

