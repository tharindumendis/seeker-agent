# FastAPI Web Interface - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd D:\DEV\ML\Project-Enso-Full\Project-Enso-Framework\temp_plan\Seeker
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python run_web.py
```

### 3. Open Browser

Navigate to: **http://localhost:8000**

## 📍 URLs

- **Web Interface**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## 🎯 Features

### Chat Interface

- Type messages and get AI responses
- See agent's reasoning process
- View tool executions in real-time
- Dark/Light theme toggle

### Memory Management

- View memory status in sidebar
- Clear memory with one click
- Summarize and save to Agent_Insight

### Tools

- View all 13+ available tools
- See tool descriptions and parameters
- Quick action buttons for common tasks

## 🔧 API Endpoints

- `POST /api/chat` - Send message
- `GET /api/tools` - List tools
- `GET /api/memory` - Memory status
- `POST /api/memory/clear` - Clear memory
- `POST /api/memory/summarize` - Summarize
- `WS /ws/chat` - WebSocket chat

## 📝 Usage Tips

1. **Quick Actions**: Use sidebar buttons for common tasks
2. **Theme**: Click 🌙/☀️ to toggle dark/light mode
3. **Keyboard**: Press Enter to send, Shift+Enter for new line
4. **Memory**: Regularly summarize to save important info
5. **Tools**: Click "🔧 Tools" to see all capabilities

## 🎨 Interface

- **Modern Design**: Clean, professional UI
- **Responsive**: Works on desktop and mobile
- **Animations**: Smooth message transitions
- **Accessible**: Keyboard navigation support

---

**Ready to use!** Just run `python run_web.py` and open http://localhost:8000
