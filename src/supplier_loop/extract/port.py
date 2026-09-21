from typing import Protocol

from supplier_loop.extract.schema import ExtractRequest, ExtractResult


class Extractor(Protocol):
    def extract(self, request: ExtractRequest) -> ExtractResult: ...


class UnimplementedExtractor:
    def extract(self, request: ExtractRequest) -> ExtractResult:
        raise NotImplementedError
