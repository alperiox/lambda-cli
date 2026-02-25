"""Instance availability watcher and auto-launcher for Lambda Labs Cloud."""

from dataclasses import dataclass
from lambda_cli.api import LambdaLabsAPI, LambdaLabsAPIError


@dataclass
class PollResult:
    """Result of a single poll iteration."""

    available: bool = False
    launched: bool = False
    instance_ids: list[str] | None = None
    error: str | None = None


class InstanceWatcher:
    """Polls Lambda Labs API for instance availability and auto-launches.

    This is a pure logic class — the caller decides when/how often to call
    poll_once(). The CLI uses a while+sleep loop; the web app uses APScheduler.
    """

    def __init__(
        self,
        api: LambdaLabsAPI,
        instance_type: str,
        region: str,
        ssh_key_names: list[str],
        file_system_names: list[str] | None = None,
        quantity: int = 1,
        instance_name: str | None = None,
    ):
        self.api = api
        self.instance_type = instance_type
        self.region = region
        self.ssh_key_names = ssh_key_names
        self.file_system_names = file_system_names
        self.quantity = quantity
        self.instance_name = instance_name
        self.poll_count = 0

    def check_availability(self) -> bool:
        """Check if instance_type is available in the target region.

        Queries the instance types endpoint and checks whether the target
        region appears in regions_with_capacity_available for our type.
        """
        response = self.api.list_instance_types()
        instance_types = response.get("data", {})

        type_data = instance_types.get(self.instance_type)
        if type_data is None:
            return False

        regions = type_data.get("regions_with_capacity_available", [])
        return any(r.get("name") == self.region for r in regions)

    def attempt_launch(self) -> dict | None:
        """Launch the instance. Returns the API response or None on failure."""
        try:
            response = self.api.launch_instance(
                region_name=self.region,
                instance_type_name=self.instance_type,
                ssh_key_names=self.ssh_key_names,
                file_system_names=self.file_system_names,
                quantity=self.quantity,
                name=self.instance_name,
            )
            return response
        except LambdaLabsAPIError:
            return None

    def poll_once(self) -> PollResult:
        """Single poll iteration: check availability + optional launch.

        Increments poll_count, checks availability, and if available,
        attempts to launch. Returns a PollResult with the outcome.
        """
        self.poll_count += 1

        try:
            available = self.check_availability()
        except LambdaLabsAPIError as e:
            return PollResult(error=str(e))

        if not available:
            return PollResult(available=False)

        result = self.attempt_launch()
        if result is None:
            return PollResult(
                available=True,
                launched=False,
                error="Instance was available but launch failed",
            )

        instance_ids = result.get("data", {}).get("instance_ids", [])
        return PollResult(
            available=True,
            launched=True,
            instance_ids=instance_ids,
        )
