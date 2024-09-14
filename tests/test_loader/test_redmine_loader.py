#!/usr/bin/env python3
# encoding: utf-8

import pytest
from redmine_loader import RedmineLoader


def test_init():
    _ = RedmineLoader(
        redmine_url="http://issues.com",
        api_key="1234567890",
        issue_ids=[
            1234567890,
        ],
        include_comments=True,
        include_attachments=True,
        attachment_maxcharsize=12345,
    )

    _ = RedmineLoader(
        redmine_url="http://issues.com",
    )

    # redmine_url is required
    with pytest.raises(Exception):
        _ = RedmineLoader(
            api_key="1234567890",
            issue_ids=[
                1234567890,
            ],
            include_comments=True,
            include_attachments=True,
            attachment_maxcharsize=12345,
        )

    # valid extra arguments: proxy for httpx
    loader = RedmineLoader(
        redmine_url="http://issues.com", proxy="http://proxy.com:8080/"
    )
    assert isinstance(loader, RedmineLoader)
    asset = loader.__dict__
    assert asset["_redmine_url"] == "http://issues.com"

    # invalid extra arguments: http_proxy for httpx
    with pytest.raises(Exception):
        _ = RedmineLoader(
            redmine_url="http://issues.com", http_proxy="http://proxy.com:8080/"
        )


# @pytest.mark.parametrize(
#     "mock_client",
#     [
#         1,
#     ],
#     indirect=True,
# )
# def test_init(mock_client):
#     loader = RedmineLoader(
#         redmine_url="http://issues.com", include_attachments=True, include_comments=True
#     )
#     loader.client = mock_client
#     # loader.load()
