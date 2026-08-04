from app.models import user
from app.models import customers  # noqa: F401  让 Base.metadata 发现 Customer 表
from app.models import experiment  # noqa: F401  让 Base.metadata 发现 Experiment 表
from app.models import prompt_template  # noqa: F401  让 Base.metadata 发现 PromptTemplate 表
from app.models import email_record  # noqa: F401  让 Base.metadata 发现 EmailRecord 表
from app.models import operation_log  # noqa: F401  让 Base.metadata 发现 OperationLog 表
