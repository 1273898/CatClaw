"""CLI entry point for PrivateClaw."""

import asyncio
import sys
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from privateclaw.config.settings import Settings, get_settings
from privateclaw.core.agent.agent import PrivateClawAgent
from privateclaw.core.llm.factory import LLMFactory
from privateclaw.core.memory.manager import MemoryManager
from privateclaw.core.tools.registry import ToolRegistry

console = Console()


def create_agent(settings: Settings) -> PrivateClawAgent:
    """Create agent from settings."""
    # Initialize memory - pass settings object directly
    memory = MemoryManager(settings)

    # Initialize LLM
    llm = LLMFactory.create_from_settings(settings)

    # Load tools - create registry instance
    registry = ToolRegistry()
    tools = registry.load_all()

    # Create agent
    return PrivateClawAgent(
        llm=llm,
        memory=memory,
        tools=tools,
        tool_registry=registry,
    )


@click.group()
@click.option("--config", "-c", help="Path to config file")
@click.pass_context
def cli(ctx, config):
    """CatClaw - Your private AI assistant."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = get_settings()


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, type=int, help="Port to bind")
@click.pass_context
def serve(ctx, host, port):
    """Start the gateway server."""
    from privateclaw.gateway.server import Gateway

    settings = ctx.obj["settings"]
    settings.gateway_host = host
    settings.gateway_port = port

    gateway = Gateway(settings)

    console.print(Panel(
        f"Starting CatClaw Gateway on {host}:{port}",
        title="🚀 CatClaw",
        style="green",
    ))

    asyncio.run(gateway.start())


@cli.command()
@click.option("--session", "-s", default="cli", help="Session ID")
@click.pass_context
def chat(ctx, session):
    """Start an interactive chat session."""
    settings = ctx.obj["settings"]

    console.print(Panel(
        "Welcome to CatClaw! Type 'exit' or 'quit' to end the session.",
        title="CatClaw Chat",
        style="blue",
    ))

    agent = create_agent(settings)

    async def run_chat():
        while True:
            try:
                # Get user input
                user_input = console.input("[bold green]You:[/bold green] ")

                # Check for exit commands
                if user_input.lower() in ("exit", "quit", "q"):
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input.strip():
                    continue

                # Get response
                with console.status("[bold blue]Thinking...[/bold blue]"):
                    response = await agent.run(user_input, session)

                # Display response
                console.print(Panel(
                    response,
                    title="🤖 CatClaw",
                    style="cyan",
                ))

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")

    asyncio.run(run_chat())


@cli.command()
@click.argument("message")
@click.option("--session", "-s", default="cli", help="Session ID")
@click.pass_context
def ask(ctx, message, session):
    """Ask a single question."""
    settings = ctx.obj["settings"]
    agent = create_agent(settings)

    async def run_ask():
        response = await agent.run(message, session)
        console.print(response)

    asyncio.run(run_ask())


@cli.command()
@click.pass_context
def models(ctx):
    """List available LLM providers and models."""
    providers = LLMFactory.list_providers()

    for provider in providers:
        console.print(f"\n[bold]{provider}:[/bold]")
        models = LLMFactory.list_models(provider)
        for model in models:
            console.print(f"  - {model}")


@cli.command()
@click.pass_context
def tools(ctx):
    """List available tools."""
    registry = ToolRegistry()
    registry.load_builtin_tools()

    categories = registry.get_categories()
    for category in categories:
        console.print(f"\n[bold]{category}:[/bold]")
        tool_list = registry.get_by_category(category)
        for tool in tool_list:
            console.print(f"  - {tool.name}: {tool.description}")


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    settings = ctx.obj["settings"]

    console.print(Panel(
        f"App Name: {settings.app_name}\n"
        f"Data Dir: {settings.data_dir}\n"
        f"Log Level: {settings.log_level}\n\n"
        f"LLM Provider: {settings.llm_provider}\n"
        f"LLM Model: {settings.llm_model}\n\n"
        f"Gateway: {settings.gateway_host}:{settings.gateway_port}\n\n"
        f"Channels:\n"
        f"  Web: {'enabled' if settings.channel_web_enabled else 'disabled'}\n"
        f"  CLI: {'enabled' if settings.channel_cli_enabled else 'disabled'}\n"
        f"  Telegram: {'enabled' if settings.channel_telegram_enabled else 'disabled'}\n"
        f"  Discord: {'enabled' if settings.channel_discord_enabled else 'disabled'}\n"
        f"  Slack: {'enabled' if settings.channel_slack_enabled else 'disabled'}\n",
        title="⚙️ Configuration",
        style="yellow",
    ))


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
