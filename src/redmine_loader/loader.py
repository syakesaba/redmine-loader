#!/usr/bin/env python3
# encoding: utf-8

import io
from typing import Any, AsyncGenerator, Generator, List, Dict, Optional

from pydantic import AnyUrl
import httpx
from langchain_core.documents import Document
from langchain.document_loaders.base import BaseLoader
from langchain_unstructured import UnstructuredLoader

from .models import Attachment, Comment, Issue


class RedmineLoader(BaseLoader):
    """Redmine Issue Document Loader

    :param redmine_url: Redmine URL
    :type redmine_url: AnyUrl
    :param api_key: Redmine API Key
    :type api_key: Optional[str]
    :param issue_ids: Redmine issue id to load leave it blank if need all.
    :type issue_ids: List[int]
    :param include_comments: Whether include issue notes to Document.
    :type include_comments: Optional[bool]
    :param include_attachments: Whether include issue attachments to Document.
    :type include_attachments: Optional[bool]
    :param attachment_maxcharsize: Document length to read per an attachment.
    :type attachment_maxcharsize: Optional[int]
    :param *args: args for httpx client
    :type *args: Any
    :param **kwargs: kwargs for httpx client
    :type **kwargs: Any
    """

    def __init__(
        self,
        redmine_url: AnyUrl,
        api_key: Optional[str] = "",
        issue_ids: List[int] = [],
        include_comments: Optional[bool] = False,
        include_attachments: Optional[bool] = False,
        attachment_maxcharsize: Optional[int] = 100000,
        *keys: Any,
        **kwargs: Any,
    ):
        self.async_client = httpx.AsyncClient(*keys, **kwargs)
        self.client = httpx.Client(*keys, **kwargs)
        self._redmine_url = redmine_url
        self._api_key = api_key
        self._issue_ids = issue_ids
        self._include_comments = include_comments
        self._include_attachments = include_attachments
        self._attachment_maxcharsize = attachment_maxcharsize

    def lazy_load(self) -> Generator[Document, None, None]:
        """Get Issue Document

        :return: the Documents
        :rtype: Generator[Document, None, None]
        """
        for issue in self.fetch_issues():
            llm_text = self.format_issue_description(issue)
            yield Document(
                page_content=llm_text.strip(),
                metadata={
                    "id": issue.id,
                    "subject": issue.subject,
                },
            )

    async def alazy_load(self) -> AsyncGenerator[Document, None]:
        """Get Issue Document asynchronously

        :return: the Documents
        :rtype: AsyncGenerator[Document, None]
        """
        async for issue in self.fetch_issues_async():
            llm_text = self.format_issue_description(issue)
            yield Document(
                page_content=llm_text.strip(),
                metadata={
                    "id": issue.id,
                    "subject": issue.subject,
                },
            )

    @property
    def headers(self) -> dict[str, str]:
        """Get required http headers to request Redmine API.

        :return: Request Headers
        :rtype: dict[str, str]
        """
        return {
            "X-Redmine-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    @property
    def issues_params(self) -> dict[str, str]:
        """Get required http params to request Redmine API.
        see: https://www.redmine.org/projects/redmine/wiki/Rest_Issues

        :return: Request Params
        :rtype: dict[str, str]
        """
        params = {"status_id": "*"}  # not only opened but also closed
        if self._issue_ids:
            params["issue_id"] = ",".join([str(s) for s in self._issue_ids])
        includes = []
        if self._include_attachments:
            includes.append("attachments")
        if includes != []:
            params["include"] = ",".join(includes)
        return params

    @property
    def issue_params(self) -> dict[str, str]:
        """Get required http params to request Redmine API.
        see: https://www.redmine.org/projects/redmine/wiki/Rest_IssueJournals

        :return: Request Params
        :rtype: dict[str, str]
        """
        params = {}
        includes = []
        if self._include_comments:
            includes.append("journals")
        if includes != []:
            params["include"] = ",".join(includes)
        return params

    def fetch_issues(self) -> Generator[Issue, None, None]:
        """Fetch issues

        :return: Issues
        :rtype: Generator[Issue, None, None]
        :raises Exception: HTTPStatusError if response was invalid.
        """
        response = self.client.get(
            f"{self._redmine_url}/issues.json",
            headers=self.headers,
            params=self.issues_params,
        )
        response.raise_for_status()
        issues_data: Dict = response.json()
        issue_data: List
        for issue_data in issues_data.get("issues", []):
            issue = Issue(**issue_data, attachments_=[], comments_=[])
            if self._include_attachments:
                issue.attachments_ = self._fetch_attachments(issue_data)
            if self._include_comments:
                issue.comments_ = self._fetch_comments(issue)
            yield issue

    async def fetch_issues_async(self) -> AsyncGenerator[Issue, None]:
        """Fetch issues asynchronously.

        :return: Issues
        :rtype: AsyncGenerator[Issue, None]
        :raises Exception: HTTPStatusError if response was invalid.
        """
        response = await self.async_client.get(
            f"{self._redmine_url}/issues.json",
            headers=self.headers,
            params=self.issues_params,
        )
        response.raise_for_status()
        issues_data: Dict = response.json()
        issue_data: List
        for issue_data in issues_data.get("issues", []):
            attachments = []
            if self._include_attachments:
                attachments = [
                    attachment
                    async for attachment in self._fetch_attachments_async(issue_data)
                ]
            issue = Issue(**issue_data, attachments_=attachments)
            if self._include_comments:
                issue.comments_ = [c async for c in self._fetch_comments_async(issue)]
            yield issue

    def _fetch_comments(self, issue: Issue) -> Generator[Comment, None, None]:
        """Fetch comments of an issue

        :param issue_id: Issue ID
        :type issue_id: int
        :return: List of comments
        :rtype: Generator[Comment]
        :raises Exception: HTTPStatusError if response from Redmine was invalid.
        """
        response = self.client.get(
            f"{self._redmine_url}/issues/{issue.id}.json",
            headers=self.headers,
            params=self.issue_params,
        )
        response.raise_for_status()
        issue_data: Dict = response.json()
        journals_data: List[Dict] = issue_data.get("issue", {}).get("journals", [])
        for journal_data in journals_data:
            who = journal_data.get("user", {}).get("name", "Anonymous")
            yield Comment(**journal_data, who_=who)

    async def _fetch_comments_async(
        self, issue: Issue
    ) -> AsyncGenerator[Comment, None]:
        """Fetch comments of an issue asynchronously.

        :param issue: The issue object
        :type issue: Issue
        :return: List of comments
        :rtype: AsyncGenerator[Comment, None]
        :raises Exception: HTTPStatusError if response from Redmine was invalid.
        """
        response = await self.async_client.get(
            f"{self._redmine_url}/issues/{issue.id}.json",
            headers=self.headers,
            params=self.issue_params,
        )
        response.raise_for_status()
        issue_data: Dict = response.json()
        journals_data: List[Dict] = issue_data.get("issue", {}).get("journals", [])
        for journal_data in journals_data:
            who = journal_data.get("user", {}).get("name", "Anonymous")
            yield Comment(**journal_data, who_=who)

    def _fetch_attachments(
        self,
        issue_data: Dict,
    ) -> Generator[Attachment, None, None]:
        """Fetch attachments of an issue

        :param issue_data: issue data
        :type issue_data: Dict
        :return: List of Attachment
        :rtype: Generator[Attachment, None, None]
        """
        attachments_data: List[Dict] = issue_data.get("attachments", [])
        for attachment_data in attachments_data:
            attachment = Attachment(**attachment_data)
            attachment.documents_ = [
                doc for doc in self.__process_attachment(attachment)
            ]
            yield attachment

    async def _fetch_attachments_async(
        self,
        issue_data: Dict,
    ) -> AsyncGenerator[Attachment, None]:
        """Fetch attachments of an issue asynchronously.

        :param issue_data: issue data
        :type issue_data: Dict
        :return: List of Attachment
        :rtype: Generator[Attachment, None, None]
        """
        attachments_data: List[Dict] = issue_data.get("attachments", [])
        for attachment_data in attachments_data:
            attachment = Attachment(**attachment_data)
            attachment.documents_ = [
                doc async for doc in self.__process_attachment_async(attachment)
            ]
            yield attachment

    def __process_attachment(
        self, attachment: Attachment
    ) -> Generator[Document, Any, Any]:
        """Process an attachment and return a list of documents.

        :param attachment: Attachment of an issue
        :type attachment: Attachment
        :return: List of Document
        :rtype: List[Document]
        """
        response = self.client.get(str(attachment.content_url))
        response.raise_for_status()
        fp = io.BytesIO(response.content)
        attachment_loader = UnstructuredLoader(
            file=fp,
            metadata_filename=attachment.filename,
            chunking_strategy="basic",
            max_characters=self._attachment_maxcharsize,
        )
        docs = attachment_loader.load()
        for document in docs:
            document.metadata["source"] = attachment.content_url
            yield document

    async def __process_attachment_async(
        self, attachment: Attachment
    ) -> AsyncGenerator[Document, Any]:
        """Process an attachment asynchronously and return a list of documents.

        :param attachment: Attachment of an issue
        :type attachment: Attachment
        :return: List of Document
        :rtype: AsyncGenerator[Document, Any]
        """
        response = await self.async_client.get(str(attachment.content_url))
        response.raise_for_status()
        fp = io.BytesIO(response.read())
        attachment_loader = UnstructuredLoader(
            file=fp,
            metadata_filename=attachment.filename,
            chunking_strategy="basic",
            max_characters=self._attachment_maxcharsize,
        )
        docs = await attachment_loader.aload()
        for document in docs:
            document.metadata["source"] = attachment.content_url
            yield document

    def format_issue_description(
        self,
        issue: Issue,
    ) -> str:
        """Format the description of an issue.

        :::

        :param issue: the issue
        :type issue: Issue
        :return: Formatted description of an issue
        :rtype: str
        """
        description = f"**Subject**:\n{issue.subject}\n\n"
        description += f"**Description**:\n{issue.description}\n\n"
        if self._include_comments:
            description += "**Comments**:\n"
            for comment in issue.comments_:
                if comment.notes:
                    description += (
                        f"""\n'{comment.who_}' said:\n```{comment.notes}```\n"""
                    )
            description += "\n\n"
        if self._include_attachments:
            description += "**Attachments**:\n"
            for attachment in issue.attachments_:
                description += f"{attachment.filename} instructs:\n"
                for document in attachment.documents_:
                    description += f"```{document.page_content}```"
                    description += "\n"
        return description.strip()


if __name__ == "__main__":
    loader = RedmineLoader(
        api_key="",
        redmine_url="https://www.redmine.org/",
        issue_ids=[
            1,
        ],
        include_comments=True,
        include_attachments=True,
        attachment_maxcharsize=100000,
    )

    for doc in loader.load():
        print(doc.metadata)
        print(doc.page_content)

    for doc in loader.lazy_load():
        print(doc.metadata)
        print(doc.page_content)
