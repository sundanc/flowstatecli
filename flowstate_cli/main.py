import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import Optional
from flowstate_cli.api import api
from flowstate_cli.config import config
from flowstate_cli.timer import timer
from flowstate_cli.daemon import daemon
from flowstate_cli.flow_mode import flow_mode
from flowstate_cli.data_manager import get_data_manager
from flowstate_cli.auth import local_auth
from flowstate_cli.sync_engine import sync_engine

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
            rprint("✅ Magic link sent! Check your email.")
            rprint("")
            rprint("📝 [bold yellow]Next steps:[/bold yellow]")
            rprint("1. Click the magic link in your email")
            rprint("2. You'll be redirected to the web dashboard")
            rprint("3. Copy your CLI token from the dashboard")
            rprint("4. Run: [bold cyan]flowstate auth token <your-token>[/bold cyan]")
            rprint("")
            rprint("� [dim]Your CLI token can be found in the dashboard under 'CLI Access'[/dim]")
        else:
            rprint("❌ Failed to send magic link. Please try again.")
    
    asyncio.run(_login())

@auth_app.command("token")
def auth_token(token: str = typer.Argument(..., help="CLI authentication token from the dashboard")):
    """Set authentication token from the web dashboard"""
    config.set_auth_token(token)
    rprint("✅ Authentication token saved!")
    rprint("🚀 You can now use all FlowState CLI commands!")

@app.command("donate")
def donate():
    """Support FlowState development"""
    import webbrowser
    
    rprint("☕ [bold yellow]Support FlowState Development[/bold yellow]")
    rprint("")
    rprint("💖 If FlowState has helped you stay productive, consider buying me a coffee!")
    rprint("🚀 Your support helps keep this project alive and growing.")
    rprint("")
    rprint("🌐 Opening donation page: [bold cyan]https://buymeacoffee.com/sundanc[/bold cyan]")
    rprint("")
    rprint("🙏 [dim]Thank you for using FlowState![/dim]")
    
    try:
        webbrowser.open("https://buymeacoffee.com/sundanc")
    except Exception:
        rprint("❌ Could not open browser. Please visit: https://buymeacoffee.com/sundanc")

# Task management commands
@app.command("add")
def add_task(description: str = typer.Argument(..., help="Task description")):
    """Add a new task"""
    async def _add_task():
        try:
            data_manager = get_data_manager()
            task = await data_manager.create_task(description)
            rprint(f"✅ Added task: [bold green]{task['description']}[/bold green]")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_add_task())

@app.command("list")
def list_tasks(all: bool = typer.Option(False, "--all", "-a", help="Include completed tasks")):
    """List all tasks"""
    async def _list_tasks():
        try:
            data_manager = get_data_manager()
            tasks = await data_manager.get_tasks(include_completed=all)
            
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
                created_date = task['created_at'][:10] if task['created_at'] else "N/A"
                table.add_row(
                    str(task['id']),
                    status,
                    task['description'],
                    created_date
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
            data_manager = get_data_manager()
            task = await data_manager.start_task(task_id)
            rprint(f"🎯 Started task: [bold green]{task['description']}[/bold green]")
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_task())

@app.command("done")
def complete_task(task_id: Optional[int] = typer.Argument(None, help="Task ID to complete (or 'current' for active task)")):
    """Mark task as completed"""
    async def _complete_task():
        try:
            data_manager = get_data_manager()
            if task_id is None:
                # Get current active task
                active_task = await data_manager.get_active_task()
                if not active_task:
                    rprint("❌ No active task found. Specify a task ID or start a task first.")
                    return
                target_id = active_task['id']
            else:
                target_id = task_id
            
            task = await data_manager.complete_task(target_id)
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
            data_manager = get_data_manager()
            await data_manager.delete_task(task_id)
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
            data_manager = get_data_manager()
            # Get active task if any
            active_task = await data_manager.get_active_task()
            task_description = active_task['description'] if active_task else "General focus"
            task_id = active_task['id'] if active_task else None
            
            # Get user settings
            try:
                user = await data_manager.get_current_user()
                duration = user.get('pomo_duration', 25) if user else 25
            except Exception:
                duration = 25
            
            # Start daemon timer
            success, message = daemon.start_timer(duration, "focus", task_description, task_id)
            if success:
                rprint(f"🍅 {message}")
                rprint(f"📝 Working on: [bold]{task_description}[/bold]")
                rprint("🔄 Timer running in background. Use 'flowstate pom status' to check progress.")
                
                # Record pomodoro in backend
                try:
                    await data_manager.start_pomodoro(task_id, "focus", duration)
                except Exception as e:
                    rprint(f"⚠️ Failed to sync pomodoro: {e}")
                
            else:
                rprint(f"❌ {message}")
                
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_pomodoro())

@pom_app.command("stop")
def pom_stop():
    """Stop current timer"""
    success, message = daemon.stop_timer()
    if success:
        rprint(f"⏹️ {message}")
    else:
        rprint(f"❌ {message}")

@pom_app.command("status")
def pom_status():
    """Show current timer status"""
    status = daemon.get_status()
    
    if not status['active']:
        if status.get('daemon_running'):
            rprint("⏸️ No timer is currently running")
        else:
            rprint("� Timer daemon is not running")
    else:
        session_type = status['session_type'].replace('_', ' ').title()
        remaining = status['remaining_display']
        task = status.get('task_description', 'Unknown')
        
        if status['paused']:
            rprint(f"⏸️ {session_type} timer paused - {remaining} remaining")
        else:
            rprint(f"🍅 {session_type} timer active - {remaining} remaining")
        rprint(f"📝 Working on: [bold]{task}[/bold]")

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
            
            # Start daemon timer
            success, message = daemon.start_timer(duration, f"{type}_break", f"{type.title()} break")
            if success:
                rprint(f"☕ {message}")
                rprint("🔄 Break timer running in background. Use 'flowstate pom status' to check progress.")
                
                # Record break in backend
                try:
                    await api.start_pomodoro(None, f"{type}_break", duration)
                except Exception as e:
                    rprint(f"⚠️ Failed to sync with backend: {e}")
            else:
                rprint(f"❌ {message}")
                
        except Exception as e:
            rprint(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_break())

@pom_app.command("pause")
def pom_pause():
    """Pause/resume current timer"""
    success, message = daemon.pause_timer()
    if success:
        rprint(f"⏸️ {message}")
    else:
        rprint(f"❌ {message}")

@pom_app.command("daemon")
def pom_daemon(action: str = typer.Argument(..., help="Daemon action: 'start', 'stop', or 'status'")):
    """Manage timer daemon"""
    if action == "start":
        success, message = daemon.start_daemon()
        if success:
            rprint(f"🚀 {message}")
        else:
            rprint(f"❌ {message}")
    elif action == "stop":
        success, message = daemon.stop_daemon()
        if success:
            rprint(f"🛑 {message}")
        else:
            rprint(f"❌ {message}")
    elif action == "status":
        if daemon.is_daemon_running():
            rprint("✅ Timer daemon is running")
        else:
            rprint("❌ Timer daemon is not running")
    else:
        rprint("❌ Action must be 'start', 'stop', or 'status'")

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

# Mode management commands
@mode_app.command("set")
def mode_set(mode: str = typer.Argument(..., help="Mode to set: cloud, local, or hybrid")):
    """Set operating mode"""
    try:
        config.set_mode(mode)
        rprint(f"✅ Mode set to: [bold cyan]{mode}[/bold cyan]")
        
        if mode == "local":
            rprint("📝 [yellow]Note:[/yellow] In local mode, all data is stored locally and won't sync to cloud")
        elif mode == "cloud":
            rprint("📝 [yellow]Note:[/yellow] In cloud mode, you need internet connection and valid authentication")
        else:  # hybrid
            rprint("📝 [yellow]Note:[/yellow] In hybrid mode, cloud is preferred but falls back to local when offline")
    except ValueError as e:
        rprint(f"❌ {e}")

@mode_app.command("status")
def mode_status():
    """Show current mode and connectivity status"""
    current_mode = config.get_mode()
    
    table = Table(title="FlowState Mode Status")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Current Mode", current_mode)
    table.add_row("Auto Sync", "Enabled" if config.get_auto_sync() else "Disabled")
    table.add_row("Sync Interval", f"{config.get_sync_interval()} seconds")
    
    # Check connectivity
    async def check_status():
        connectivity = await config.check_connectivity()
        table.add_row("Cloud Connectivity", "✅ Connected" if connectivity else "❌ Offline")
        
        # Check authentication
        cloud_auth = config.get_auth_token() is not None
        local_auth_status = local_auth.is_authenticated_locally()
        
        table.add_row("Cloud Auth", "✅ Authenticated" if cloud_auth else "❌ Not authenticated")
        table.add_row("Local Auth", "✅ Authenticated" if local_auth_status else "❌ Not authenticated")
        
        console.print(table)
    
    asyncio.run(check_status())

@mode_app.command("sync")
def mode_sync():
    """Manually trigger sync with cloud"""
    async def _sync():
        try:
            if config.is_local_mode():
                rprint("❌ Cannot sync in local-only mode")
                return
            
            if not await config.check_connectivity():
                rprint("❌ No internet connection available")
                return
            
            rprint("🔄 Starting sync...")
            results = await sync_engine.sync_all()
            
            if "error" in results:
                rprint(f"❌ Sync failed: {results['error']}")
                return
            
            # Display sync results
            rprint("✅ Sync completed!")
            if results.get("users_synced", 0) > 0:
                rprint(f"👤 Users synced: {results['users_synced']}")
            if results.get("tasks_synced", 0) > 0:
                rprint(f"� Tasks synced: {results['tasks_synced']}")
            if results.get("pomodoros_synced", 0) > 0:
                rprint(f"🍅 Pomodoros synced: {results['pomodoros_synced']}")
            
            if results.get("errors"):
                rprint(f"⚠️ {len(results['errors'])} errors occurred during sync")
                for error in results["errors"][:3]:  # Show first 3 errors
                    rprint(f"  • {error}")
                
        except Exception as e:
            rprint(f"❌ Sync failed: {e}")
    
    asyncio.run(_sync())

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

# Local auth commands
@auth_app.command("local-login")
def auth_local_login(
    username: str = typer.Option(..., prompt=True, help="Username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password")
):
    """Login with local account"""
    user = local_auth.authenticate_local_user(username, password)
    if user:
        token = local_auth.generate_local_token(user)
        local_auth.save_auth_state({"local_token": token})
        config.set_local_user_id(user.id)
        rprint(f"✅ Welcome back, [bold cyan]{username}[/bold cyan]!")
    else:
        rprint("❌ Invalid credentials")

@auth_app.command("local-register")
def auth_local_register(
    username: str = typer.Option(..., prompt=True, help="Choose a username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True, help="Password"),
    email: str = typer.Option(None, help="Email (optional, for cloud sync)")
):
    """Register new local account"""
    try:
        user = local_auth.create_local_user(username, password, email)
        token = local_auth.generate_local_token(user)
        local_auth.save_auth_state({"local_token": token})
        config.set_local_user_id(user.id)
        rprint(f"✅ Account created! Welcome, [bold cyan]{username}[/bold cyan]!")
        if email:
            rprint(f"📧 Email [dim]{email}[/dim] saved for future cloud sync")
        else:
            rprint("💡 [dim]Tip: You can add an email later for cloud sync[/dim]")
    except Exception as e:
        rprint(f"❌ Registration failed: {e}")

@auth_app.command("logout")
def auth_logout():
    """Logout from current session"""
    config.set_auth_token(None)
    local_auth.clear_auth_state()
    config.set_local_user_id(None)
    rprint("✅ Logged out successfully!")

if __name__ == "__main__":
    app()
