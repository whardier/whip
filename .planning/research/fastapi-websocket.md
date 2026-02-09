# FastAPI WebSocket Implementation Patterns

**Researched:** 2026-02-09
**Confidence:** HIGH (Official FastAPI documentation + verified community patterns)

## Executive Summary

FastAPI provides robust WebSocket support through Starlette's WebSocket implementation with async/await patterns. The framework handles text, JSON, and binary messages natively, supports dependency injection for WebSocket endpoints, and integrates seamlessly with FastAPI's existing routing system. Key considerations include proper connection lifecycle management, choosing between JSON and binary protocols based on performance requirements, implementing appropriate error handling with `WebSocketDisconnect`, and scaling beyond single-process deployments using Redis or similar message brokers.

---

## 1. FastAPI WebSocket Endpoint Setup and Lifecycle

### Basic Endpoint Structure

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept connection
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
```

**Source:** [FastAPI Official Documentation - WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

### Connection Lifecycle Stages

1. **Connection Initiation**: Client initiates HTTP upgrade request
2. **Connection Acceptance**: Server calls `await websocket.accept()` to establish WebSocket connection
3. **Message Exchange**: Bidirectional communication using `receive_*()` and `send_*()` methods
4. **Connection Termination**: Either party closes connection, raising `WebSocketDisconnect` exception

**Key Pattern**: Always call `websocket.accept()` before any other WebSocket operations. The connection remains open until explicitly closed or network failure occurs.

### Dependency Injection Support

WebSocket endpoints support FastAPI's dependency injection system:

```python
from typing import Annotated
from fastapi import Depends, Query, Cookie, WebSocket, WebSocketException, status

async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token

@app.websocket("/items/{item_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    item_id: str,
    q: int | None = None,
    cookie_or_token: Annotated[str, Depends(get_cookie_or_token)] = None,
):
    await websocket.accept()
    # ... connection logic
```

**Supported Parameters:**
- `Depends` - Dependency injection
- `Security` - Authentication/authorization
- `Cookie` - HTTP cookies
- `Header` - HTTP headers
- `Path` - URL path parameters
- `Query` - Query string parameters

**Note**: Browser manufacturers do not allow passing auth headers in WebSocket initialization, requiring workarounds such as token-in-query-string or cookie-based authentication.

**Source:** [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/), [Implementing Auth on a WebSocket with FastAPI](https://peterbraden.co.uk/article/websocket-auth-fastapi/)

---

## 2. Connection Handling and Error Recovery

### Exception Management

**Primary Exception**: `WebSocketDisconnect` - raised when client closes connection

```python
from fastapi import WebSocketDisconnect

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process data
    except WebSocketDisconnect:
        # Handle graceful disconnect
        print(f"Client {client_id} disconnected")
    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {e}")
    finally:
        # Cleanup resources
        await cleanup(client_id)
```

### Error Handling Best Practices

1. **Validate Before Accepting**: Check authentication/authorization before `accept()`
2. **Use Appropriate Close Codes**: Follow RFC 6455 WebSocket close codes
   - `1000` - Normal closure
   - `1001` - Going away
   - `1008` - Policy violation
   - `1011` - Unexpected condition
3. **Implement Timeouts**: Prevent connections from hanging indefinitely
4. **Add Heartbeat Mechanisms**: Detect stale connections early
5. **Provide Meaningful Error Messages**: Aid debugging and monitoring
6. **Clean Up Resources**: Always use `finally` block for resource cleanup
7. **Log Errors**: Enable debugging and monitoring

**Critical Pitfall**: Failing to remove disconnected clients from connection lists causes attempts to send messages to dead connections, leading to errors and potential crashes.

### WebSocketException for Pre-Accept Errors

```python
from fastapi import WebSocketException, status

async def verify_token(token: str):
    if not is_valid(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
```

**Important**: Use `WebSocketException` (not `HTTPException`) for WebSocket-specific errors.

**Sources:**
- [FastAPI Exceptions Reference](https://fastapi.tiangolo.com/reference/exceptions/)
- [FastAPI WebSocket Error Handling](https://www.compilenrun.com/docs/framework/fastapi/fastapi-websockets/fastapi-websocket-error-handling/)
- [Handling WebSocket Disconnections Gracefully](https://hexshift.medium.com/handling-websocket-disconnections-gracefully-in-fastapi-9f0a1de365da)

---

## 3. Message Protocol Design: JSON vs Binary

### Message Types

FastAPI supports three message types:

```python
# Text messages
data = await websocket.receive_text()
await websocket.send_text("Hello")

# JSON messages (auto-serialization)
data = await websocket.receive_json()  # Automatically parses JSON
await websocket.send_json({"type": "update", "value": 42})

# Binary messages
data = await websocket.receive_bytes()
await websocket.send_bytes(b"\x00\x01\x02")
```

### JSON vs Binary: Decision Matrix

| Criterion | JSON | Binary |
|-----------|------|--------|
| **Readability** | High - human-readable, easy debugging | Low - requires tools to inspect |
| **Payload Size** | Larger - text encoding overhead | Smaller - compact encoding |
| **Performance** | Slower - JSON parsing overhead | Faster - no parsing overhead |
| **Type Safety** | Lower - string-based types | Higher - strict schemas |
| **Compatibility** | Excellent - universal support | Good - requires schema agreement |
| **Best For** | General apps, debugging, rapid development | High-frequency, low-latency, large data |

### Protocol Design Recommendations

**Use JSON when:**
- Building MVP or prototyping
- Message frequency < 10/sec per connection
- Human readability matters for debugging
- Client diversity (web, mobile, desktop)
- Payload sizes < 1KB

**Use Binary when:**
- High-frequency updates (>50 messages/sec)
- Low-latency requirements (<50ms)
- Large payloads (audio, video, sensor data)
- Bandwidth-constrained environments
- Strict type safety needed

**Hybrid Approach** (Advanced):
Implement dual-path communication where critical real-time data uses binary frames and auxiliary/control messages use JSON. This balances performance and maintainability.

```python
async def handle_message(websocket: WebSocket):
    # Receive generic message
    message = await websocket.receive()

    if message["type"] == "websocket.receive":
        if "text" in message:
            # Handle JSON/text message
            data = json.loads(message["text"])
        elif "bytes" in message:
            # Handle binary message
            data = parse_binary(message["bytes"])
```

### receive_json() Details

- Validates connection state before receiving
- Accepts either text or binary frames (configurable via `mode` parameter)
- Automatically applies `json.loads()` to received data
- Default mode is text frame
- Raises `WebSocketDisconnect` on disconnect

**Sources:**
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [Implementing Custom WebSocket Message Protocols](https://hexshift.medium.com/implementing-custom-websocket-message-protocols-in-fastapi-84ef3ebbf003)
- [How to Handle WebSocket Binary Messages](https://oneuptime.com/blog/post/2026-01-24-websocket-binary-messages/view)

---

## 4. Async/Await Patterns for WebSocket Handlers

### Core Async Pattern

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Await incoming message (non-blocking)
            message = await websocket.receive_text()

            # Process (can await other async operations)
            result = await process_message(message)

            # Send response (non-blocking)
            await websocket.send_text(result)
    except WebSocketDisconnect:
        pass
```

**Key Principles:**
- All WebSocket operations (`accept`, `receive_*`, `send_*`) must be awaited
- Use `async def` for WebSocket endpoint functions
- FastAPI's async support enables handling thousands of concurrent connections efficiently
- Python's `asyncio` prevents blocking the event loop

### ConnectionManager Pattern (Multi-Client)

```python
from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Send to individual
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            # Broadcast to all
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left")
```

### Async Best Practices

1. **Avoid Blocking Operations**: Never use synchronous I/O in WebSocket handlers
   ```python
   # BAD - blocks event loop
   def sync_db_query():
       return db.query()

   # GOOD - non-blocking
   async def async_db_query():
       return await db_pool.fetch_one()
   ```

2. **Offload CPU-Intensive Tasks**: Use thread/process pools for heavy computation
   ```python
   import asyncio
   from concurrent.futures import ProcessPoolExecutor

   executor = ProcessPoolExecutor()

   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       while True:
           data = await websocket.receive_bytes()
           # Offload CPU-intensive work
           result = await asyncio.get_event_loop().run_in_executor(
               executor, process_image, data
           )
           await websocket.send_bytes(result)
   ```

3. **Minimize Memory Allocations**: Keep coroutines lightweight, yield control frequently

4. **Graceful Shutdown**: Implement cleanup for active connections
   ```python
   @app.on_event("shutdown")
   async def shutdown_event():
       for connection in manager.active_connections:
           await connection.close()
   ```

**Sources:**
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [Building Real-Time Applications with FastAPI WebSockets (2025)](https://dev-faizan.medium.com/building-real-time-applications-with-fastapi-websockets-a-complete-guide-2025-40f29d327733)
- [Real-time Communication in Python with WebSockets and FastAPI](https://leapcell.io/blog/real-time-communication-in-python-with-websockets-and-fastapi)

---

## 5. Broadcasting vs Point-to-Point Communication

### Point-to-Point (Direct Messaging)

```python
class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket

    async def send_to_user(self, user_id: str, message: str):
        if user_id in self.connections:
            await self.connections[user_id].send_text(message)
```

**Use Cases:**
- Direct messages between users
- User-specific notifications
- Private data updates
- Session-specific state

### Broadcasting (One-to-Many)

```python
class ConnectionManager:
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Clean up failed connections
        for conn in disconnected:
            self.active_connections.remove(conn)
```

**Use Cases:**
- Chat rooms
- Live notifications/alerts
- Real-time dashboards
- Collaborative editing
- Live sports scores

### Scaling Beyond Single Process

**Problem**: In-memory ConnectionManager only works with single process. Production deployments use multiple workers.

**Solution**: External message broker for cross-worker communication.

#### Redis Pub/Sub Architecture

```python
import aioredis
from fastapi import FastAPI, WebSocket

app = FastAPI()
redis = None

@app.on_event("startup")
async def startup():
    global redis
    redis = await aioredis.create_redis_pool("redis://localhost")

class RedisConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def broadcast_local(self, message: str):
        """Broadcast to connections on THIS worker"""
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_global(self, message: str):
        """Broadcast across ALL workers via Redis"""
        await redis.publish("chat", message)

    async def listen_redis(self):
        """Subscribe to Redis and relay to local connections"""
        channel = (await redis.subscribe("chat"))[0]
        while True:
            message = await channel.get()
            if message:
                await self.broadcast_local(message.decode())

# Start Redis listener on startup
@app.on_event("startup")
async def start_listener():
    asyncio.create_task(manager.listen_redis())
```

**Architecture**:
1. Client connects to any FastAPI worker (via Nginx load balancer)
2. Worker maintains local WebSocket connections
3. When broadcasting, worker publishes to Redis channel
4. All workers subscribe to Redis channel
5. Each worker receives message and broadcasts to its local connections

**Alternative Brokers**:
- **Redis Streams**: Better for ordered message history
- **NATS**: Lightweight, high-performance messaging
- **Apache Kafka**: Enterprise-scale event streaming
- **RabbitMQ**: Advanced routing patterns
- **encode/broadcaster**: Python library supporting multiple backends (Redis, PostgreSQL, Kafka)

#### Channel-Based Broadcasting (Advanced)

```python
class ChannelManager:
    def __init__(self):
        self.channels: dict[str, List[WebSocket]] = {}

    async def subscribe(self, channel: str, websocket: WebSocket):
        if channel not in self.channels:
            self.channels[channel] = []
        self.channels[channel].append(websocket)

    async def broadcast_to_channel(self, channel: str, message: str):
        if channel in self.channels:
            for connection in self.channels[channel]:
                await connection.send_text(message)
```

**Use Cases**:
- Topic-based subscriptions
- Room-based chat systems
- Geographic regions
- User groups/teams

### Optimistic UI Pattern

For real-time collaboration, update local UI immediately, then broadcast asynchronously:

```python
async def handle_user_action(websocket: WebSocket, action: dict):
    # 1. Immediately send confirmation to acting user
    await websocket.send_json({"status": "confirmed", "action": action})

    # 2. Broadcast to others (asynchronous)
    await manager.broadcast_global(json.dumps(action))
```

**Benefit**: Perceived latency near zero for the user performing action.

**Sources:**
- [Broadcasting WebSocket Messages Across Instances](https://medium.com/@philipokiokio/broadcasting-websockets-messages-across-instances-and-workers-with-fastapi-9a66d42cb30a)
- [How to Build WebSocket Servers with FastAPI and Redis](https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view)
- [Advanced WebSocket Architectures in FastAPI](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401)
- [encode/broadcaster](https://github.com/encode/broadcaster)

---

## 6. Latency Optimization Techniques

### Core Performance Principles

**Mantra**: "Reduce blocking, reuse resources, avoid redundant work"

### 1. Avoid Synchronous Operations

```python
# BAD - blocks event loop
def get_data():
    return requests.get("https://api.example.com/data")

# GOOD - non-blocking
async def get_data():
    async with httpx.AsyncClient() as client:
        return await client.get("https://api.example.com/data")
```

**Rule**: Use async libraries for all I/O operations (database, HTTP, file system).

### 2. Offload CPU-Intensive Tasks

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor(max_workers=4)

async def handle_image(websocket: WebSocket):
    image_data = await websocket.receive_bytes()

    # Offload to process pool
    result = await asyncio.get_event_loop().run_in_executor(
        executor, process_image, image_data
    )

    await websocket.send_bytes(result)
```

### 3. Connection Management

**Set Connection Limits**: Prevent resource exhaustion
```python
class ConnectionManager:
    MAX_CONNECTIONS = 1000

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1008, reason="Server at capacity")
            return
        await websocket.accept()
        self.active_connections.append(websocket)
```

**Implement Message Size Limits**: Prevent DoS attacks
```python
MAX_MESSAGE_SIZE = 64 * 1024  # 64 KB

async def receive_with_limit(websocket: WebSocket):
    message = await websocket.receive_text()
    if len(message) > MAX_MESSAGE_SIZE:
        await websocket.close(code=1009, reason="Message too large")
        return None
    return message
```

### 4. Heartbeat/Keepalive

Detect stale connections and prevent silent failures:

```python
import asyncio

async def heartbeat(websocket: WebSocket):
    """Send ping every 30 seconds"""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Start heartbeat task
    heartbeat_task = asyncio.create_task(heartbeat(websocket))

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "pong":
                continue  # Heartbeat response
            # Process other messages
    finally:
        heartbeat_task.cancel()
```

**Protocol-Level Ping/Pong**: WebSocket protocol includes built-in ping (0x9) and pong (0xA) frames. The `websockets` library automatically sends pings every 20 seconds and expects pongs within 20 seconds (configurable via `ping_interval` and `ping_timeout`).

**Recommended Interval**: 20-30 seconds for most applications.

### 5. WebSocket Compression

Reduce bandwidth for text/JSON payloads:

```python
# Uvicorn supports permessage-deflate extension
# Enable via configuration or client negotiation
```

**Note**: Compression adds CPU overhead. Best for large text payloads, less useful for small messages or binary data.

### 6. Monitoring and Metrics

Track key performance indicators:

```python
import time
from prometheus_client import Counter, Histogram

ws_connections = Counter('websocket_connections_total', 'Total WebSocket connections')
ws_message_latency = Histogram('websocket_message_latency_seconds', 'Message processing latency')

async def websocket_endpoint(websocket: WebSocket):
    ws_connections.inc()
    await websocket.accept()

    try:
        while True:
            start_time = time.time()
            data = await websocket.receive_text()

            # Process message
            result = await process(data)
            await websocket.send_text(result)

            ws_message_latency.observe(time.time() - start_time)
    finally:
        ws_connections.dec()
```

**Key Metrics**:
- Active connections count
- Message latency (p50, p95, p99)
- Event loop delay
- Memory usage per connection
- Messages per second
- Connection duration

### 7. Scaling Architecture

**Single Worker**: Up to ~10K concurrent connections per core
**Multi-Worker**: Linear scaling with workers, requires Redis/broker for broadcasting
**Horizontal Scaling**: Multiple servers behind load balancer (Nginx with sticky sessions)

```
[Clients] → [Nginx Load Balancer] → [FastAPI Workers] ↔ [Redis Pub/Sub]
                                            ↓
                                      [Database Pool]
```

**Load Balancer Configuration**: Use sticky sessions (IP hash) to route same client to same worker, reducing connection migration overhead.

### 8. Batch Processing

For high-throughput scenarios, batch messages:

```python
import asyncio

async def batch_sender(websocket: WebSocket):
    queue = asyncio.Queue()

    async def sender():
        while True:
            batch = []
            # Collect messages for 10ms
            deadline = asyncio.get_event_loop().time() + 0.01
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=0.01)
                    batch.append(msg)
                except asyncio.TimeoutError:
                    break

            if batch:
                await websocket.send_json({"batch": batch})

    return queue, asyncio.create_task(sender())
```

**Benefit**: Reduces overhead from many small messages, improves throughput at cost of slight latency increase.

**Sources:**
- [Advanced WebSocket Architectures for High Performance](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401)
- [How to Handle Large Scale WebSocket Traffic](https://hexshift.medium.com/how-to-handle-large-scale-websocket-traffic-with-fastapi-9c841f937f39)
- [FastAPI Performance Tuning & Caching Strategy 101](https://blog.greeden.me/en/2026/02/03/fastapi-performance-tuning-caching-strategy-101-a-practical-recipe-for-growing-a-slow-api-into-a-lightweight-fast-api/)
- [WebSocket Heartbeat Implementation](https://oneuptime.com/blog/post/2026-01-27-websocket-heartbeat/view)
- [websockets library keepalive](https://websockets.readthedocs.io/en/stable/topics/keepalive.html)

---

## 7. Static File Serving Alongside WebSocket Endpoints

### Basic Static Files Setup

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve HTML page with WebSocket client
@app.get("/", response_class=HTMLResponse)
async def get():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Test</title>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <input id="messageInput" type="text" />
            <button onclick="sendMessage()">Send</button>
            <ul id="messages"></ul>

            <script>
                const ws = new WebSocket("ws://localhost:8000/ws");

                ws.onmessage = function(event) {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('li');
                    message.textContent = event.data;
                    messages.appendChild(message);
                };

                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    ws.send(input.value);
                    input.value = '';
                }
            </script>
        </body>
    </html>
    """

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # ... WebSocket logic
```

### Project Structure

```
project/
├── main.py              # FastAPI app
├── static/              # Static files directory
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── websocket.js
│   └── index.html
└── requirements.txt
```

### Mounting Multiple Static Directories

```python
# Separate directories for different asset types
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
```

### SPA (Single Page Application) Support

For React, Vue, Angular apps with client-side routing:

```python
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

# Mount SPA build directory
app.mount("/app", StaticFiles(directory="frontend/build", html=True), name="app")

# Fallback to index.html for SPA routing
@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request, exc):
    if exc.status_code == 404 and request.url.path.startswith("/app"):
        return FileResponse("frontend/build/index.html")
    return exc
```

### Production Considerations

**Development**: FastAPI serves static files directly
```bash
uvicorn main:app --reload
```

**Production**: Use Nginx to serve static files, proxy WebSocket and API requests
```nginx
server {
    listen 80;
    server_name example.com;

    # Static files served by Nginx
    location /static/ {
        alias /var/www/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;  # 24 hours for long-lived connections
    }

    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SPA fallback
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

**Benefit**: Nginx efficiently serves static files, reducing load on FastAPI workers.

### CORS Configuration

If frontend and backend on different domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: WebSocket connections respect CORS policies. Ensure WebSocket endpoint origin is allowed.

**Sources:**
- [FastAPI Static Files Documentation](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Developing a Real-time Dashboard with FastAPI](https://testdriven.io/blog/fastapi-postgres-websockets/)
- [FastAPI WebSocket Tutorial](https://github.com/zhiyuan8/FastAPI-websocket-tutorial)

---

## 8. Common Pitfalls and Best Practices

### Critical Pitfalls

#### 1. Memory Leaks from Disconnected Clients

**Problem**: Failing to remove disconnected clients from connection list causes memory leaks and attempts to send to dead connections.

```python
# BAD - no cleanup on disconnect
class ConnectionManager:
    def __init__(self):
        self.connections = []

    async def broadcast(self, message: str):
        for conn in self.connections:
            await conn.send_text(message)  # May fail on dead connections

# GOOD - proper cleanup
class ConnectionManager:
    async def broadcast(self, message: str):
        dead_connections = []
        for conn in self.connections:
            try:
                await conn.send_text(message)
            except Exception:
                dead_connections.append(conn)

        for conn in dead_connections:
            self.connections.remove(conn)
```

**Best Practice**: Always catch `WebSocketDisconnect` and clean up resources in `finally` block.

#### 2. Infinite Loops Without Exit Conditions

**Problem**: Loop continues even after client disconnects if exceptions aren't caught.

```python
# BAD - loop never exits gracefully
@app.websocket("/ws")
async def endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:  # No exit condition
        data = await websocket.receive_text()
        await websocket.send_text(data)

# GOOD - proper exception handling
@app.websocket("/ws")
async def endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        # Cleanup
        await cleanup()
```

#### 3. Using --reload in Production

**Problem**: `--reload` flag spawns autoreloader process not designed for concurrency/reliability.

```bash
# BAD - never use in production
uvicorn main:app --reload

# GOOD - multiple workers
uvicorn main:app --workers 4
# OR with Gunicorn
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

**Formula**: Workers = (2 × CPU cores) + 1

#### 4. Single Process Broadcasting

**Problem**: In-memory connection list only works with single process. Multi-worker deployments need external broker.

```python
# BAD - only works with single worker
class ConnectionManager:
    def __init__(self):
        self.connections = []  # In-memory only

# GOOD - use Redis for multi-worker
import aioredis

class RedisConnectionManager:
    async def broadcast_global(self, message: str):
        await redis.publish("channel", message)
```

**Best Practice**: Use Redis Pub/Sub, NATS, or Kafka for production deployments.

#### 5. Large JSON Payloads Without Flow Control

**Problem**: Sending large payloads frequently overloads clients/server.

```python
# BAD - no size limits
await websocket.send_json(huge_data_object)

# GOOD - implement limits and batching
MAX_MESSAGE_SIZE = 64 * 1024  # 64 KB

async def send_with_limit(websocket: WebSocket, data: dict):
    payload = json.dumps(data)
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("Message too large")
    await websocket.send_text(payload)
```

**Best Practice**:
- Set message size limits
- Implement rate limiting per connection
- Use pagination for large datasets
- Consider binary protocol for large data

#### 6. Authentication in WebSocket Headers

**Problem**: Browsers don't allow custom headers in WebSocket connection initialization.

**Solutions**:
1. **Token in Query String** (most common)
   ```python
   @app.websocket("/ws")
   async def endpoint(websocket: WebSocket, token: str = Query(...)):
       user = await verify_token(token)
       if not user:
           await websocket.close(code=1008)
           return
       await websocket.accept()
   ```

2. **Cookie-Based Authentication**
   ```python
   @app.websocket("/ws")
   async def endpoint(
       websocket: WebSocket,
       session: str = Cookie(None)
   ):
       if not await verify_session(session):
           raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
       await websocket.accept()
   ```

3. **Two-Step Authentication**: Connect first, then send auth message
   ```python
   @app.websocket("/ws")
   async def endpoint(websocket: WebSocket):
       await websocket.accept()

       # Wait for auth message
       auth_msg = await websocket.receive_json()
       if not await verify_auth(auth_msg["token"]):
           await websocket.close(code=1008)
           return

       # Proceed with authenticated connection
       while True:
           data = await websocket.receive_json()
           # ...
   ```

#### 7. Blocking Operations in Event Loop

**Problem**: Synchronous I/O blocks event loop, degrading performance for all connections.

```python
# BAD - blocks event loop
import requests
await websocket.send_text(requests.get("https://api.example.com").text)

# GOOD - use async libraries
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
    await websocket.send_text(response.text)
```

**Best Practice**: Use async versions of all I/O libraries:
- `httpx` instead of `requests`
- `aioredis` instead of `redis-py`
- `asyncpg` or `aiomysql` instead of synchronous DB drivers
- `aiofiles` for file I/O

#### 8. Missing Resource Limits

**Problem**: No connection/message limits enables DoS attacks.

**Best Practices**:
```python
class ConnectionManager:
    MAX_CONNECTIONS = 1000
    MAX_MESSAGE_SIZE = 64 * 1024
    MAX_MESSAGES_PER_MINUTE = 60

    def __init__(self):
        self.connections = []
        self.rate_limits = {}  # user_id -> message count

    async def connect(self, websocket: WebSocket, user_id: str):
        if len(self.connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1008, reason="Server at capacity")
            return False

        await websocket.accept()
        self.connections.append(websocket)
        return True

    async def receive_with_limits(self, websocket: WebSocket, user_id: str):
        # Rate limiting
        if self.rate_limits.get(user_id, 0) >= self.MAX_MESSAGES_PER_MINUTE:
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return None

        message = await websocket.receive_text()

        # Size limiting
        if len(message) > self.MAX_MESSAGE_SIZE:
            await websocket.close(code=1009, reason="Message too large")
            return None

        self.rate_limits[user_id] = self.rate_limits.get(user_id, 0) + 1
        return message
```

#### 9. No Heartbeat/Keepalive

**Problem**: Silent connection failures go undetected, wasting resources.

**Best Practice**: Implement heartbeat mechanism (see Section 6).

#### 10. Using HTTPException in WebSocket Routes

**Problem**: `HTTPException` doesn't work in WebSocket context.

```python
# BAD - wrong exception type
from fastapi import HTTPException

@app.websocket("/ws")
async def endpoint(websocket: WebSocket, token: str = Query(...)):
    if not verify(token):
        raise HTTPException(status_code=401)  # Won't work!

# GOOD - use WebSocketException
from fastapi import WebSocketException, status

@app.websocket("/ws")
async def endpoint(websocket: WebSocket, token: str = Query(...)):
    if not verify(token):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
```

### Best Practices Summary

#### Connection Management
- Always catch `WebSocketDisconnect`
- Use `finally` block for cleanup
- Remove disconnected clients from tracking structures
- Implement connection limits
- Set timeouts for long-running operations

#### Message Handling
- Validate message size and rate
- Use appropriate protocol (JSON vs binary) based on requirements
- Implement flow control for large payloads
- Handle malformed messages gracefully

#### Performance
- Use async I/O for all operations
- Offload CPU-intensive tasks to thread/process pools
- Implement heartbeat mechanism
- Monitor key metrics (connections, latency, memory)
- Use Redis/broker for multi-worker deployments

#### Security
- Authenticate before accepting connection
- Validate all incoming data
- Implement rate limiting
- Use HTTPS/WSS in production
- Set message size limits

#### Deployment
- Use multiple workers (Gunicorn + Uvicorn)
- Configure Nginx for WebSocket proxying
- Enable sticky sessions for load balancing
- Never use `--reload` in production
- Implement graceful shutdown

#### Code Quality
- Use type hints with `Annotated` syntax
- Implement proper error logging
- Write integration tests for WebSocket endpoints
- Document connection lifecycle and message protocols
- Use connection manager pattern for multiple clients

**Sources:**
- [10 Common FastAPI Mistakes That Hurt Performance](https://medium.com/@connect.hashblock/10-common-fastapi-mistakes-that-hurt-performance-and-how-to-fix-them-72b8553fe8e7)
- [Deploying WebSocket Applications with FastAPI](https://hexshift.medium.com/deploying-websocket-applications-built-with-fastapi-using-uvicorn-gunicorn-and-nginx-04249b1cb87d)
- [FastAPI WebSocket Error Handling](https://www.compilenrun.com/docs/framework/fastapi/fastapi-websockets/fastapi-websocket-error-handling/)

---

## 9. Production Deployment Architecture

### Recommended Stack

```
[Clients]
    ↓
[Nginx Load Balancer]
    ↓ (with sticky sessions)
[FastAPI App (Gunicorn + Uvicorn Workers)]
    ↓↔ (pub/sub)
[Redis]
    ↓
[Database (PostgreSQL/etc)]
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use Gunicorn with Uvicorn workers
CMD ["gunicorn", "main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "4", \
     "-b", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30"]
```

### Nginx Configuration

```nginx
upstream fastapi_backend {
    # Use IP hash for sticky sessions (same client -> same worker)
    ip_hash;

    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name example.com;

    # WebSocket endpoint
    location /ws {
        proxy_pass http://fastapi_backend;

        # WebSocket-specific headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-lived connections
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # API endpoints
    location /api {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (served directly by Nginx)
    location /static {
        alias /var/www/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Environment Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379"

    # WebSocket
    max_connections: int = 1000
    max_message_size: int = 64 * 1024  # 64 KB
    heartbeat_interval: int = 30  # seconds

    # Workers
    workers: int = 4

    class Config:
        env_file = ".env"

settings = Settings()
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "redis": await check_redis_connection()
    }
```

### Monitoring

```python
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

# Metrics
ws_connections_active = Gauge('websocket_connections_active', 'Active WebSocket connections')
ws_connections_total = Counter('websocket_connections_total', 'Total WebSocket connections')
ws_messages_sent = Counter('websocket_messages_sent_total', 'Total messages sent')
ws_messages_received = Counter('websocket_messages_received_total', 'Total messages received')
ws_message_latency = Histogram('websocket_message_latency_seconds', 'Message processing latency')

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**Sources:**
- [Deploying WebSocket Applications with FastAPI](https://hexshift.medium.com/deploying-websocket-applications-built-with-fastapi-using-uvicorn-gunicorn-and-nginx-04249b1cb87d)
- [FastAPI Server Workers Documentation](https://fastapi.tiangolo.com/deployment/server-workers/)
- [FastAPI Production Deployment Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)

---

## Conclusion

FastAPI provides robust, production-ready WebSocket support with async/await patterns, dependency injection, and seamless integration with the broader FastAPI ecosystem. Key takeaways:

1. **Connection Lifecycle**: Accept, communicate, handle disconnect gracefully
2. **Protocol Choice**: JSON for simplicity, binary for performance
3. **Async Patterns**: Keep coroutines lightweight, avoid blocking operations
4. **Broadcasting**: Use Redis/broker for multi-worker deployments
5. **Performance**: Implement limits, heartbeats, monitoring
6. **Static Files**: FastAPI serves in dev, Nginx in production
7. **Avoid Pitfalls**: Clean up disconnections, use proper exceptions, never use `--reload` in production
8. **Production**: Gunicorn + Uvicorn workers behind Nginx with sticky sessions

**Confidence Level**: HIGH - All recommendations based on official FastAPI documentation and verified community patterns from 2025-2026.

---

## Sources

### Official Documentation
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Exceptions Reference](https://fastapi.tiangolo.com/reference/exceptions/)
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/)
- [Starlette WebSocket Documentation](https://www.starlette.dev/websockets/)
- [websockets Library - Keepalive](https://websockets.readthedocs.io/en/stable/topics/keepalive.html)

### Community Guides and Tutorials
- [Getting Started with FastAPI WebSockets - Better Stack](https://betterstack.com/community/guides/scaling-python/fastapi-websockets/)
- [Building Real-Time Applications with FastAPI WebSockets (2025)](https://dev-faizan.medium.com/building-real-time-applications-with-fastapi-websockets-a-complete-guide-2025-40f29d327733)
- [Broadcasting WebSocket Messages Across Instances](https://medium.com/@philipokiokio/broadcasting-websockets-messages-across-instances-and-workers-with-fastapi-9a66d42cb30a)
- [Developing a Real-time Dashboard with FastAPI](https://testdriven.io/blog/fastapi-postgres-websockets/)

### Advanced Architectures and Performance
- [Advanced WebSocket Architectures in FastAPI](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401)
- [How to Handle Large Scale WebSocket Traffic](https://hexshift.medium.com/how-to-handle-large-scale-websocket-traffic-with-fastapi-9c841f937f39)
- [Handling WebSocket Disconnections Gracefully](https://hexshift.medium.com/handling-websocket-disconnections-gracefully-in-fastapi-9f0a1de365da)
- [Implementing Custom WebSocket Message Protocols](https://hexshift.medium.com/implementing-custom-websocket-message-protocols-in-fastapi-84ef3ebbf003)
- [FastAPI Performance Tuning & Caching Strategy 101](https://blog.greeden.me/en/2026/02/03/fastapi-performance-tuning-caching-strategy-101-a-practical-recipe-for-growing-a-slow-api-into-a-lightweight-fast-api/)

### Deployment and Production
- [Deploying WebSocket Applications with FastAPI](https://hexshift.medium.com/deploying-websocket-applications-built-with-fastapi-using-uvicorn-gunicorn-and-nginx-04249b1cb87d)
- [FastAPI Production Deployment Best Practices - Render](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Mastering Gunicorn and Uvicorn for FastAPI](https://medium.com/@iklobato/mastering-gunicorn-and-uvicorn-the-right-way-to-deploy-fastapi-applications-aaa06849841e)
- [FastAPI Deployment Guide for 2026](https://www.zestminds.com/blog/fastapi-deployment-guide/)

### Specialized Topics
- [How to Build WebSocket Servers with FastAPI and Redis](https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view)
- [How to Implement Heartbeat/Ping-Pong in WebSockets](https://oneuptime.com/blog/post/2026-01-27-websocket-heartbeat/view)
- [How to Handle WebSocket Binary Messages](https://oneuptime.com/blog/post/2026-01-24-websocket-binary-messages/view)
- [Implementing Auth on a WebSocket with FastAPI](https://peterbraden.co.uk/article/websocket-auth-fastapi/)
- [FastAPI WebSocket Error Handling - Compile N Run](https://www.compilenrun.com/docs/framework/fastapi/fastapi-websockets/fastapi-websocket-error-handling/)

### Common Mistakes and Best Practices
- [10 Common FastAPI Mistakes That Hurt Performance](https://medium.com/@connect.hashblock/10-common-fastapi-mistakes-that-hurt-performance-and-how-to-fix-them-72b8553fe8e7)
- [10 FastAPI Mistakes That Quietly Kill Performance](https://medium.com/@bhagyarana80/10-fastapi-mistakes-that-quietly-kill-performance-5b030cdf8505)
- [Common Mistakes Developers Make While Building FastAPI Applications](https://medium.com/@rameshkannanyt0078/common-mistakes-developers-make-while-building-fastapi-applications-bec0a55fe48f)

### Libraries and Tools
- [encode/broadcaster](https://github.com/encode/broadcaster)
- [fastapi-websocket-pubsub](https://pypi.org/project/fastapi-websocket-pubsub/)
