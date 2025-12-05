"""Lambda Labs Cloud API client."""
import httpx
from typing import Optional, Dict, Any, List


class LambdaLabsAPIError(Exception):
    """Exception raised for Lambda Labs API errors."""
    pass


class LambdaLabsAPI:
    """Client for interacting with Lambda Labs Cloud API."""

    BASE_URL = "https://cloud.lambdalabs.com/api/v1"

    def __init__(self, api_key: str):
        """Initialize the API client with an API key.

        Args:
            api_key: Lambda Labs Cloud API key
        """
        self.api_key = api_key
        # Lambda Labs requires API key with trailing colon for basic auth
        self.auth = (api_key, "")

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Lambda Labs API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: Optional JSON payload

        Returns:
            Response data as dictionary

        Raises:
            LambdaLabsAPIError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = httpx.request(
                method=method,
                url=url,
                auth=self.auth,
                json=json,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed with status {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg = f"{error_msg}: {error_data['error']}"
            except Exception:
                pass
            raise LambdaLabsAPIError(error_msg) from e
        except httpx.RequestError as e:
            raise LambdaLabsAPIError(f"Network error: {str(e)}") from e

    def list_instances(self) -> Dict[str, Any]:
        """List all running instances.

        Returns:
            Dictionary containing instance data
        """
        return self._request("GET", "/instances")

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get details of a specific instance.

        Args:
            instance_id: The instance ID

        Returns:
            Dictionary containing instance details
        """
        return self._request("GET", f"/instances/{instance_id}")

    def list_instance_types(self) -> Dict[str, Any]:
        """List all available instance types.

        Returns:
            Dictionary containing instance types and their availability
        """
        return self._request("GET", "/instance-types")

    def launch_instance(
        self,
        region_name: str,
        instance_type_name: str,
        ssh_key_names: List[str],
        file_system_names: Optional[List[str]] = None,
        quantity: int = 1,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Launch new instance(s).

        Args:
            region_name: Region to launch in (e.g., "us-west-1")
            instance_type_name: Instance type (e.g., "gpu_1x_a10")
            ssh_key_names: List of SSH key names to add to the instance
            file_system_names: Optional list of file system names to attach
            quantity: Number of instances to launch (default: 1)
            name: Optional name for the instance

        Returns:
            Dictionary containing launch operation result
        """
        payload = {
            "region_name": region_name,
            "instance_type_name": instance_type_name,
            "ssh_key_names": ssh_key_names,
            "quantity": quantity
        }

        if file_system_names:
            payload["file_system_names"] = file_system_names

        if name:
            payload["name"] = name

        return self._request("POST", "/instance-operations/launch", json=payload)

    def terminate_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Terminate instances.

        Args:
            instance_ids: List of instance IDs to terminate

        Returns:
            Dictionary containing termination operation result
        """
        payload = {"instance_ids": instance_ids}
        return self._request("POST", "/instance-operations/terminate", json=payload)

    def restart_instances(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Restart instances.

        Args:
            instance_ids: List of instance IDs to restart

        Returns:
            Dictionary containing restart operation result
        """
        payload = {"instance_ids": instance_ids}
        return self._request("POST", "/instance-operations/restart", json=payload)
