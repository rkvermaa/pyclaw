"""PyClaw CLI - Typer-based command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="pyclaw",
    help="PyClaw - Python personal AI assistant built on LangChain Deep Agents",
    no_args_is_help=True,
)
console = Console()


@app.command()
def onboard():
    """Initialize PyClaw: create config and workspace with template files."""
    from pyclaw.config import (
        DEFAULT_CONFIG_PATH,
        PyClawConfig,
        save_config,
    )
    from pyclaw.workspace import init_workspace

    console.print(Panel("Welcome to PyClaw!", style="bold blue"))

    # Create config
    if DEFAULT_CONFIG_PATH.exists():
        console.print(f"[yellow]Config already exists at {DEFAULT_CONFIG_PATH}[/yellow]")
        config_data = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
        from pyclaw.config import load_config

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

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Edit ~/.pyclaw/config.json to set your preferred model and API keys")
    console.print("  2. Edit workspace .md files to customize your assistant's personality")
    console.print("  3. Run [bold]pyclaw agent[/bold] to start chatting")
    console.print("  4. Run [bold]pyclaw agent -m 'your question'[/bold] for one-shot mode")


@app.command()
def agent(
    message: Optional[str] = typer.Option(None, "-m", "--message", help="One-shot message (skip interactive mode)"),
    thread: Optional[str] = typer.Option(None, "-t", "--thread", help="Thread ID for session continuity"),
    model: Optional[str] = typer.Option(None, "--model", help="Override default model (e.g. 'openai:gpt-4o')"),
):
    """Start the PyClaw agent (interactive REPL or one-shot)."""
    from pyclaw.agent import create_pyclaw_agent
    from pyclaw.config import load_config
    from pyclaw.sessions.manager import get_default_thread_id, new_thread_id

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
    console.print(Panel("PyClaw Interactive Mode", style="bold green"))
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
