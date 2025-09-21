"""
Command Line Interface for the notification service.
"""
import asyncio
import json
from datetime import datetime
from typing import Optional, List

try:
    import click
    from tabulate import tabulate
    
    from ..presentation.dependencies import get_container
    from ..application.dto import CreateUserDTO, SendNotificationDTO
    from ..domain.value_objects.user import UserId
    from ..domain.value_objects.notification import NotificationId
    from ..infrastructure.config import get_config
    from ..infrastructure.logging import setup_logging, get_logger
    
    
    @click.group()
    @click.option('--config-file', '-c', help='Configuration file path')
    @click.option('--log-level', '-l', default='INFO', help='Logging level')
    @click.pass_context
    def cli(ctx, config_file: Optional[str], log_level: str):
        """Notification Service CLI."""
        ctx.ensure_object(dict)
        
        config = get_config()
        config.logging.level = log_level
        setup_logging(config.logging)
        
        ctx.obj['config'] = config
        ctx.obj['logger'] = get_logger("cli")
        ctx.obj['container'] = get_container()
    
    
    @cli.group()
    def user():
        """User management commands."""
        pass
    
    
    @user.command()
    @click.option('--email', '-e', help='User email address')
    @click.option('--phone', '-p', help='User phone number')
    @click.option('--telegram', '-t', help='User Telegram ID')
    @click.option('--preferences', help='User preferences as JSON string')
    @click.pass_context
    def create(ctx, email: Optional[str], phone: Optional[str], telegram: Optional[str], preferences: Optional[str]):
        """Create a new user."""
        async def _create_user():
            container = ctx.obj['container']
            logger = ctx.obj['logger']
            
            prefs = {}
            if preferences:
                try:
                    prefs = json.loads(preferences)
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON in preferences", error=str(e))
                    return
            
            dto = CreateUserDTO(
                email=email,
                phone_number=phone,
                telegram_id=telegram,
                preferences=prefs
            )
            
            try:
                use_case = container.create_user_use_case()
                user_response = await use_case.execute(dto)
                
                click.echo(f"✅ User created successfully!")
                click.echo(f"   ID: {user_response.id}")
                click.echo(f"   Email: {user_response.email or 'Not set'}")
                click.echo(f"   Phone: {user_response.phone_number or 'Not set'}")
                click.echo(f"   Telegram: {user_response.telegram_id or 'Not set'}")
                click.echo(f"   Created: {user_response.created_at}")
                
            except Exception as e:
                logger.error("Failed to create user", error=str(e))
                click.echo(f"❌ Error: {e}")
        
        asyncio.run(_create_user())
    
    
    @user.command()
    @click.argument('user_id')
    @click.pass_context
    def get(ctx, user_id: str):
        """Get user by ID."""
        async def _get_user():
            container = ctx.obj['container']
            logger = ctx.obj['logger']
            
            try:
                use_case = container.get_user_use_case()
                user_response = await use_case.execute(UserId(user_id))
                
                if user_response:
                    click.echo("📋 User Information:")
                    data = [
                        ["ID", user_response.id],
                        ["Email", user_response.email or "Not set"],
                        ["Phone", user_response.phone_number or "Not set"],
                        ["Telegram", user_response.telegram_id or "Not set"],
                        ["Active", "Yes" if user_response.is_active else "No"],
                        ["Created", user_response.created_at],
                        ["Preferences", json.dumps(user_response.preferences, indent=2) if user_response.preferences else "None"]
                    ]
                    click.echo(tabulate(data, headers=["Field", "Value"], tablefmt="grid"))
                else:
                    click.echo(f"❌ User {user_id} not found")
                    
            except Exception as e:
                logger.error("Failed to get user", error=str(e))
                click.echo(f"❌ Error: {e}")
        
        asyncio.run(_get_user())
    
    
    @cli.group()
    def notification():
        """Notification management commands."""
        pass
    
    
    @notification.command()
    @click.argument('recipient_id')
    @click.argument('message')
    @click.option('--channels', '-c', multiple=True, default=['email'], help='Notification channels')
    @click.option('--priority', '-p', default='MEDIUM', help='Notification priority')
    @click.option('--scheduled', '-s', help='Schedule time (ISO format)')
    @click.option('--variables', help='Template variables as JSON string')
    @click.pass_context
    def send(ctx, recipient_id: str, message: str, channels: tuple, priority: str, scheduled: Optional[str], variables: Optional[str]):
        """Send a notification."""
        async def _send_notification():
            container = ctx.obj['container']
            logger = ctx.obj['logger']
            
            vars_dict = {}
            if variables:
                try:
                    vars_dict = json.loads(variables)
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON in variables", error=str(e))
                    return
            
            scheduled_at = None
            if scheduled:
                try:
                    scheduled_at = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
                except ValueError as e:
                    logger.error("Invalid date format", error=str(e))
                    return
            
            dto = SendNotificationDTO(
                recipient_id=recipient_id,
                message_template=message,
                message_variables=vars_dict,
                channels=list(channels),
                priority=priority,
                scheduled_at=scheduled_at
            )
            
            try:
                use_case = container.send_notification_use_case()
                notification_response = await use_case.execute(dto)
                
                click.echo(f"✅ Notification sent successfully!")
                click.echo(f"   ID: {notification_response.id}")
                click.echo(f"   Recipient: {notification_response.recipient_id}")
                click.echo(f"   Channels: {', '.join(notification_response.channels)}")
                click.echo(f"   Priority: {notification_response.priority}")
                click.echo(f"   Scheduled: {notification_response.scheduled_at}")
                click.echo(f"   Status: {notification_response.status}")
                
            except Exception as e:
                logger.error("Failed to send notification", error=str(e))
                click.echo(f"❌ Error: {e}")
        
        asyncio.run(_send_notification())
    
    
    @notification.command()
    @click.argument('notification_id')
    @click.pass_context
    def status(ctx, notification_id: str):
        """Get notification status."""
        async def _get_status():
            container = ctx.obj['container']
            logger = ctx.obj['logger']
            
            try:
                use_case = container.get_notification_status_use_case()
                status_response = await use_case.execute(NotificationId(notification_id))
                
                if status_response:
                    click.echo("📋 Notification Status:")
                    click.echo(f"   ID: {status_response.notification_id}")
                    click.echo(f"   Status: {status_response.status}")
                    click.echo(f"   Created: {status_response.created_at}")
                    
                    if status_response.deliveries:
                        click.echo("\n📦 Deliveries:")
                        delivery_data = []
                        for delivery in status_response.deliveries:
                            delivery_data.append([
                                delivery.delivery_id,
                                delivery.channel,
                                delivery.provider,
                                delivery.status,
                                delivery.attempts,
                                delivery.created_at,
                                delivery.completed_at or "In progress"
                            ])
                        
                        headers = ["ID", "Channel", "Provider", "Status", "Attempts", "Created", "Completed"]
                        click.echo(tabulate(delivery_data, headers=headers, tablefmt="grid"))
                    
                else:
                    click.echo(f"❌ Notification {notification_id} not found")
                    
            except Exception as e:
                logger.error("Failed to get notification status", error=str(e))
                click.echo(f"❌ Error: {e}")
        
        asyncio.run(_get_status())
    
    
    @cli.group()
    def server():
        """Server management commands."""
        pass
    
    
    @server.command()
    @click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
    @click.option('--port', '-p', default=8000, help='Port to bind to')
    @click.option('--reload', is_flag=True, help='Enable auto-reload')
    @click.pass_context
    def start(ctx, host: str, port: int, reload: bool):
        """Start the FastAPI server."""
        try:
            import uvicorn
            from ..presentation.app import create_app
            
            app = create_app()
            
            click.echo(f"🚀 Starting server on {host}:{port}")
            if reload:
                click.echo("🔄 Auto-reload enabled")
            
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=reload,
                log_level="info"
            )
            
        except ImportError:
            click.echo("❌ uvicorn is not installed. Please install it with: pip install uvicorn")
        except Exception as e:
            click.echo(f"❌ Failed to start server: {e}")
    
    
    if __name__ == '__main__':
        cli()

except ImportError:
    # Fallback when click is not available
    def cli():
        print("CLI dependencies not installed. Please install with: pip install click tabulate")
    
    if __name__ == '__main__':
        cli()