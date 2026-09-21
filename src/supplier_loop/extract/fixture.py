from collections.abc import Mapping

from supplier_loop.extract.schema import ExtractRequest, ExtractResult


class FixtureExtractor:
    def __init__(self, results: Mapping[str, ExtractResult]) -> None:
        self._results = dict(results)
        self.requests: list[ExtractRequest] = []

    def extract(self, request: ExtractRequest) -> ExtractResult:
        self.requests.append(request)
        return self._results[request.email_id]
