# shadowflake/__main__.py
import datetime
import re
import sys

def main():
    # Check if rich is available
    try:
        from rich.console import Console
        from rich.prompt import Prompt
        from rich.panel import Panel
        from rich import print as rprint
        console = Console()
    except ImportError:
        print("Interactive mode uses the 'rich' package.")
        print("You can either install it manually or use the extra:")
        print("pip install shadowflake[interactive]")
        sys.exit(1)
    
    from .shadowflake import Shadowflake, ShadowflakeError

    firstIteration = True
    while True:
        if not firstIteration:
            console.print()
        firstIteration = False
        
        console.print(Panel.fit(
            "[bold cyan]Shadowflake[/bold cyan]\n\n"
            "[1] Generate a Shadowflake\n"
            "[2] Decode a Shadowflake\n"
            "[0] Exit",
            border_style="cyan"
        ))
        
        opt = Prompt.ask("Select an option", choices=["0", "1", "2"])
        
        match opt:
            case "0":
                console.print("[green][bold]✓[/bold] Exiting...[/green]")
                break

            case "1":
                anchor_input = Prompt.ask(
                    "Enter anchor time (HH:MM:SS, 24 hour)",
                    default="00:00:00"
                )
                try:
                    anchor_time = datetime.datetime.strptime(anchor_input, "%H:%M:%S").time()
                    now = datetime.datetime.now(datetime.timezone.utc)
                    anchor = datetime.datetime.combine(now.date(), anchor_time, tzinfo=datetime.timezone.utc)
                except ValueError:
                    console.print("[red][bold]✗[/bold] Invalid time format.[/red]")
                    continue

                system = Prompt.ask(
                    "Enter SYSTEM field (alphanumeric, - and _ only, max 10 characters)",
                    default=""
                ) or None
                node = Prompt.ask(
                    "Enter NODE field (alphanumeric, - and _ only, max 10 characters)",
                    default=""
                ) or None
                id_input = Prompt.ask(
                    "Enter ID field (numeric, positive or 0)",
                    default=""
                ) or None

                if id_input is not None:
                    try:
                        id = int(id_input)
                        if id < 0:
                            console.print("[red][bold]✗[/bold] ID must be non-negative![/red]")
                            continue
                    except ValueError:
                        console.print("[red][bold]✗[/bold] ID must be a number![/red]")
                        continue
                else:
                    id = None

                if system is not None:
                    system = system.upper()
                    if not re.fullmatch(r"[A-Z0-9\-_]+", system):
                        console.print(f"[red][bold]✗[/bold] Invalid SYSTEM value: {system!r}![/red]")
                        continue

                if node is not None:
                    node = node.upper()
                    if not re.fullmatch(r"[A-Z0-9\-_]+", node):
                        console.print(f"[red][bold]✗[/bold] Invalid NODE value: {node!r}![/red]")
                        continue

                fields = {
                    "system": system,
                    "node": node,
                    "id": id,
                }

                present = [k for k, v in fields.items() if v is not None]
                missing = [k for k, v in fields.items() if v is None]

                if present and missing:
                    console.print("[yellow][bold]![/bold] Metadata must be all-or-nothing![/yellow]")

                    if len(missing) == 3:
                        needs_populating = "system, node and id"
                    elif len(missing) == 2:
                        needs_populating = " and ".join(missing)
                    else:
                        needs_populating = missing[0]

                    while True:
                        console.print(f"Populate {needs_populating}?")
                        poptyp = Prompt.ask(
                            "Choose an option",
                            choices=["0", "1", "2"],
                            default="0",
                            show_choices=False
                        )
                        console.print("[0] No (cancel) | [1] No (don't use metadata) | [2] Yes (make them empty)")
                        
                        if poptyp not in "012":
                            console.print(f"[red][bold]✗[/bold] Invalid option![/red]")
                            continue

                        match poptyp:
                            case "0":
                                break
                            case "1":
                                system = node = id = None
                                break
                            case "2":
                                if system is None:
                                    system = ""
                                if node is None:
                                    node = ""
                                if id is None:
                                    id = 0
                                break

                    if poptyp == "0":
                        continue
                
                try:
                    shadowflake = Shadowflake.generate(
                        anchor,
                        system=system,
                        node=node,
                        id=id,
                    )
                    console.print(Panel(
                        f"[bold green]{shadowflake}[/bold green]",
                        title="Generated Shadowflake",
                        border_style="green"
                    ))
                except ShadowflakeError as e:
                    console.print(f"[red][bold]✗[/bold] Error generating Shadowflake: {e}[/red]")
            
            case "2":
                shadowflake_input = Prompt.ask("Enter Shadowflake to decode")
                try:
                    decoded = Shadowflake.decode(shadowflake_input)
                    body = []
                    for k, v in decoded.items():
                        body.append(f"[yellow]{k}:[/yellow] {v}")


                    console.print(Panel(
                        "\n".join(body),
                        title="Decoded Shadowflake",
                        border_style="green"
                    ))
                except ShadowflakeError as e:
                    console.print(f"[red][bold]✗[/bold] Error decoding Shadowflake: {e}[/red]")

if __name__ == "__main__":
    main()