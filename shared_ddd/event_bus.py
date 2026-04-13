"""
Shared DDD Event Bus - RabbitMQ Integration
Central event publisher/subscriber for inter-service communication
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Type
from dataclasses import asdict
from datetime import datetime
import pika
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)


class EventBusConfig:
    """Configuration for event bus"""
    
    def __init__(self,
                 rabbitmq_url: str = "amqp://guest:guest@localhost:5672/",
                 exchange_name: str = "health_platform_events",
                 prefetch_count: int = 10,
                 auto_ack: bool = False):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.prefetch_count = prefetch_count
        self.auto_ack = auto_ack


class IEventPublisher(ABC):
    """Abstract event publisher interface"""
    
    @abstractmethod
    def publish(self, event: 'DomainEvent', routing_key: Optional[str] = None) -> None:
        """Publish domain event to message bus"""
        pass
    
    @abstractmethod
    def publish_batch(self, events: List['DomainEvent']) -> None:
        """Publish multiple events"""
        pass


class IEventSubscriber(ABC):
    """Abstract event subscriber interface"""
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to specific event type"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        pass
    
    @abstractmethod
    def start_listening(self) -> None:
        """Start listening for events"""
        pass
    
    @abstractmethod
    def stop_listening(self) -> None:
        """Stop listening for events"""
        pass


class RabbitMQEventPublisher(IEventPublisher):
    """RabbitMQ implementation of event publisher"""
    
    def __init__(self, config: EventBusConfig):
        self.config = config
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            connection_params = pika.URLParameters(self.config.rabbitmq_url)
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declare exchange (topic exchange for complex routing)
            self.channel.exchange_declare(
                exchange=self.config.exchange_name,
                exchange_type='topic',
                durable=True
            )
            logger.info(f"Connected to RabbitMQ: {self.config.rabbitmq_url}")
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish(self, event, routing_key: Optional[str] = None) -> None:
        """Publish single event"""
        if not self.channel or self.channel.is_closed:
            self._connect()
        
        # Determine routing key
        if routing_key is None:
            routing_key = event.__class__.__name__
        
        # Serialize event
        event_data = self._serialize_event(event)
        
        try:
            self.channel.basic_publish(
                exchange=self.config.exchange_name,
                routing_key=routing_key,
                body=event_data,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            logger.debug(f"Published event: {routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    def publish_batch(self, events: List) -> None:
        """Publish multiple events"""
        for event in events:
            self.publish(event)
    
    def _serialize_event(self, event) -> str:
        """Serialize domain event to JSON"""
        event_dict = asdict(event) if hasattr(event, '__dataclass_fields__') else event.__dict__
        
        # Handle datetime serialization
        serializable = {}
        for key, value in event_dict.items():
            if isinstance(value, datetime):
                serializable[key] = value.isoformat()
            else:
                serializable[key] = value
        
        return json.dumps(serializable)
    
    def close(self) -> None:
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


class RabbitMQEventSubscriber(IEventSubscriber):
    """RabbitMQ implementation of event subscriber"""
    
    def __init__(self, config: EventBusConfig, service_name: str):
        self.config = config
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.queue_name = f"{service_name}_events_queue"
        self.handlers: Dict[str, List[Callable]] = {}
        self.is_listening = False
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            connection_params = pika.URLParameters(self.config.rabbitmq_url)
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.config.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue (service-specific)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=self.config.prefetch_count)
            
            logger.info(f"Subscriber connected to RabbitMQ: {self.service_name}")
        except AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        # Bind queue to event type routing key
        binding_key = event_type
        self.channel.queue_bind(
            exchange=self.config.exchange_name,
            queue=self.queue_name,
            routing_key=binding_key
        )
        
        logger.info(f"Subscribed to {event_type} for {self.service_name}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            if not self.handlers[event_type]:
                del self.handlers[event_type]
                logger.info(f"Unsubscribed from {event_type}")
    
    def start_listening(self) -> None:
        """Start listening for events"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        def on_message_received(ch, method, properties, body):
            """Callback when message received"""
            try:
                event_data = json.loads(body)
                event_type = method.routing_key
                
                # Call all handlers for this event type
                if event_type in self.handlers:
                    for handler in self.handlers[event_type]:
                        handler(event_data)
                
                # Acknowledge message
                if not self.config.auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                
                logger.debug(f"Processed event: {event_type}")
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                if not self.config.auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=on_message_received,
            auto_ack=self.config.auto_ack
        )
        
        logger.info(f"Started listening for events: {self.service_name}")
        self.channel.start_consuming()
    
    def stop_listening(self) -> None:
        """Stop listening for events"""
        self.is_listening = False
        if self.channel and self.channel.is_consuming:
            self.channel.stop_consuming()
        logger.info(f"Stopped listening for events: {self.service_name}")
    
    def close(self) -> None:
        """Close connection"""
        self.stop_listening()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Subscriber connection closed")


class EventBusFactory:
    """Factory for creating event bus instances"""
    
    _publisher: Optional[RabbitMQEventPublisher] = None
    _subscriber: Optional[RabbitMQEventSubscriber] = None
    _config: Optional[EventBusConfig] = None
    
    @classmethod
    def initialize(cls, config: EventBusConfig) -> None:
        """Initialize event bus with configuration"""
        cls._config = config
    
    @classmethod
    def get_publisher(cls) -> RabbitMQEventPublisher:
        """Get or create event publisher"""
        if cls._publisher is None:
            if cls._config is None:
                cls._config = EventBusConfig()
            cls._publisher = RabbitMQEventPublisher(cls._config)
        return cls._publisher
    
    @classmethod
    def get_subscriber(cls, service_name: str) -> RabbitMQEventSubscriber:
        """Get or create event subscriber"""
        if cls._subscriber is None:
            if cls._config is None:
                cls._config = EventBusConfig()
            cls._subscriber = RabbitMQEventSubscriber(cls._config, service_name)
        return cls._subscriber
    
    @classmethod
    def cleanup(cls) -> None:
        """Cleanup resources"""
        if cls._publisher:
            cls._publisher.close()
            cls._publisher = None
        if cls._subscriber:
            cls._subscriber.close()
            cls._subscriber = None


class InMemoryEventBus:
    """In-memory event bus for development/testing"""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
    
    def publish(self, event, routing_key: Optional[str] = None) -> None:
        """Publish event in-memory"""
        if routing_key is None:
            routing_key = event.__class__.__name__
        
        if routing_key in self.handlers:
            event_data = asdict(event) if hasattr(event, '__dataclass_fields__') else event.__dict__
            for handler in self.handlers[routing_key]:
                handler(event_data)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
