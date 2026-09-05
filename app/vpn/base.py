from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class VPNProviderError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class VPNProvider(ABC):
    name = "base"

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def create_account(self, username: str, password: str) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_account(self, account_id: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def disable_account(self, account_id: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def enable_account(self, account_id: int) -> Dict[str, Any]: ...

    @abstractmethod
    async def delete_account(self, account_id: int) -> None: ...

    @abstractmethod
    async def get_vless_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_wireguard_config(self, account_id: int, server_id: Optional[int] = None) -> Dict[str, Any]: ...

    @abstractmethod
    async def get_openvpn_config(self, username: str, password: str, server_id: Optional[int] = None, port_id: Optional[int] = None) -> Dict[str, Any]: ...
