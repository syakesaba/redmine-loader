[![Python package](https://github.com/syakesaba/redmine-loader/actions/workflows/python-package.yml/badge.svg)](https://github.com/syakesaba/redmine-loader/actions/workflows/python-package.yml)
[![Upload Python Package](https://github.com/syakesaba/redmine-loader/actions/workflows/python-publish.yml/badge.svg)](https://github.com/syakesaba/redmine-loader/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/github/syakesaba/redmine-loader/graph/badge.svg?token=HTRTEEOOT9)](https://codecov.io/github/syakesaba/redmine-loader)
![GitHub License](https://img.shields.io/github/license/syakesaba/redmine-loader)

redmine-loader
=====
Document Loader for bitnami Redmine.
Crawl Redmine Issues using WebAPI and gather issue subject, description, comments, attachments.
Attachments are parsed with [unstructured.io](https://unstructured.io/) .

Usage
=====

```python
from redmine_loader import RedmineLoader
loader = RedmineLoader(
    api_key="",
    redmine_url="https://www.redmine.org/",
    issue_ids=[1, 2],
    include_comments=True,
    include_attachments=True,
    attachment_maxcharsize=1000,
)
for doc in loader.load():
    print(doc)
```


Build
=====
```sh
poetry build
```

Install
=====
```sh
poetry install
```

License
=====
MIT