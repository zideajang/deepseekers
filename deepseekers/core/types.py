from dataclasses import dataclass
from typing import Optional,Any

@dataclass
class ResponseOrError:
    response: Optional[Any] = None
    error: Optional[Exception] = None

    @staticmethod
    def from_response(response: Any) -> 'ResponseOrError':
        return ResponseOrError(response=response)

    @staticmethod
    def from_error(error: Exception) -> 'ResponseOrError':
        return ResponseOrError(error=error)

    def is_ok(self) -> bool:
        return self.response is not None

    def unwrap(self) -> Any:
        if self.response is None:
            raise ValueError("Cannot unwrap an error.")
        return self.response