#!/usr/bin/env python3
# encoding: utf-8

from typing import List, Optional, Annotated

from pydantic import BaseModel, ConfigDict, Field, AnyUrl
from langchain_core.documents import Document


class Attachment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int = Field(..., description="Attachment ID")
    filename: str = Field(..., description="Attachment filename")
    content_url: AnyUrl = Field(..., description="URL to attachment content")
    content_type: str | None = Field(..., description="Attachment ContentType")
    documents_: Optional[List[Document]] = Annotated[
        List[Document], Field(..., description="Documents of an attachment")
    ]


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int = Field(..., description="Comment ID")
    notes: str = Field(..., description="Comment text")
    who_: str = Field(..., description="Who Comment")


class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int = Field(..., description="Issue ID")
    subject: str = Field(..., description="Issue subject")
    description: str = Field(..., description="Issue description")
    attachments_: Optional[List[Attachment]] = Annotated[
        List[Attachment], Field(..., description="Issue attachments")
    ]
    comments_: Optional[List[Comment]] = Annotated[
        List[Comment], Field(..., description="Issue attachments")
    ]
