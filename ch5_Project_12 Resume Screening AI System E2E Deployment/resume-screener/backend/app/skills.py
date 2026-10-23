"""Skill taxonomy with aliases (spec 4.5: 'JS' == 'JavaScript').

Used for (a) normalising text before embedding, (b) must-have / nice-to-have
skill coverage, (c) matched / missing skills shown to the recruiter.
"""
import re

# canonical -> aliases (canonical itself is always matched)
TAXONOMY: dict[str, list[str]] = {
    # languages
    "python": [], "sql": ["t-sql", "pl/sql", "tsql"], "java": [], "javascript": ["js", "ecmascript"],
    "typescript": [], "scala": [], "c++": ["cpp"], "bash": ["shell scripting"],
    "golang": [],
    # data engineering
    "apache spark": ["spark", "pyspark", "spark structured streaming", "spark streaming"],
    "apache airflow": ["airflow"], "apache kafka": ["kafka", "kafka streams"], "apache flink": ["flink"],
    "hadoop": [], "hive": [], "dbt": ["data build tool"], "snowflake": [], "databricks": [],
    "redshift": ["amazon redshift"], "bigquery": ["big query"], "aws glue": ["glue"], "aws emr": ["emr"],
    "s3": ["amazon s3"], "parquet": [], "delta lake": [],
    "etl/elt": ["etl", "elt", "etl/elt", "etl pipelines", "elt pipelines", "data pipelines", "data pipeline"],
    "data warehousing": ["data warehouse", "data warehouses", "dwh", "warehousing", "cloud data warehouse"],
    "data modeling": ["data modelling", "dimensional modeling", "dimensional modelling"],
    "data quality": ["data validation", "data quality checks"],
    "terraform": ["infrastructure as code", "infrastructure-as-code", "iac"],
    "docker": [], "kubernetes": ["k8s"], "ci/cd": ["cicd", "ci cd"], "git": [], "github": [],
    "nosql": [], "mongodb": ["mongo"], "postgresql": ["postgres"], "mysql": [], "sql server": ["mssql"],
    # cloud
    "aws": ["amazon web services"], "azure": ["microsoft azure"], "gcp": ["google cloud", "google cloud platform"],
    # BI / analytics
    "power bi": ["powerbi", "power-bi"], "tableau": [], "looker": [], "metabase": [], "excel": ["microsoft excel", "ms excel"],
    "power query": [], "power pivot": [], "pivot tables": ["pivot table", "pivots"],
    "google analytics": ["ga4"], "a/b testing": ["ab testing", "a/b test", "a/b tests", "split testing", "experimentation"],
    "hypothesis testing": [], "statistics": ["statistical analysis", "statistical modeling", "statistical modelling"],
    "dashboards": ["dashboard", "dashboarding"], "kpi reporting": ["kpi", "kpis", "kpi dashboards"],
    "data visualization": ["data visualisation", "data viz", "visualization", "visualisation"],
    "cohort analysis": [], "forecasting": ["time series", "time-series"], "jira": [],
    # python data stack
    "pandas": [], "numpy": [], "matplotlib": [], "seaborn": [], "scikit-learn": ["sklearn", "scikit learn"],
    # ML / AI
    "machine learning": ["ml", "predictive analytics", "predictive modeling", "predictive modelling"],
    "deep learning": ["neural networks"], "nlp": ["natural language processing"],
    "computer vision": [], "pytorch": ["torch"], "tensorflow": [], "keras": [],
    "transformers": ["hugging face", "huggingface"], "llm": ["llms", "large language models", "large language model"],
    "rag": ["retrieval augmented generation", "retrieval-augmented generation"], "mlops": ["ml ops"],
    "mlflow": [], "kubeflow": [], "opencv": [], "yolo": [], "langchain": [],
    "vector database": ["vector databases", "faiss", "pinecone", "vector search"],
    # web / misc
    "fastapi": [], "flask": [], "django": [], "react": ["reactjs", "react.js"], "node.js": ["nodejs", "node js"],
    "agile": ["scrum", "agile/scrum"], "rest api": ["rest apis", "restful api", "restful apis"],
}

DISPLAY = {
    "sql": "SQL", "aws": "AWS", "gcp": "GCP", "etl/elt": "ETL/ELT", "nlp": "NLP", "llm": "LLM", "rag": "RAG",
    "dbt": "dbt", "ci/cd": "CI/CD", "a/b testing": "A/B testing", "power bi": "Power BI", "mlops": "MLOps",
    "kpi reporting": "KPI reporting", "s3": "S3", "aws glue": "AWS Glue", "aws emr": "AWS EMR",
    "mysql": "MySQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB", "node.js": "Node.js",
    "javascript": "JavaScript", "typescript": "TypeScript", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn", "numpy": "NumPy", "pandas": "pandas", "opencv": "OpenCV", "yolo": "YOLO",
    "github": "GitHub", "sql server": "SQL Server", "rest api": "REST API", "c++": "C++", "bigquery": "BigQuery",
    "mlflow": "MLflow", "langchain": "LangChain", "fastapi": "FastAPI", "kubeflow": "Kubeflow",
}


def display(skill: str) -> str:
    if skill in DISPLAY:
        return DISPLAY[skill]
    return " ".join(w.capitalize() for w in skill.split(" "))


def _alias_regex(alias: str) -> str:
    parts = re.split(r"[\s\-]+", alias.lower())
    return r"[\s\-]+".join(re.escape(p) for p in parts)


_ALIAS_TO_CANON: dict[str, str] = {}
for canon, aliases in TAXONOMY.items():
    _ALIAS_TO_CANON[canon] = canon
    for a in aliases:
        _ALIAS_TO_CANON.setdefault(a.lower(), canon)

_ORDERED = sorted(_ALIAS_TO_CANON, key=len, reverse=True)
_PATTERN = re.compile(
    r"(?<![a-z0-9+#])(" + "|".join(_alias_regex(a) for a in _ORDERED) + r")(?![a-z0-9+#])", re.I
)


def _canon_of(matched: str) -> str:
    key = re.sub(r"[\s\-]+", " ", matched.lower())
    if key in _ALIAS_TO_CANON:
        return _ALIAS_TO_CANON[key]
    for k, v in _ALIAS_TO_CANON.items():
        if re.sub(r"[\s\-]+", " ", k) == key:
            return v
    return key


def extract_skills(text: str) -> set[str]:
    """Canonical skills found in text (alias aware)."""
    return {_canon_of(m.group(1)) for m in _PATTERN.finditer(text.lower())}


def normalize_aliases(text: str) -> str:
    """Rewrite aliases to their canonical term so 'JS' and 'JavaScript'
    land on the same tokens before embedding."""
    return _PATTERN.sub(lambda m: _canon_of(m.group(1)), text)
