"""
Delivery management API endpoints.
"""
from typing import List, Optional
from datetime import datetime

try:
    from fastapi import APIRouter, Depends, HTTPException, status, Query
    from pydantic import BaseModel, Field
    
    from ....domain.value_objects.delivery import DeliveryId
    from ....domain.value_objects.notification import NotificationId
    from ...dependencies import get_delivery_repository
    
    router = APIRouter()
    
    
    class DeliveryResponse(BaseModel):
        """Delivery response model."""
        id: str = Field(description="Delivery ID")
        notification_id: str = Field(description="Notification ID")
        channel: str = Field(description="Delivery channel")
        provider: str = Field(description="Provider used")
        status: str = Field(description="Delivery status")
        attempts: int = Field(description="Number of delivery attempts")
        created_at: str = Field(description="Creation timestamp")
        completed_at: Optional[str] = Field(None, description="Completion timestamp")
    
    
    class DeliveryStatisticsResponse(BaseModel):
        """Delivery statistics response model."""
        period_days: int = Field(description="Statistics period in days")
        total_deliveries: int = Field(description="Total number of deliveries")
        successful_deliveries: int = Field(description="Number of successful deliveries")
        failed_deliveries: int = Field(description="Number of failed deliveries")
        pending_deliveries: int = Field(description="Number of pending deliveries")
        success_rate: float = Field(description="Success rate percentage")
        average_delivery_time: Optional[float] = Field(None, description="Average delivery time in seconds")
        provider_statistics: dict = Field(description="Statistics by provider")
    
    
    @router.get("/{delivery_id}", response_model=DeliveryResponse)
    async def get_delivery(
        delivery_id: str,
        delivery_repository = Depends(get_delivery_repository)
    ):
        """Get delivery by ID."""
        try:
            delivery = await delivery_repository.get_by_id(DeliveryId(delivery_id))
            
            if not delivery:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
            
            return DeliveryResponse(
                id=delivery.id.value,
                notification_id=delivery.notification.id.value,
                channel=delivery.channel,
                provider=delivery.provider,
                status=delivery.status.value,
                attempts=len(delivery.attempts),
                created_at=delivery.created_at.isoformat(),
                completed_at=delivery.completed_at.isoformat() if delivery.completed_at else None
            )
            
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
    @router.get("/notification/{notification_id}", response_model=List[DeliveryResponse])
    async def get_deliveries_by_notification(
        notification_id: str,
        delivery_repository = Depends(get_delivery_repository)
    ):
        """Get all deliveries for a specific notification."""
        try:
            deliveries = await delivery_repository.get_by_notification(NotificationId(notification_id))
            
            return [
                DeliveryResponse(
                    id=delivery.id.value,
                    notification_id=delivery.notification.id.value,
                    channel=delivery.channel,
                    provider=delivery.provider,
                    status=delivery.status.value,
                    attempts=len(delivery.attempts),
                    created_at=delivery.created_at.isoformat(),
                    completed_at=delivery.completed_at.isoformat() if delivery.completed_at else None
                )
                for delivery in deliveries
            ]
            
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
    @router.get("/statistics/summary", response_model=DeliveryStatisticsResponse)
    async def get_delivery_statistics(
        days: int = Query(7, description="Number of days for statistics", ge=1, le=365),
        delivery_repository = Depends(get_delivery_repository)
    ):
        """Get delivery statistics for the specified period."""
        try:
            stats = await delivery_repository.get_statistics(days=days)
            
            return DeliveryStatisticsResponse(**stats)
            
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    
    @router.get("/retries/pending", response_model=List[DeliveryResponse])
    async def get_pending_retries(
        delivery_repository = Depends(get_delivery_repository)
    ):
        """Get deliveries that are pending retry."""
        try:
            deliveries = await delivery_repository.get_pending_retries()
            
            return [
                DeliveryResponse(
                    id=delivery.id.value,
                    notification_id=delivery.notification.id.value,
                    channel=delivery.channel,
                    provider=delivery.provider,
                    status=delivery.status.value,
                    attempts=len(delivery.attempts),
                    created_at=delivery.created_at.isoformat(),
                    completed_at=delivery.completed_at.isoformat() if delivery.completed_at else None
                )
                for delivery in deliveries
            ]
            
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

except ImportError:
    # Mock router for when FastAPI is not available
    class MockRouter:
        def get(self, path: str, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    router = MockRouter()