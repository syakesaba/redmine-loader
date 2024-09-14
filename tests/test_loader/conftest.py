import httpx
import pytest
import json
import pathlib

thisdir = pathlib.Path(__file__).parent


@pytest.fixture
def mock_client(request):
    case_number = request.param

    def transport(request: httpx.Request) -> httpx.Response:
        basename = pathlib.Path(request.url.path).name
        basedir = thisdir / "issues" / str(case_number)
        try:
            if basename.endswith(".json"):
                with open(basedir / basename) as f:
                    response_json = json.load(f)
                    return httpx.Response(200, json=response_json)
            else:
                with open(basedir / basename) as f:
                    return httpx.Response(200, content=f.read())
        except FileNotFoundError:
            return httpx.Response(404)
        return httpx.Response(500)

    return httpx.Client(transport=httpx.MockTransport(transport))
