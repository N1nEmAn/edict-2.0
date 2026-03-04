"""Task 模型 — 三省六部任务核心表。

对应当前 tasks_source.json 中的每一条任务记录。
state 对应三省六部流转状态机：
  Taizi → Zhongshu → Menxia → Assigned → Doing → Review → Done
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..db import Base


class TaskState(str, enum.Enum):
    """任务状态枚举 — 映射三省六部流程。"""
    Taizi = "Taizi"           # 太子分拣
    Zhongshu = "Zhongshu"     # 中书省起草
    Menxia = "Menxia"         # 门下省审议
    Assigned = "Assigned"     # 尚书省已将任务派发
    Next = "Next"             # 待执行
    Doing = "Doing"           # 六部执行中
    Review = "Review"         # 审查汇总
    Done = "Done"             # 完成
    Blocked = "Blocked"       # 阻塞
    Cancelled = "Cancelled"   # 取消
    Pending = "Pending"       # 待处理


# 终态集合
TERMINAL_STATES = {TaskState.Done, TaskState.Cancelled}

# 状态流转合法路径
STATE_TRANSITIONS = {
    TaskState.Taizi: {TaskState.Zhongshu, TaskState.Cancelled},
    TaskState.Zhongshu: {TaskState.Menxia, TaskState.Cancelled, TaskState.Blocked},
    TaskState.Menxia: {TaskState.Assigned, TaskState.Zhongshu, TaskState.Cancelled},  # 封驳退回中书
    TaskState.Assigned: {TaskState.Doing, TaskState.Next, TaskState.Cancelled, TaskState.Blocked},
    TaskState.Next: {TaskState.Doing, TaskState.Cancelled},
    TaskState.Doing: {TaskState.Review, TaskState.Done, TaskState.Blocked, TaskState.Cancelled},
    TaskState.Review: {TaskState.Done, TaskState.Doing, TaskState.Cancelled},  # 审查不通过退回
    TaskState.Blocked: {TaskState.Taizi, TaskState.Zhongshu, TaskState.Menxia, TaskState.Assigned, TaskState.Doing},
}

# 状态 → Agent 映射
STATE_AGENT_MAP = {
    TaskState.Taizi: "taizi",
    TaskState.Zhongshu: "zhongshu",
    TaskState.Menxia: "menxia",
    TaskState.Assigned: "shangshu",
    TaskState.Review: "shangshu",
}

# 组织 → Agent 映射（六部）
ORG_AGENT_MAP = {
    "户部": "hubu",
    "礼部": "libu",
    "兵部": "bingbu",
    "刑部": "xingbu",
    "工部": "gongbu",
    "吏部": "libu_hr",
}


class Task(Base):
    """三省六部任务表。"""
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, server_default=None)
    trace_id = Column(String(64), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, server_default="")
    priority = Column(String(10), server_default="中")
    state = Column(String(20), nullable=False, server_default="Taizi")
    assignee_org = Column(String(50), nullable=True)
    creator = Column(String(50), server_default="emperor")
    tags = Column(JSONB, server_default="[]")
    flow_log = Column(JSONB, server_default="[]")
    progress_log = Column(JSONB, server_default="[]")
    todos = Column(JSONB, server_default="[]")
    scheduler = Column(JSONB, nullable=True)
    meta = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=None)
    updated_at = Column(DateTime(timezone=True), server_default=None)

    __table_args__ = (
        Index("ix_tasks_state", "state"),
        Index("ix_tasks_trace_id", "trace_id"),
        Index("ix_tasks_assignee_org", "assignee_org"),
        Index("ix_tasks_created_at", "created_at"),
    )

    def to_dict(self) -> dict:
        """序列化为 API 响应格式。"""
        return {
            "task_id": str(self.task_id) if self.task_id else "",
            "trace_id": self.trace_id or "",
            "title": self.title,
            "description": self.description or "",
            "priority": self.priority or "中",
            "state": self.state or "Taizi",
            "assignee_org": self.assignee_org,
            "creator": self.creator or "emperor",
            "tags": self.tags or [],
            "flow_log": self.flow_log or [],
            "progress_log": self.progress_log or [],
            "todos": self.todos or [],
            "scheduler": self.scheduler or {},
            "meta": self.meta or {},
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
