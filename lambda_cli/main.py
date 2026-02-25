"""Lambda Labs Cloud CLI main entry point."""
import time
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel
from rich.live import Live

from lambda_cli import config
from lambda_cli.api import LambdaLabsAPI, LambdaLabsAPIError
from lambda_cli.scheduler import InstanceWatcher

app = typer.Typer(
    name="ll",
    help="Lambda Labs Cloud CLI - Manage your GPU instances",
    no_args_is_help=True
)
instances_app = typer.Typer(
    name="instances",
    help="Manage Lambda Labs Cloud instances",
    no_args_is_help=True
)
config_app = typer.Typer(
    name="config",
    help="Manage CLI configuration",
    no_args_is_help=True
)

app.add_typer(instances_app, name="instances")
app.add_typer(config_app, name="config")

console = Console()


def get_api_client() -> LambdaLabsAPI:
    """Get an authenticated API client.

    Returns:
        Configured LambdaLabsAPI client

    Exits:
        If API key is not configured
    """
    try:
        api_key = config.get_api_key()
        return LambdaLabsAPI(api_key)
    except config.ConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


# Config commands
@config_app.command("set-key")
def config_set_key(api_key: str = typer.Argument(..., help="Lambda Labs Cloud API key")):
    """Save your Lambda Labs Cloud API key."""
    try:
        config.save_api_key(api_key)
        console.print("[green]API key saved successfully![/green]")
        console.print(f"Config location: {config.CONFIG_FILE}")
    except config.ConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@config_app.command("show")
def config_show():
    """Show current configuration."""
    try:
        api_key = config.load_api_key()
        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            console.print(f"[green]API Key:[/green] {masked_key}")
            console.print(f"[dim]Config file: {config.CONFIG_FILE}[/dim]")
        else:
            console.print("[yellow]No API key configured[/yellow]")
            console.print("Run: ll config set-key <your-api-key>")
    except config.ConfigError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@config_app.command("clear")
def config_clear():
    """Clear the configuration."""
    try:
        config.clear_config()
        console.print("[green]Configuration cleared successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


# Instance commands
@instances_app.command("ls")
def instances_list():
    """List all running instances."""
    api = get_api_client()

    try:
        response = api.list_instances()
        instances = response.get("data", [])

        if not instances:
            console.print("[yellow]No running instances found[/yellow]")
            return

        table = Table(title="Running Instances", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Instance Type", style="yellow")
        table.add_column("Region", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("IP", style="white")

        for instance in instances:
            table.add_row(
                instance.get("id", "N/A"),
                instance.get("name", "N/A"),
                instance.get("instance_type", {}).get("name", "N/A"),
                instance.get("region", {}).get("name", "N/A"),
                instance.get("status", "N/A"),
                instance.get("ip", "N/A")
            )

        console.print(table)

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("look")
def instances_look(
    available_only: bool = typer.Option(False, "--available", "-a", help="Show only instance types with available capacity")
):
    """List all instance types with specs and availability."""
    api = get_api_client()

    try:
        response = api.list_instance_types()
        instance_types = response.get("data", {})

        if not instance_types:
            console.print("[yellow]No instance types found[/yellow]")
            return

        table = Table(title="Instance Types", show_header=True, header_style="bold magenta")
        table.add_column("Instance Type", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("vCPUs", style="green")
        table.add_column("Memory (GiB)", style="yellow")
        table.add_column("Storage (GiB)", style="blue")
        table.add_column("Price ($/hr)", style="magenta")
        table.add_column("Available Regions", style="green")

        for type_name, type_data in instance_types.items():
            instance_type = type_data.get("instance_type", {})
            regions = type_data.get("regions_with_capacity_available", [])

            # Skip if filtering for available only and no regions available
            if available_only and not regions:
                continue

            specs = instance_type.get("specs", {})
            price = instance_type.get("price_cents_per_hour", 0) / 100

            region_names = ", ".join([r.get("name", "N/A") for r in regions]) if regions else "None"

            table.add_row(
                instance_type.get("name", type_name),
                instance_type.get("description", "N/A"),
                str(specs.get("vcpus", "N/A")),
                str(specs.get("memory_gib", "N/A")),
                str(specs.get("storage_gib", "N/A")),
                f"${price:.2f}",
                region_names
            )

        console.print(table)

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("get")
def instances_get(instance_id: str = typer.Argument(..., help="Instance ID")):
    """Get details of a specific instance."""
    api = get_api_client()

    try:
        response = api.get_instance(instance_id)
        instance = response.get("data", {})

        if not instance:
            console.print(f"[yellow]Instance {instance_id} not found[/yellow]")
            return

        # Create a detailed view
        console.print(Panel.fit(
            f"[bold cyan]Instance Details[/bold cyan]\n\n"
            f"[bold]ID:[/bold] {instance.get('id', 'N/A')}\n"
            f"[bold]Name:[/bold] {instance.get('name', 'N/A')}\n"
            f"[bold]Status:[/bold] {instance.get('status', 'N/A')}\n"
            f"[bold]Instance Type:[/bold] {instance.get('instance_type', {}).get('name', 'N/A')}\n"
            f"[bold]Region:[/bold] {instance.get('region', {}).get('name', 'N/A')}\n"
            f"[bold]IP Address:[/bold] {instance.get('ip', 'N/A')}\n"
            f"[bold]Hostname:[/bold] {instance.get('hostname', 'N/A')}\n"
            f"[bold]SSH Key Names:[/bold] {', '.join(instance.get('ssh_key_names', []))}\n"
            f"[bold]File Systems:[/bold] {', '.join([fs for fs in instance.get('file_system_names', [])])}"
        ))

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("launch")
def instances_launch(
    instance_type: str = typer.Option(..., "--type", "-t", help="Instance type (e.g., gpu_1x_a10)"),
    region: str = typer.Option(..., "--region", "-r", help="Region (e.g., us-west-1)"),
    ssh_keys: List[str] = typer.Option(..., "--ssh-key", "-k", help="SSH key name (can specify multiple times)"),
    file_systems: Optional[List[str]] = typer.Option(None, "--file-system", "-f", help="File system name (can specify multiple times)"),
    quantity: int = typer.Option(1, "--quantity", "-q", help="Number of instances to launch"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for the instance")
):
    """Launch new instance(s)."""
    api = get_api_client()

    try:
        console.print(f"[cyan]Launching {quantity} instance(s) of type {instance_type} in {region}...[/cyan]")

        response = api.launch_instance(
            region_name=region,
            instance_type_name=instance_type,
            ssh_key_names=ssh_keys,
            file_system_names=file_systems,
            quantity=quantity,
            name=name
        )

        if response.get("data", {}).get("instance_ids"):
            instance_ids = response["data"]["instance_ids"]
            console.print(f"[green]Successfully launched {len(instance_ids)} instance(s)![/green]")
            for instance_id in instance_ids:
                console.print(f"  - {instance_id}")
        else:
            console.print("[yellow]Launch request submitted, but no instance IDs returned[/yellow]")
            rprint(response)

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("terminate")
def instances_terminate(
    instance_ids: List[str] = typer.Argument(..., help="Instance ID(s) to terminate"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Terminate instance(s)."""
    api = get_api_client()

    if not yes:
        console.print(f"[yellow]Warning: You are about to terminate {len(instance_ids)} instance(s):[/yellow]")
        for instance_id in instance_ids:
            console.print(f"  - {instance_id}")

        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            console.print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        console.print(f"[cyan]Terminating {len(instance_ids)} instance(s)...[/cyan]")

        response = api.terminate_instances(instance_ids)

        if response.get("data", {}).get("terminated_instances"):
            terminated = response["data"]["terminated_instances"]
            console.print(f"[green]Successfully terminated {len(terminated)} instance(s)![/green]")
            for instance_id in terminated:
                console.print(f"  - {instance_id}")
        else:
            console.print("[yellow]Termination request submitted[/yellow]")
            rprint(response)

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("restart")
def instances_restart(
    instance_ids: List[str] = typer.Argument(..., help="Instance ID(s) to restart")
):
    """Restart instance(s)."""
    api = get_api_client()

    try:
        console.print(f"[cyan]Restarting {len(instance_ids)} instance(s)...[/cyan]")

        response = api.restart_instances(instance_ids)

        if response.get("data", {}).get("restarted_instances"):
            restarted = response["data"]["restarted_instances"]
            console.print(f"[green]Successfully restarted {len(restarted)} instance(s)![/green]")
            for instance_id in restarted:
                console.print(f"  - {instance_id}")
        else:
            console.print("[yellow]Restart request submitted[/yellow]")
            rprint(response)

    except LambdaLabsAPIError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@instances_app.command("watch")
def instances_watch(
    instance_type: str = typer.Option(..., "--type", "-t", help="Instance type (e.g., gpu_1x_a10)"),
    region: str = typer.Option(..., "--region", "-r", help="Region (e.g., us-west-1)"),
    ssh_keys: List[str] = typer.Option(..., "--ssh-key", "-k", help="SSH key name(s)"),
    file_systems: Optional[List[str]] = typer.Option(None, "--file-system", "-f", help="File system name(s)"),
    quantity: int = typer.Option(1, "--quantity", "-q", help="Number of instances to launch"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for the instance"),
    interval: int = typer.Option(120, "--interval", "-i", help="Poll interval in seconds"),
    timeout: int = typer.Option(1440, "--timeout", help="Max wait time in minutes"),
):
    """Watch for instance availability and auto-launch when ready."""
    api = get_api_client()
    watcher = InstanceWatcher(
        api=api,
        instance_type=instance_type,
        region=region,
        ssh_key_names=ssh_keys,
        file_system_names=file_systems,
        quantity=quantity,
        instance_name=name,
    )

    timeout_seconds = timeout * 60
    start_time = time.time()

    console.print(Panel.fit(
        f"[bold cyan]Instance Watcher[/bold cyan]\n\n"
        f"[bold]Type:[/bold] {instance_type}\n"
        f"[bold]Region:[/bold] {region}\n"
        f"[bold]SSH Keys:[/bold] {', '.join(ssh_keys)}\n"
        f"[bold]Interval:[/bold] {interval}s\n"
        f"[bold]Timeout:[/bold] {timeout}m"
    ))

    def build_status_table(status: str, next_poll_in: int = 0) -> Table:
        elapsed = int(time.time() - start_time)
        elapsed_m, elapsed_s = divmod(elapsed, 60)
        elapsed_h, elapsed_m = divmod(elapsed_m, 60)

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="bold")
        table.add_column("Value")
        table.add_row("Status", status)
        table.add_row("Elapsed", f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}")
        table.add_row("Polls", str(watcher.poll_count))
        if next_poll_in > 0:
            table.add_row("Next poll in", f"{next_poll_in}s")
        return table

    try:
        with Live(build_status_table("[yellow]Starting...[/yellow]"), console=console, refresh_per_second=1) as live:
            while True:
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    live.update(build_status_table("[red]Timeout reached[/red]"))
                    console.print(f"\n[red]Timed out after {timeout} minutes[/red]")
                    raise typer.Exit(1)

                live.update(build_status_table("[cyan]Polling...[/cyan]"))
                result = watcher.poll_once()

                if result.error:
                    live.update(build_status_table(f"[red]Error: {result.error}[/red]"))
                elif result.launched:
                    live.update(build_status_table("[green]Launched![/green]"))
                    console.print(f"\n[green]Successfully launched instance(s)![/green]")
                    if result.instance_ids:
                        for iid in result.instance_ids:
                            console.print(f"  - {iid}")
                    return
                else:
                    live.update(build_status_table("[yellow]Not available[/yellow]"))

                # Countdown between polls
                for remaining in range(interval, 0, -1):
                    elapsed = time.time() - start_time
                    if elapsed >= timeout_seconds:
                        break
                    status = f"[red]Error: {result.error}[/red]" if result.error else "[yellow]Waiting...[/yellow]"
                    live.update(build_status_table(status, next_poll_in=remaining))
                    time.sleep(1)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Cancelled after {watcher.poll_count} poll(s)[/yellow]")
        raise typer.Exit(0)


if __name__ == "__main__":
    app()
