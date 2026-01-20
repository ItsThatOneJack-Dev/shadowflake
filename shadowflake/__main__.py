# shadowflake/__main__.py
import argparse
import datetime
import re
import sys

from .shadowflake import Shadowflake, ShadowflakeError


def output_machine(data, format_type):
    import json
    
    if format_type == "json":
        print(json.dumps(data, separators=(',', ':')))
    elif format_type == "dict":
        print(repr(data))

def dumb_input(prompt, default=None):
    if default is not None:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else str(default)
    return input(f"{prompt}: ").strip()

def dumb_choice(prompt, choices):
    while True:
        result = input(f"{prompt} ({'/'.join(choices)}): ").strip()
        if result in choices:
            return result
        print(f"Invalid choice. Please choose from: {', '.join(choices)}")

def dumb_panel(title, content, color=None):
    width = 60
    print("=" * width)
    print(f" {title} ".center(width))
    print("=" * width)
    print(content)
    print("=" * width)

def prompt_missing_fields(fields, use_rich, console=None):
    system = fields.get("system")
    node = fields.get("node")
    id_val = fields.get("id")
    
    if use_rich:
        assert console is not None
        if system is None:
            system = console.print("[yellow]SYSTEM field is required but not provided[/yellow]") or ""
            system = console.input("Enter SYSTEM field (alphanumeric, - and _ only, max 10 characters) [empty]: ").strip() or ""
        if node is None:
            console.print("[yellow]NODE field is required but not provided[/yellow]")
            node = console.input("Enter NODE field (alphanumeric, - and _ only, max 10 characters) [empty]: ").strip() or ""
        if id_val is None:
            console.print("[yellow]ID field is required but not provided[/yellow]")
            id_input = console.input("Enter ID field (numeric, positive or 0) [0]: ").strip() or "0"
            try:
                id_val = int(id_input)
            except ValueError:
                console.print("[red]Invalid ID, using 0[/red]")
                id_val = 0
    else:
        if system is None:
            print("SYSTEM field is required but not provided")
            system = dumb_input("Enter SYSTEM field (alphanumeric, - and _ only, max 10 characters)", "")
        if node is None:
            print("NODE field is required but not provided")
            node = dumb_input("Enter NODE field (alphanumeric, - and _ only, max 10 characters)", "")
        if id_val is None:
            print("ID field is required but not provided")
            id_input = dumb_input("Enter ID field (numeric, positive or 0)", "0")
            try:
                id_val = int(id_input)
            except ValueError:
                print("Invalid ID, using 0")
                id_val = 0
    
    return system or None, node or None, id_val

def generate_from_args(args, use_rich, console=None):
    if hasattr(args, 'anchor') and args.anchor:
        try:
            anchor_time = datetime.datetime.strptime(args.anchor, "%H:%M:%S").time()
            now = datetime.datetime.now(datetime.timezone.utc)
            anchor = datetime.datetime.combine(now.date(), anchor_time, tzinfo=datetime.timezone.utc)
        except ValueError:
            if args.machine:
                output_machine({"success": False, "error": "Invalid anchor time format. Use HH:MM:SS"}, args.machine)
            elif use_rich:
                assert console is not None
                console.print("[red][bold]✗[/bold] Invalid anchor time format. Use HH:MM:SS[/red]")
            else:
                print("Error: Invalid anchor time format. Use HH:MM:SS")
            sys.exit(1)
    else:
        anchor = None
    
    system = getattr(args, 'system', None)
    node = getattr(args, 'node', None)
    id_val = getattr(args, 'id', None)
    
    fields = {"system": system, "node": node, "id": id_val}
    present = [k for k, v in fields.items() if v is not None]
    missing = [k for k, v in fields.items() if v is None]
    
    if present and missing:
        if args.fail_silently:
            if args.machine:
                output_machine({"success": False, "error": "Metadata incomplete"}, args.machine)
            sys.exit(1)
        
        if args.no_dumb:
            error_msg = f"Metadata must be all-or-nothing! Missing fields: {', '.join(missing)}"
            if args.machine:
                output_machine({"success": False, "error": error_msg}, args.machine)
            elif use_rich:
                assert console is not None
                console.print("[red][bold]✗[/bold] Metadata must be all-or-nothing![/red]")
                console.print(f"[yellow]Missing fields: {', '.join(missing)}[/yellow]")
            else:
                print("Error: Metadata must be all-or-nothing!")
                print(f"Missing fields: {', '.join(missing)}")
            sys.exit(1)
        
        if args.machine:
            error_msg = f"Metadata incomplete. Missing: {', '.join(missing)}"
            output_machine({"success": False, "error": error_msg}, args.machine)
            sys.exit(1)
        
        system, node, id_val = prompt_missing_fields(fields, use_rich and not args.dumb, console)
    
    if system is not None:
        system = system.upper()
        if system and not re.fullmatch(r"[A-Z0-9\-_]+", system):
            error_msg = f"Invalid SYSTEM value: {system!r}"
            if args.machine:
                output_machine({"success": False, "error": error_msg}, args.machine)
            elif use_rich:
                assert console is not None
                console.print(f"[red][bold]✗[/bold] Invalid SYSTEM value: {system!r}[/red]")
            else:
                print(f"Error: Invalid SYSTEM value: {system!r}")
            sys.exit(1)
        if not system:
            system = None
    
    if node is not None:
        node = node.upper()
        if node and not re.fullmatch(r"[A-Z0-9\-_]+", node):
            error_msg = f"Invalid NODE value: {node!r}"
            if args.machine:
                output_machine({"success": False, "error": error_msg}, args.machine)
            elif use_rich:
                assert console is not None
                console.print(f"[red][bold]✗[/bold] Invalid NODE value: {node!r}[/red]")
            else:
                print(f"Error: Invalid NODE value: {node!r}")
            sys.exit(1)
        if not node:
            node = None
    
    if id_val is not None and id_val < 0:
        error_msg = "ID must be non-negative!"
        if args.machine:
            output_machine({"success": False, "error": error_msg}, args.machine)
        elif use_rich:
            assert console is not None
            console.print("[red][bold]✗[/bold] ID must be non-negative![/red]")
        else:
            print("Error: ID must be non-negative!")
        sys.exit(1)
    
    try:
        shadowflake = Shadowflake.generate(
            anchor,
            system=system,
            node=node,
            id=id_val,
        )
        
        if args.machine:
            output_machine({"success": True, "uxid": shadowflake}, args.machine)
        elif use_rich:
            assert console is not None
            from rich.panel import Panel
            console.print(Panel(
                f"[bold green]{shadowflake}[/bold green]",
                title="Generated Shadowflake",
                border_style="green"
            ))
        else:
            dumb_panel("Generated Shadowflake", shadowflake)
        
        return shadowflake
    except ShadowflakeError as e:
        if args.machine:
            output_machine({"success": False, "error": str(e)}, args.machine)
        elif use_rich:
            assert console is not None
            console.print(f"[red][bold]✗[/bold] Error generating Shadowflake: {e}[/red]")
        else:
            print(f"Error generating Shadowflake: {e}")
        sys.exit(1)

def decode_from_args(args, use_rich, console=None):
    try:
        decoded = Shadowflake.decode(args.decode)
        
        if use_rich:
            assert console is not None
            from rich.panel import Panel
            body = []
            for k, v in decoded.items():
                body.append(f"[yellow]{k}:[/yellow] {v}")
            console.print(Panel(
                "\n".join(body),
                title="Decoded Shadowflake",
                border_style="green"
            ))
        else:
            lines = [f"{k}: {v}" for k, v in decoded.items()]
            dumb_panel("Decoded Shadowflake", "\n".join(lines))
        
        return decoded
    except ShadowflakeError as e:
        if use_rich:
            assert console is not None
            console.print(f"[red][bold]✗[/bold] Error decoding Shadowflake: {e}[/red]")
        else:
            print(f"Error decoding Shadowflake: {e}")
        sys.exit(1)

def interactive_mode(use_rich):
    if use_rich:
        try:
            from rich.console import Console
            from rich.prompt import Prompt
            from rich.panel import Panel
            console = Console()
        except ImportError:
            print("Interactive mode uses the 'rich' package.")
            print("You can either install it manually or use the extra:")
            print("  pip install shadowflake[interactive]")
            print("")
            print("Or use --dumb flag for simple prompts without rich")
            sys.exit(1)
        
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
                            console.print("[0] No (cancel) | [1] No (don't use metadata) | [2] Yes (make them empty)")
                            poptyp = Prompt.ask(
                                "Choose an option",
                                choices=["0", "1", "2"],
                                default="0",
                                show_choices=False
                            )
                            
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
    
    else:
        firstIteration = True
        while True:
            if not firstIteration:
                print()
            firstIteration = False
            
            dumb_panel("Shadowflake", "[1] Generate a Shadowflake\n[2] Decode a Shadowflake\n[0] Exit")
            
            opt = dumb_choice("Select an option", ["0", "1", "2"])
            
            match opt:
                case "0":
                    print("✓ Exiting...")
                    break

                case "1":
                    anchor_input = dumb_input("Enter anchor time (HH:MM:SS, 24 hour)", "00:00:00")
                    try:
                        anchor_time = datetime.datetime.strptime(anchor_input, "%H:%M:%S").time()
                        now = datetime.datetime.now(datetime.timezone.utc)
                        anchor = datetime.datetime.combine(now.date(), anchor_time, tzinfo=datetime.timezone.utc)
                    except ValueError:
                        print("✗ Invalid time format.")
                        continue

                    system = dumb_input("Enter SYSTEM field (alphanumeric, - and _ only, max 10 characters)", "") or None
                    node = dumb_input("Enter NODE field (alphanumeric, - and _ only, max 10 characters)", "") or None
                    id_input = dumb_input("Enter ID field (numeric, positive or 0)", "") or None

                    if id_input is not None:
                        try:
                            id = int(id_input)
                            if id < 0:
                                print("✗ ID must be non-negative!")
                                continue
                        except ValueError:
                            print("✗ ID must be a number!")
                            continue
                    else:
                        id = None

                    if system is not None:
                        system = system.upper()
                        if not re.fullmatch(r"[A-Z0-9\-_]+", system):
                            print(f"✗ Invalid SYSTEM value: {system!r}!")
                            continue

                    if node is not None:
                        node = node.upper()
                        if not re.fullmatch(r"[A-Z0-9\-_]+", node):
                            print(f"✗ Invalid NODE value: {node!r}!")
                            continue

                    fields = {
                        "system": system,
                        "node": node,
                        "id": id,
                    }

                    present = [k for k, v in fields.items() if v is not None]
                    missing = [k for k, v in fields.items() if v is None]

                    if present and missing:
                        print("! Metadata must be all-or-nothing!")

                        if len(missing) == 3:
                            needs_populating = "system, node and id"
                        elif len(missing) == 2:
                            needs_populating = " and ".join(missing)
                        else:
                            needs_populating = missing[0]

                        print(f"Populate {needs_populating}?")
                        print("[0] No (cancel) | [1] No (don't use metadata) | [2] Yes (make them empty)")
                        poptyp = dumb_choice("Choose an option", ["0", "1", "2"])

                        match poptyp:
                            case "0":
                                continue
                            case "1":
                                system = node = id = None
                            case "2":
                                if system is None:
                                    system = ""
                                if node is None:
                                    node = ""
                                if id is None:
                                    id = 0
                    
                    try:
                        shadowflake = Shadowflake.generate(
                            anchor,
                            system=system,
                            node=node,
                            id=id,
                        )
                        dumb_panel("Generated Shadowflake", shadowflake)
                    except ShadowflakeError as e:
                        print(f"✗ Error generating Shadowflake: {e}")
                
                case "2":
                    shadowflake_input = dumb_input("Enter Shadowflake to decode")
                    try:
                        decoded = Shadowflake.decode(shadowflake_input)
                        lines = [f"{k}: {v}" for k, v in decoded.items()]
                        dumb_panel("Decoded Shadowflake", "\n".join(lines))
                    except ShadowflakeError as e:
                        print(f"✗ Error decoding Shadowflake: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Shadowflake - Universal Extended Identity (UXID) generator and decoder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shadowflake                                    # Interactive mode (requires rich)
  shadowflake --dumb                             # Interactive mode with simple prompts
  shadowflake generate                           # Generate a Shadowflake
  shadowflake generate --system=AUTH --node=API --id=123
  shadowflake decode <UXID>                      # Decode a Shadowflake
  shadowflake generate --machine=json            # Machine-readable output
        """
    )
    
    parser.add_argument(
        "--dumb",
        action="store_true",
        help="Use simple prompts without rich (for interactive mode or missing fields)"
    )
    parser.add_argument(
        "--no-dumb",
        action="store_true",
        help="Fail with error if metadata is incomplete (don't prompt)"
    )
    parser.add_argument(
        "--fail-silently",
        action="store_true",
        help="Exit silently with error code if metadata is incomplete"
    )
    parser.add_argument(
        "--machine",
        type=str,
        choices=["json", "dict"],
        help="Output in machine-readable format (json or dict)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    generate_parser = subparsers.add_parser("generate", help="Generate a new Shadowflake")
    generate_parser.add_argument(
        "--anchor",
        type=str,
        metavar="HH:MM:SS",
        help="Anchor time for generation (24-hour format, e.g., 14:30:00)"
    )
    generate_parser.add_argument(
        "--system",
        type=str,
        metavar="SYSTEM",
        help="SYSTEM field for metadata (alphanumeric, - and _ only, max 10 chars)"
    )
    generate_parser.add_argument(
        "--node",
        type=str,
        metavar="NODE",
        help="NODE field for metadata (alphanumeric, - and _ only, max 10 chars)"
    )
    generate_parser.add_argument(
        "--id",
        type=int,
        metavar="ID",
        help="ID field for metadata (non-negative integer, max 1,073,741,823)"
    )
    
    decode_parser = subparsers.add_parser("decode", help="Decode a Shadowflake UXID")
    decode_parser.add_argument(
        "uxid",
        type=str,
        help="The Shadowflake UXID to decode"
    )
    
    args = parser.parse_args()
    
    use_rich = not args.dumb
    console = None
    
    if use_rich and not (args.command in ["generate", "decode"]):
        try:
            from rich.console import Console
            console = Console()
        except ImportError:
            if not args.dumb:
                print("Interactive mode uses the 'rich' package.")
                print("You can either install it manually or use the extra:")
                print("  pip install shadowflake[interactive]")
                print("")
                print("Or use --dumb flag for simple prompts without rich")
                sys.exit(1)
            use_rich = False
    elif use_rich and args.command in ["generate", "decode"]:
        if not args.machine:
            try:
                from rich.console import Console
                console = Console()
            except ImportError:
                use_rich = False
        else:
            use_rich = False
    
    if args.command == "decode":
        decode_from_args(args, use_rich, console)
    elif args.command == "generate":
        generate_from_args(args, use_rich, console)
    else:
        interactive_mode(use_rich)

if __name__ == "__main__":
    main()