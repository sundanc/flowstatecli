import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import Optional
from flowstate_cli.api import api
from flowstate_cli.config import config
from flowstate_cli.timer import timer
from flowstate_cli.flow_mode import flow_mode

app = typer.Typer(help="FlowState CLI - Productivity tool with task management and Pomodoro timers")
console = Console()

# Auth commands
auth_app = typer.Typer(help="Authentication commands")
app.add_typer(auth_app, name="auth")

@auth_app.command("login")
def auth_login(email: str = typer.Argument(..., help="Your email address")):
    """Login with magic link authentication"""
    async def _login():
        success = await api.send_magic_link(email)
        if success:
            rprint("✅ Magic link sent! Check your email and follow the instructions.")
            rprint("💡 After clicking the link, copy the token and run: flowstate auth token <your-token>")
        else:
            rprint("❌ Failed to send magic link. Please try again.")
    
    asyncio.run(_login())

@auth_app.command("token")
def auth_token(token: str = typer.Argument(..., help="Authentication token from magic link")):
    """Set authentication token"""
    config.set_auth_token(token)
    rprint("✅ Authentication token saved!")

# Task management commands
@app.command("add")
def add_task(description: str = typer.Argument(..., help="Task description")):
    """Add a new task"""
    async def _add_task():
        try:
            task = await api.create_task(description)
            rprint(f"✅ Added task: [bold green]{task['description']}[/bold green]")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_add_task())

@app.command("list")
def list_tasks(all: bool = typer.Option(False, "--all", "-a", help="Include completed tasks")):
    """List all tasks"""
    async def _list_tasks():
        try:
            tasks = await api.get_tasks(include_completed=all)
            
            if not tasks:
                rprint("📝 No tasks found. Add one with: flowstate add \"Task description\"")
                return
            
            table = Table(title="Your Tasks")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="magenta")
            table.add_column("Description", style="white")
            table.add_column("Created", style="dim")
            
            for task in tasks:
                status = "✅" if task['is_completed'] else ("🎯" if task['is_active'] else "⭕")
                table.add_row(
                    str(task['id']),
                    status,
                    task['description'],
                    task['created_at'][:10]  # Just the date
                )
            
            console.print(table)
            
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_list_tasks())

@app.command("start")
def start_task(task_id: int = typer.Argument(..., help="Task ID to start")):
    """Set task as active"""
    async def _start_task():
        try:
            task = await api.start_task(task_id)
            rprint(f"🎯 Started task: [bold green]{task['description']}[/bold green]")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_task())

@app.command("done")
def complete_task(task_id: Optional[int] = typer.Argument(None, help="Task ID to complete (or 'current' for active task)")):
    """Mark task as completed"""
    async def _complete_task():
        try:
            if task_id is None:
                # Get current active task
                active_task = await api.get_active_task()
                if not active_task:
                    rprint("❌ No active task found. Specify a task ID or start a task first.")
                    return
                target_id = active_task['id']
            else:
                target_id = task_id
            
            task = await api.complete_task(target_id)
            rprint(f"✅ Completed task: [bold green]{task['description']}[/bold green]")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_complete_task())

@app.command("rm")
def delete_task(task_id: int = typer.Argument(..., help="Task ID to delete")):
    """Delete a task"""
    # Confirmation prompt
    if not typer.confirm("Are you sure?"):
        rprint("❌ Cancelled")
        return
    
    async def _delete_task():
        try:
            await api.delete_task(task_id)
            rprint("🗑️ Task deleted successfully")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_delete_task())

# Pomodoro commands
pom_app = typer.Typer(help="Pomodoro timer commands")
app.add_typer(pom_app, name="pom")

@pom_app.command("start")
def pom_start():
    """Start a 25-minute focus session"""
    async def _start_pomodoro():
        try:
            # Get active task if any
            active_task = await api.get_active_task()
            task_description = active_task['description'] if active_task else "General focus"
            task_id = active_task['id'] if active_task else None
            
            # Get user settings
            user = await api.get_current_user()
            duration = user.get('pomo_duration', 25)
            
            # Start local timer
            success, message = timer.start(duration, "focus", task_description)
            if success:
                rprint(f"🍅 {message}")
                rprint(f"📝 Working on: [bold]{task_description}[/bold]")
                
                # Record pomodoro in backend
                await api.start_pomodoro(task_id, "focus", duration)
                
                # Show timer status periodically
                while timer.active:
                    status = timer.get_status()
                    if status['active']:
                        print(f"\r🍅 Focusing on '{task_description}': {status['remaining_display']}", end="", flush=True)
                        await asyncio.sleep(1)
                    else:
                        break
                
                print()  # New line after timer completes
            else:
                rprint(f"❌ {message}")
                
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_pomodoro())

@pom_app.command("stop")
def pom_stop():
    """Stop current timer"""
    success, message = timer.stop()
    if success:
        rprint(f"⏹️ {message}")
    else:
        rprint(f"❌ {message}")

@pom_app.command("status")
def pom_status():
    """Show current timer status"""
    status = timer.get_status()
    if status['active']:
        rprint(f"🍅 {status['session_type'].title()} session active")
        rprint(f"📝 Task: {status['task_description']}")
        rprint(f"⏰ Time remaining: {status['remaining_display']}")
        if status['paused']:
            rprint("⏸️ Timer is paused")
    else:
        rprint("⭕ No timer active")

@pom_app.command("break")
def pom_break(type: str = typer.Argument(..., help="Break type: 'short' or 'long'")):
    """Start a break timer"""
    if type not in ["short", "long"]:
        rprint("❌ Break type must be 'short' or 'long'")
        return
    
    async def _start_break():
        try:
            # Get user settings
            user = await api.get_current_user()
            duration = user.get('short_break_duration', 5) if type == "short" else user.get('long_break_duration', 15)
            
            # Start local timer
            success, message = timer.start(duration, f"{type}_break", f"{type.title()} break")
            if success:
                rprint(f"☕ {message}")
                
                # Record break in backend
                await api.start_pomodoro(None, f"{type}_break", duration)
                
                # Show timer status
                while timer.active:
                    status = timer.get_status()
                    if status['active']:
                        print(f"\r☕ {type.title()} break: {status['remaining_display']}", end="", flush=True)
                        await asyncio.sleep(1)
                    else:
                        break
                
                print()  # New line after timer completes
            else:
                rprint(f"❌ {message}")
                
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_break())

# Flow state mode commands
mode_app = typer.Typer(help="Flow state mode commands")
app.add_typer(mode_app, name="mode")

@mode_app.command("on")
def mode_on():
    """Activate distraction blocking"""
    success, message = flow_mode.activate()
    if success:
        rprint(f"🚫 {message}")
        rprint("💡 Distracting websites are now blocked")
    else:
        rprint(f"❌ {message}")

@mode_app.command("off")
def mode_off():
    """Deactivate distraction blocking"""
    success, message = flow_mode.deactivate()
    if success:
        rprint(f"✅ {message}")
    else:
        rprint(f"❌ {message}")

@mode_app.command("status")
def mode_status():
    """Check flow state mode status"""
    if flow_mode.is_active():
        rprint("🚫 Flow state mode is [bold red]ACTIVE[/bold red]")
        blocked_sites = flow_mode.get_blocked_sites()
        rprint(f"🔒 Blocking {len(blocked_sites)} sites")
    else:
        rprint("✅ Flow state mode is [bold green]INACTIVE[/bold green]")

# Configuration commands
config_app = typer.Typer(help="Configuration commands")
app.add_typer(config_app, name="config")

@config_app.command("show")
def config_show():
    """Show current configuration"""
    async def _show_config():
        try:
            user = await api.get_current_user()
            
            table = Table(title="FlowState Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Pomodoro Duration", f"{user['pomo_duration']} minutes")
            table.add_row("Short Break", f"{user['short_break_duration']} minutes")
            table.add_row("Long Break", f"{user['long_break_duration']} minutes")
            table.add_row("Notifications", "Enabled" if user['notifications_enabled'] else "Disabled")
            table.add_row("API URL", config.get_api_base_url())
            
            console.print(table)
            
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_show_config())

@config_app.command("set")
def config_set(key: str = typer.Argument(..., help="Configuration key"), 
               value: str = typer.Argument(..., help="Configuration value")):
    """Update configuration setting"""
    async def _set_config():
        try:
            # Map CLI keys to API keys
            key_mapping = {
                "pomo_duration": "pomo_duration",
                "short_break": "short_break_duration", 
                "long_break": "long_break_duration",
                "notifications": "notifications_enabled"
            }
            
            api_key = key_mapping.get(key)
            if not api_key:
                rprint(f"❌ Unknown setting: {key}")
                rprint("Available settings: pomo_duration, short_break, long_break, notifications")
                return
            
            # Convert value to appropriate type
            if key == "notifications":
                api_value = value.lower() in ["true", "1", "yes", "on"]
            else:
                api_value = int(value)
            
            # Update via API
            settings = {api_key: api_value}
            await api.update_user_settings(settings)
            
            rprint(f"✅ Updated {key} to {value}")
            
        except ValueError:
            rprint(f"❌ Invalid value for {key}: {value}")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_set_config())

# Analytics command
@app.command("stats")
def show_stats():
    """Show productivity statistics"""
    async def _show_stats():
        try:
            stats = await api.get_analytics()
            
            table = Table(title="Your Productivity Stats")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Total Pomodoros", str(stats['total_pomodoros']))
            table.add_row("Tasks Completed This Week", str(stats['tasks_completed_this_week']))
            
            focus_hours = stats['focus_time_this_week_minutes'] // 60
            focus_mins = stats['focus_time_this_week_minutes'] % 60
            table.add_row("Focus Time This Week", f"{focus_hours}h {focus_mins}m")
            
            console.print(table)
            
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_show_stats())

if __name__ == "__main__":
    app()
