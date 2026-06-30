# Linear Issue Importer

A simple Python utility to bulk import Issues into **Linear** from **CSV** or **Excel (.xlsx)** files.

The importer automatically:

* ✅ Creates Issues
* ✅ Creates Projects when they do not exist
* ✅ Creates Parent / Sub-Issue relationships
* ✅ Formats User Stories using a Scrum template
* ✅ Converts Acceptance Criteria into Markdown checklists
* ✅ Supports **Dry Run** mode
* ✅ Logs all operations to `import.log`

---

# Features

* Import from **CSV**
* Import from **Excel (.xlsx / .xls)**
* Automatic Project creation
* Parent / Sub-Issue hierarchy
* Scrum-friendly Issue descriptions
* CSV/XLSX validation before import
* Console and file logging
* Dry Run mode
* Environment-based configuration

---

# Project Structure

```text
linear-import/
│
├── importer.py
├── requirements.txt
├── .env
├── issues.csv
├── issues.xlsx
└── import.log
```

---

# Requirements

* Python 3.10+
* Linear Personal API Key

---

# Installation

Clone the repository.

```bash
git clone <repository-url>

cd linear-import
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file.

```env
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxx
TEAM_KEY=LEG
```

| Variable         | Description                         |
| ---------------- | ----------------------------------- |
| `LINEAR_API_KEY` | Linear Personal API Key             |
| `TEAM_KEY`       | Team Key (recommended) or Team Name |

---

# Supported File Formats

The importer supports:

* `.csv`
* `.xlsx`
* `.xls`

Examples:

```bash
python importer.py issues.csv
```

```bash
python importer.py issues.xlsx
```

---

# CSV / Excel Format

The importer expects the following columns.

| Column                   | Required | Description                 |
| ------------------------ | -------- | --------------------------- |
| Title                    | ✅        | Issue title                 |
| Parent                   |          | Parent Issue Title          |
| Priority                 |          | Urgent, High, Medium or Low |
| User Story / Description | ✅        | User Story                  |
| Context                  |          | Business Context            |
| Acceptance Criteria      |          | Acceptance Criteria         |
| Project                  |          | Project Name                |

Example:

| Title          | Parent         | Priority | User Story / Description         | Context           | Acceptance Criteria        | Project         |
| -------------- | -------------- | -------- | -------------------------------- | ----------------- | -------------------------- | --------------- |
| Authentication |                | High     | As a user I want to authenticate | Login is required | Login works | Logout works | Customer Portal |
| Login Screen   | Authentication | Medium   | Create Login Screen              | Frontend          | Screen completed           | Customer Portal |

---

# Acceptance Criteria

Acceptance Criteria may be separated using **pipes**:

```text
Login works|Logout works|JWT returned
```

or multiple lines:

```text
- Login works
- Logout works
- JWT returned
```

Both formats become:

```markdown
- [ ] Login works
- [ ] Logout works
- [ ] JWT returned
```

---

# Generated Issue Description

Each Issue is created using the following template.

```markdown
# User Story

As a user...

---

## Context

Business context...

---

## Acceptance Criteria

- [ ] First criteria
- [ ] Second criteria
```

---

# Automatic Project Creation

If a Project referenced in the import file does not exist, the importer automatically:

1. Creates the Project
2. Associates the Issue with the new Project
3. Writes a warning to the logs

Example:

```text
WARNING | Project 'Customer Portal' did not exist and was created automatically.
```

---

# Parent / Sub-Issues

Parent relationships are resolved using the **Title** column.

Example:

| Title          | Parent         |
| -------------- | -------------- |
| Authentication |                |
| Login Screen   | Authentication |
| Login API      | Authentication |

Result:

```text
Authentication
├── Login Screen
└── Login API
```

> **Important:** Issue titles must be unique within the import file.

---

# Dry Run

Use **Dry Run** to validate the import without creating anything in Linear.

```bash
python importer.py issues.xlsx --dry-run
```

The Dry Run validates:

* Required columns
* Duplicate Titles
* Parent references
* Team existence
* Existing Projects
* Projects that would be created
* Number of Issues
* Parent/Sub-Issue relationships

Example output:

```text
======================================
DRY RUN SUMMARY
======================================

Issues.................... 184
Projects no arquivo....... 12
Projects a criar.......... 2
Relações Parent/Sub....... 91

WARNING
- Customer Portal
- Mobile App

======================================
```

No mutations are executed while running in Dry Run mode.

---

# Logging

Logs are written to both:

* Console
* `import.log`

Example:

```text
INFO | Team encontrado: LEG
INFO | Criando issues...
WARNING | Project 'Customer Portal' não existia e foi criado automaticamente.
INFO | LEG-12 Authentication
INFO | Login Screen -> Authentication
INFO | Importação concluída.
```

---

# Validation

Before importing, the script validates:

* Required columns
* Duplicate Issue Titles
* Invalid Parent references
* File format
* Team configuration

The import stops immediately if validation fails.

---

# Priority Mapping

| CSV    | Linear |
| ------ | ------ |
| Urgent | 1      |
| High   | 2      |
| Medium | 3      |
| Low    | 4      |
| Empty  | 0      |

---

# Usage

Import a CSV:

```bash
python importer.py issues.csv
```

Import an Excel file:

```bash
python importer.py issues.xlsx
```

Validate without importing:

```bash
python importer.py issues.xlsx --dry-run
```

---

# Roadmap

Planned improvements:

* Automatic Initiative creation
* Automatic Cycle (Sprint) assignment
* Labels
* Assignees
* Story Points
* Attachments
* Retry mechanism
* Progress bar
* Summary report
* Parallel imports

---

# License

MIT
