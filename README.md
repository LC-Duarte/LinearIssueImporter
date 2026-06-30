# Linear Issue Importer

A simple Python utility to bulk import Issues into Linear from a CSV file.

The importer automatically:

- ✅ Creates Issues
- ✅ Creates Projects if they do not exist
- ✅ Creates Parent / Sub-Issue relationships
- ✅ Converts User Stories into a standardized Markdown description
- ✅ Converts Acceptance Criteria into Markdown checklists
- ✅ Logs the entire import process to `import.log`

---

# Features

- Bulk import from CSV
- Automatic Project creation
- Parent / Sub-Issue hierarchy
- Scrum-friendly Issue template
- Project cache for improved performance
- CSV validation before import
- Console and file logging
- Simple configuration using `.env`

---

# Requirements

- Python 3.10+
- Linear API Key
- Team Key (or Team Name)

---

# Installation

Clone the repository.

```bash
git clone <repository-url>

cd linear-import
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file in the project root.

```env
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxx
TEAM_KEY=LEG
```

Where:

| Variable | Description |
|-----------|-------------|
| LINEAR_API_KEY | Personal API Key generated in Linear |
| TEAM_KEY | Team Key (recommended) or Team Name |

---

# CSV Format

The importer expects the following columns.

| Column | Required | Description |
|---------|----------|-------------|
| Title | Yes | Issue title |
| Parent | No | Parent Issue Title |
| Priority | No | Urgent, High, Medium, Low |
| User Story / Description | Yes | User Story |
| Context | No | Business Context |
| Acceptance Criteria | No | Acceptance Criteria |
| Project | No | Project name |

Example:

| Title | Parent | Priority | User Story / Description | Context | Acceptance Criteria | Project |
|--------|---------|----------|--------------------------|----------|---------------------|----------|
| Authentication | | High | As a user I want to authenticate | Login is required | Login works \| Logout works | Customer Portal |
| Login Screen | Authentication | Medium | Create Login Screen | Frontend | Screen completed | Customer Portal |

---

# Acceptance Criteria

Acceptance Criteria can be separated using either:

## Pipe

```text
Login works|Logout works|JWT returned
```

or multiple lines

```text
- Login works
- Logout works
- JWT returned
```

Both will be converted into

```markdown
- [ ] Login works
- [ ] Logout works
- [ ] JWT returned
```

---

# Generated Issue Description

Each Issue is automatically formatted using the following template.

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

# Running

Default CSV:

```bash
python importer.py
```

Custom CSV:

```bash
python importer.py my_backlog.csv
```

---

# Automatic Project Creation

If a Project referenced in the CSV does not exist, the importer will:

1. Create the Project
2. Associate the Issue with the new Project
3. Log a warning

Example:

```text
WARNING | Project 'Customer Portal' did not exist and was created automatically.
```

---

# Parent / Sub-Issues

Parent Issues are linked using the **Title** column.

Example:

| Title | Parent |
|--------|---------|
| Authentication | |
| Login Screen | Authentication |
| Login API | Authentication |

Results in

```
Authentication
├── Login Screen
└── Login API
```

**Important**

Issue titles **must be unique**.

---

# Logging

The importer writes logs to:

```
import.log
```

Example:

```text
INFO | Team found: LEG
INFO | Creating Issues...
INFO | LEG-12 Authentication
WARNING | Project 'Customer Portal' did not exist and was created automatically.
INFO | Login Screen -> Authentication
INFO | Import completed.
```

---

# Validation

Before importing, the script validates:

- Required columns
- Duplicate Issue Titles
- Invalid Parent references

The import will stop if validation fails.

---

# Priority Mapping

| CSV | Linear |
|------|--------|
| Urgent | 1 |
| High | 2 |
| Medium | 3 |
| Low | 4 |
| Empty | 0 |

---

# Future Improvements

Planned features:

- Dry Run (`--dry-run`)
- Automatic Initiative creation
- Automatic Cycle (Sprint) assignment
- Labels
- Assignees
- Story Points
- Attachments
- Retry mechanism
- Progress bar
- Summary report
- Parallel imports

---

# License

MIT