import argparse
import logging
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
TEAM_KEY = os.getenv("TEAM_KEY") or os.getenv("TEAM_NAME")

GRAPHQL_URL = "https://api.linear.app/graphql"

HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}

PRIORITY_MAP = {
    "": 0,
    "no priority": 0,
    "none": 0,
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("import.log", mode="a", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


def graphql(query, variables=None):
    """Executa uma query ou mutation GraphQL na API do Linear."""
    response = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()

    if "errors" in result:
        raise Exception(result["errors"])

    return result["data"]


def clean(value):
    """Normaliza valores vindos do CSV/XLSX."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_input_file(file_path):
    """Carrega arquivo .csv, .xlsx ou .xls usando pandas."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    extension = path.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(path).fillna("")

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(path).fillna("")

    raise ValueError("Formato não suportado. Use .csv, .xlsx ou .xls")


def get_team_id():
    """Busca o ID do Team no Linear usando TEAM_KEY ou TEAM_NAME do .env."""
    query = """
    query {
      teams {
        nodes {
          id
          key
          name
        }
      }
    }
    """

    teams = graphql(query)["teams"]["nodes"]

    for team in teams:
        if (
            team["key"].upper() == TEAM_KEY.upper()
            or team["name"].lower() == TEAM_KEY.lower()
        ):
            logger.info(f"Team encontrado: {team['name']} ({team['key']})")
            return team["id"]

    logger.error("Times encontrados no workspace:")
    for team in teams:
        logger.error(f"- Name: {team['name']} | Key: {team['key']}")

    raise Exception(f"Team '{TEAM_KEY}' não encontrado.")


def get_projects():
    """Carrega todos os Projects existentes no workspace."""
    query = """
    query {
      projects(first: 250) {
        nodes {
          id
          name
        }
      }
    }
    """

    projects = graphql(query)["projects"]["nodes"]

    return {clean(project["name"]).lower(): project["id"] for project in projects}


def create_project(team_id, project_name, dry_run=False):
    """Cria um Project no Linear ou simula a criação em dry-run."""
    if dry_run:
        logger.warning(f"[DRY RUN] Project '{project_name}' seria criado.")
        return f"dry-project-{project_name}"

    mutation = """
    mutation CreateProject($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project {
          id
          name
        }
      }
    }
    """

    variables = {
        "input": {
            "teamIds": [team_id],
            "name": project_name,
        }
    }

    data = graphql(mutation, variables)
    project = data["projectCreate"]["project"]

    logger.warning(
        f"Project '{project['name']}' não existia e foi criado automaticamente."
    )

    return project["id"]


def get_or_create_project_id(projects, team_id, project_name, dry_run=False):
    """Retorna ID do Project existente ou cria/simula um novo Project."""
    project_name = clean(project_name)

    if not project_name:
        return None

    project_key = project_name.lower()

    if project_key in projects:
        return projects[project_key]

    project_id = create_project(team_id, project_name, dry_run=dry_run)
    projects[project_key] = project_id

    return project_id


def build_acceptance_criteria(text):
    """Converte Acceptance Criteria para checklist Markdown."""
    text = clean(text)

    if not text:
        return ""

    text = text.replace("\r", "")

    if "|" in text:
        items = [item.strip() for item in text.split("|") if item.strip()]
    else:
        items = [line.strip() for line in text.split("\n") if line.strip()]

    cleaned_items = []

    for item in items:
        item = item.strip()
        item = item.removeprefix("-").strip()
        item = item.removeprefix("[ ]").strip()
        item = item.removeprefix("[x]").strip()
        cleaned_items.append(item)

    return "\n".join(f"- [ ] {item}" for item in cleaned_items if item)


def build_description(row):
    """Monta a descrição da Issue no padrão Scrum."""
    user_story = clean(row.get("User Story / Description"))
    context = clean(row.get("Context"))
    acceptance = build_acceptance_criteria(row.get("Acceptance Criteria"))

    return f"""# User Story

{user_story}

---

## Context

{context}

---

## Acceptance Criteria

{acceptance}
"""


def priority_value(priority):
    """Converte prioridade textual para valor aceito pelo Linear."""
    return PRIORITY_MAP.get(clean(priority).lower(), 0)


def create_issue(team_id, project_id, row, dry_run=False, index=0):
    """Cria uma Issue no Linear ou simula a criação em dry-run."""
    title = clean(row.get("Title"))

    if dry_run:
        logger.info(f"[DRY RUN] Issue '{title}' seria criada.")
        return {
            "id": f"dry-issue-{index}",
            "identifier": f"DRY-{index}",
            "title": title,
        }

    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
        }
      }
    }
    """

    input_data = {
        "teamId": team_id,
        "title": title,
        "description": build_description(row),
        "priority": priority_value(row.get("Priority")),
    }

    if project_id:
        input_data["projectId"] = project_id

    data = graphql(mutation, {"input": input_data})

    return data["issueCreate"]["issue"]


def set_parent(issue_id, parent_id, dry_run=False, title="", parent_title=""):
    """Define uma Issue como sub-issue de outra ou simula em dry-run."""
    if dry_run:
        logger.info(f"[DRY RUN] '{title}' seria sub-issue de '{parent_title}'.")
        return

    mutation = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
      }
    }
    """

    graphql(
        mutation,
        {
            "id": issue_id,
            "input": {"parentId": parent_id},
        },
    )


def validate_file(df):
    """Valida colunas obrigatórias, títulos duplicados e parents inválidos."""
    required_columns = [
        "Title",
        "Priority",
        "User Story / Description",
        "Context",
        "Acceptance Criteria",
        "Project",
        "Parent",
    ]

    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        raise Exception(f"Colunas faltando no arquivo: {', '.join(missing)}")

    titles = [clean(title) for title in df["Title"]]

    duplicated_titles = sorted(
        {title for title in titles if title and titles.count(title) > 1}
    )

    if duplicated_titles:
        raise Exception(
            "Existem títulos duplicados no arquivo. Como o Parent usa o Title, "
            f"os títulos precisam ser únicos: {', '.join(duplicated_titles)}"
        )

    title_set = set(titles)

    for _, row in df.iterrows():
        parent = clean(row.get("Parent"))

        if parent and parent not in title_set:
            raise Exception(
                f"Parent '{parent}' não encontrado para a issue "
                f"'{clean(row.get('Title'))}'."
            )


def print_dry_run_summary(df, projects):
    """Exibe um resumo do que seria importado no modo dry-run."""
    project_names = sorted(
        {clean(project) for project in df["Project"] if clean(project)}
    )

    projects_to_create = [
        project for project in project_names if project.lower() not in projects
    ]

    parent_relations = sum(1 for _, row in df.iterrows() if clean(row.get("Parent")))

    logger.info("======================================")
    logger.info("DRY RUN SUMMARY")
    logger.info("======================================")
    logger.info(f"Issues.................... {len(df)}")
    logger.info(f"Projects no arquivo....... {len(project_names)}")
    logger.info(f"Projects a criar.......... {len(projects_to_create)}")
    logger.info(f"Relações Parent/Sub....... {parent_relations}")

    if projects_to_create:
        logger.warning("Projects que seriam criados:")
        for project in projects_to_create:
            logger.warning(f"- {project}")

    logger.info("======================================")


def parse_args():
    """Lê argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Importador de issues para o Linear.")

    parser.add_argument(
        "input_file",
        nargs="?",
        default="issues.csv",
        help="Arquivo .csv, .xlsx ou .xls com as issues.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida e simula a importação sem criar nada no Linear.",
    )

    return parser.parse_args()


def main():
    """Fluxo principal do importador."""
    args = parse_args()

    if not LINEAR_API_KEY:
        raise Exception("LINEAR_API_KEY não encontrado no .env")

    if not TEAM_KEY:
        raise Exception("TEAM_KEY ou TEAM_NAME não encontrado no .env")

    if args.dry_run:
        logger.warning("Executando em modo DRY RUN. Nada será criado no Linear.")

    logger.info(f"Lendo arquivo: {args.input_file}")

    df = load_input_file(args.input_file)
    validate_file(df)

    team_id = get_team_id()
    projects = get_projects()

    if args.dry_run:
        print_dry_run_summary(df, projects)

    created_by_title = {}

    logger.info("Criando issues...")

    for index, (_, row) in enumerate(df.iterrows(), start=1):
        title = clean(row.get("Title"))
        project_name = clean(row.get("Project"))

        project_id = get_or_create_project_id(
            projects=projects,
            team_id=team_id,
            project_name=project_name,
            dry_run=args.dry_run,
        )

        issue = create_issue(
            team_id=team_id,
            project_id=project_id,
            row=row,
            dry_run=args.dry_run,
            index=index,
        )

        created_by_title[title] = issue["id"]

        logger.info(f"✔ {issue['identifier']} - {issue['title']}")

    logger.info("Criando relações Parent/Sub-issue...")

    for _, row in df.iterrows():
        title = clean(row.get("Title"))
        parent_title = clean(row.get("Parent"))

        if not parent_title:
            continue

        set_parent(
            issue_id=created_by_title[title],
            parent_id=created_by_title[parent_title],
            dry_run=args.dry_run,
            title=title,
            parent_title=parent_title,
        )

        logger.info(f"↳ {title} -> {parent_title}")

    logger.info("Importação concluída.")
    logger.info(f"Total de issues processadas: {len(created_by_title)}")


if __name__ == "__main__":
    main()