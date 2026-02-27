"""PyClaw CLI - Typer-based command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pyfiglet
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

app = typer.Typer(
    name="pyclaw",
    help="PyClaw - Python personal AI assistant built on LangChain Deep Agents",
    invoke_without_command=True,
)
console = Console()

_GRADIENT = ["bright_cyan", "cyan", "dodger_blue", "blue_violet", "magenta", "bright_magenta"]


def _make_banner(subtitle: str, border_style: str = "bold blue") -> Panel:
    """Build a colorful PyClaw banner panel with gradient text."""
    banner = pyfiglet.figlet_format("PyClaw", font="ansi_shadow")
    text = Text()
    for i, line in enumerate(banner.rstrip().split("\n")):
        text.append(line + "\n", style=f"bold {_GRADIENT[i % len(_GRADIENT)]}")
    text.append(f"\n  {subtitle}", style="dim white")
    return Panel(text, style=border_style, padding=(1, 2))


@app.callback()
def main(
    ctx: typer.Context,
    message: Optional[str] = typer.Option(None, "-m", "--message", help="One-shot message (skip interactive mode)"),
    thread: Optional[str] = typer.Option(None, "-t", "--thread", help="Thread ID for session continuity"),
    model: Optional[str] = typer.Option(None, "--model", help="Override default model (e.g. 'openai:gpt-4o')"),
):
    """PyClaw - Python personal AI assistant built on LangChain Deep Agents."""
    if ctx.invoked_subcommand is not None:
        return

    from pyclaw.config import DEFAULT_CONFIG_PATH, DEFAULT_ENV_PATH, load_config

    # Auto-redirect to onboarding if not set up yet or setup was incomplete
    needs_onboarding = not DEFAULT_CONFIG_PATH.exists()
    if not needs_onboarding:
        # Check if the chosen model needs an API key but .env is missing/empty
        cfg = load_config()
        from pyclaw.models import load_model_registry

        registry = load_model_registry()
        provider_key = cfg.default_model.split(":")[0] if ":" in cfg.default_model else cfg.default_model
        provider_def = registry.get_provider(provider_key)
        needs_api_key = provider_def.needs_api_key if provider_def else provider_key not in ("ollama",)
        if needs_api_key and not DEFAULT_ENV_PATH.exists():
            needs_onboarding = True

    if needs_onboarding:
        console.print("[yellow]PyClaw is not set up yet. Starting onboarding...[/yellow]")
        console.print()
        onboard()
        console.print()

    from pyclaw.agent import create_pyclaw_agent
    from pyclaw.sessions.manager import get_default_thread_id

    config = load_config()
    if model:
        config.default_model = model

    agent_graph, checkpointer = create_pyclaw_agent(config)
    thread_id = thread or get_default_thread_id()

    if message:
        _run_one_shot(agent_graph, thread_id, message)
    else:
        _run_interactive(agent_graph, thread_id)


def _write_env_vars(env_vars: dict[str, str]) -> None:
    """Write key=value pairs to the PyClaw .env file, updating existing keys."""
    from pyclaw.config import DEFAULT_ENV_PATH

    DEFAULT_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_lines: list[str] = []
    if DEFAULT_ENV_PATH.exists():
        existing_lines = DEFAULT_ENV_PATH.read_text(encoding="utf-8").splitlines()

    for env_key, env_value in env_vars.items():
        updated = False
        for i, line in enumerate(existing_lines):
            if line.strip().startswith(f"{env_key}="):
                existing_lines[i] = f"{env_key}={env_value}"
                updated = True
                break
        if not updated:
            existing_lines.append(f"{env_key}={env_value}")

    DEFAULT_ENV_PATH.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")


@app.command()
def onboard():
    """Initialize PyClaw: create config and workspace with template files."""
    from pyclaw.config import (
        DEFAULT_CONFIG_PATH,
        DEFAULT_ENV_PATH,
        PyClawConfig,
        load_config,
        save_config,
    )
    from pyclaw.workspace import init_workspace

    console.print(_make_banner("Python personal AI assistant", "bold blue"))

    # Create config
    if DEFAULT_CONFIG_PATH.exists():
        console.print(f"[yellow]Config already exists at {DEFAULT_CONFIG_PATH}[/yellow]")
        config = load_config()
    else:
        config = PyClawConfig()
        path = save_config(config)
        console.print(f"[green]Created config at {path}[/green]")

    # Initialize workspace
    workspace_path = config.workspace_path
    created = init_workspace(workspace_path)

    if created:
        console.print(f"[green]Initialized workspace at {workspace_path}[/green]")
        for f in created:
            console.print(f"  [dim]Created {f.name}[/dim]")
    else:
        console.print(f"[yellow]Workspace already initialized at {workspace_path}[/yellow]")

    # Interactive two-step model provider selection
    import questionary
    from questionary import Style

    from pyclaw.models import load_model_registry

    console.print()

    custom_style = Style([
        ("qmark", "fg:cyan bold"),
        ("question", "fg:white bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("answer", "fg:green bold"),
    ])

    registry = load_model_registry()

    # Step 1: Pick a provider
    provider_choices = [p.display_name for p in registry.providers]
    provider_choice = questionary.select(
        "Choose your model provider:",
        choices=provider_choices,
        style=custom_style,
    ).ask()

    if provider_choice is None:
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    provider_def = next(p for p in registry.providers if p.display_name == provider_choice)

    # Step 2: Pick a model from that provider
    model_choices = [m.display_name for m in provider_def.models]
    model_choice = questionary.select(
        f"Choose a {provider_def.display_name} model:",
        choices=model_choices,
        style=custom_style,
    ).ask()

    if model_choice is None:
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    model_def = next(m for m in provider_def.models if m.display_name == model_choice)

    # Save as "provider_key:model_id"
    model_id = f"{provider_def.key}:{model_def.id}"
    config.default_model = model_id
    save_config(config)
    console.print(f"[green]Default model set to {model_id}[/green]")

    # Step 3: Ask for API key if needed
    if provider_def.needs_api_key:
        console.print()
        api_key = typer.prompt(f"Enter your {provider_def.display_name} API key", default="", hide_input=False)
        if api_key:
            env_vars = {provider_def.api_key_env: api_key}
            # OpenAI-compatible providers also need OPENAI_API_KEY + OPENAI_BASE_URL
            if provider_def.langchain_provider == "openai" and provider_def.key != "openai":
                env_vars["OPENAI_API_KEY"] = api_key
                if provider_def.base_url:
                    env_vars["OPENAI_BASE_URL"] = provider_def.base_url
            _write_env_vars(env_vars)
            console.print(f"[green]API key saved to {DEFAULT_ENV_PATH}[/green]")
        else:
            console.print(
                f"[yellow]No API key entered. Set {provider_def.api_key_env} in your "
                f"environment or in {DEFAULT_ENV_PATH} later.[/yellow]"
            )

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  - Edit workspace .md files to customize your assistant")
    console.print("  - Run [bold]pyclaw[/bold] to start chatting")


@app.command()
def agent(
    message: Optional[str] = typer.Option(None, "-m", "--message", help="One-shot message (skip interactive mode)"),
    thread: Optional[str] = typer.Option(None, "-t", "--thread", help="Thread ID for session continuity"),
    model: Optional[str] = typer.Option(None, "--model", help="Override default model (e.g. 'openai:gpt-4o')"),
):
    """Start the PyClaw agent (interactive REPL or one-shot)."""
    from pyclaw.agent import create_pyclaw_agent
    from pyclaw.config import load_config
    from pyclaw.sessions.manager import get_default_thread_id

    config = load_config()
    if model:
        config.default_model = model

    agent_graph, checkpointer = create_pyclaw_agent(config)
    thread_id = thread or get_default_thread_id()

    if message:
        # One-shot mode
        _run_one_shot(agent_graph, thread_id, message)
    else:
        # Interactive REPL
        _run_interactive(agent_graph, thread_id)


def _run_one_shot(agent_graph, thread_id: str, message: str):
    """Run a single message through the agent and print the response."""
    config = {"configurable": {"thread_id": thread_id}}

    console.print(f"[dim]Thread: {thread_id}[/dim]")
    console.print()

    for chunk in agent_graph.stream(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        stream_mode="values",
    ):
        if "messages" in chunk:
            last_msg = chunk["messages"][-1]
            # Only print assistant messages
            if hasattr(last_msg, "type") and last_msg.type == "ai" and last_msg.content:
                console.print(last_msg.content)


def _run_interactive(agent_graph, thread_id: str):
    """Run the interactive REPL loop."""
    console.print(_make_banner("Interactive Mode", "bold green"))
    console.print(f"[dim]Thread: {thread_id}[/dim]")
    console.print("[dim]Type 'exit' or 'quit' to leave. Ctrl+C to interrupt.[/dim]")
    console.print()

    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if user_input.strip().lower() in ("exit", "quit", "/exit", "/quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        console.print()

        try:
            for chunk in agent_graph.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
                stream_mode="values",
            ):
                if "messages" in chunk:
                    last_msg = chunk["messages"][-1]
                    if hasattr(last_msg, "type") and last_msg.type == "ai" and last_msg.content:
                        console.print(f"[bold green]PyClaw:[/bold green] {last_msg.content}")
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")

        console.print()


@app.command()
def status():
    """Show PyClaw configuration summary and status."""
    from pyclaw.config import DEFAULT_CONFIG_PATH, load_config

    if not DEFAULT_CONFIG_PATH.exists():
        console.print("[red]PyClaw not configured. Run 'pyclaw onboard' first.[/red]")
        raise typer.Exit(1)

    config = load_config()

    table = Table(title="PyClaw Status", show_header=True)
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    table.add_row("Config", str(DEFAULT_CONFIG_PATH))
    table.add_row("Workspace", str(config.workspace_path))
    table.add_row("Default Model", config.default_model)
    table.add_row("Models Available", str(len(config.model_list)))
    table.add_row("Web Search", f"{'enabled' if config.tools.web_search.enabled else 'disabled'} ({config.tools.web_search.provider})")
    table.add_row("Shell Exec", "enabled" if config.tools.shell_exec.enabled else "disabled")
    table.add_row("Heartbeat", f"{'enabled' if config.heartbeat.enabled else 'disabled'} (every {config.heartbeat.interval_minutes}m)")

    # Channel status
    channels = []
    if config.channels.telegram.enabled:
        channels.append("telegram")
    if config.channels.discord.enabled:
        channels.append("discord")
    if config.channels.slack.enabled:
        channels.append("slack")
    table.add_row("Channels", ", ".join(channels) if channels else "none")

    # Workspace files
    ws = config.workspace_path
    md_files = ["IDENTITY.md", "SOUL.md", "MEMORY.md", "USER.md", "HEARTBEAT.md"]
    existing = [f for f in md_files if (ws / f).exists()]
    table.add_row("Workspace Files", ", ".join(existing) if existing else "none (run onboard)")

    console.print(table)


@app.command()
def cron(
    action: str = typer.Argument("list", help="Action: list, start"),
):
    """Manage the heartbeat/cron scheduler."""
    from pyclaw.config import load_config
    from pyclaw.heartbeat.scheduler import list_heartbeat_tasks, run_heartbeat

    config = load_config()

    if action == "list":
        tasks = list_heartbeat_tasks(config.workspace_path)
        if tasks:
            console.print("[bold]Heartbeat Tasks:[/bold]")
            for task in tasks:
                console.print(f"  - {task}")
        else:
            console.print("[dim]No heartbeat tasks configured.[/dim]")
    elif action == "start":
        if not config.heartbeat.enabled:
            console.print("[yellow]Heartbeat is disabled in config. Enable it first.[/yellow]")
            raise typer.Exit(1)
        console.print(f"[green]Starting heartbeat scheduler (interval: {config.heartbeat.interval_minutes}m)...[/green]")
        run_heartbeat(config)
    else:
        console.print(f"[red]Unknown action: {action}. Use 'list' or 'start'.[/red]")
        raise typer.Exit(1)


@app.command()
def gateway(
    channel: str = typer.Argument(..., help="Channel to start: telegram, discord, slack, all"),
):
    """Start a channel gateway (Telegram, Discord, Slack)."""
    from pyclaw.channels import get_enabled_channels
    from pyclaw.config import load_config

    config = load_config()

    if channel == "all":
        channels = get_enabled_channels(config)
        if not channels:
            console.print("[red]No channels enabled in config.[/red]")
            raise typer.Exit(1)
        console.print(f"[green]Starting {len(channels)} channel(s): {', '.join(channels.keys())}[/green]")
        for name, ch in channels.items():
            console.print(f"  Starting {name}...")
            ch.start()
    else:
        channels = get_enabled_channels(config)
        if channel not in channels:
            console.print(f"[red]Channel '{channel}' is not enabled in config.[/red]")
            raise typer.Exit(1)
        console.print(f"[green]Starting {channel} gateway...[/green]")
        channels[channel].start()


if __name__ == "__main__":
    app()
