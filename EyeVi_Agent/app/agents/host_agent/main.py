"""
Host Agent - FastAPI Server
Orchestrator agent để điều phối message tới các agent khác
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import os
import logging
import base64
from datetime import datetime

# Import các modules local
from server.host_server import HostServer
from server.a2a_client_manager import FileInfo


import dotenv
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title="Host Agent API",
    description="Orchestrator agent để điều phối message tới các agent khác",
    version="1.0.0"
)

# Khởi tạo host server
host_server = HostServer()

# Models cho request/response
class ChatResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None
    session_id: Optional[str] = None
    clarified_message: Optional[str] = None
    analysis: Optional[str] = None
    data: Optional[str] = None
    status: str = "success"
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str

@app.on_event("startup")
async def startup_event():
    """Khởi tạo khi server start"""
    logger.info("🚀 Host Agent Server đang khởi động...")
    await host_server.initialize()
    logger.info("✅ Host Agent Server đã sẵn sàng!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup khi server shutdown"""
    logger.info("🔄 Host Agent Server đang shutdown...")
    await host_server.cleanup()
    logger.info("✅ Host Agent Server đã shutdown thành công!")

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Host Agent Server đang hoạt động tốt!",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    try:
        # Kiểm tra trạng thái các agent connections
        agent_status = await host_server.check_agents_health()
        
        return HealthResponse(
            status="healthy",
            message=f"Tất cả services hoạt động tốt. Agents: {agent_status}",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(None)
):
    """
    Main endpoint để nhận message từ user và điều phối tới agent phù hợp
    Có thể kèm theo files (ảnh, document) hoặc không
    """
    try:
        logger.info(f"📨 Nhận message từ user: {message[:100]}...")
        
        # Tự động tạo session ID nếu không có
        if not session_id:
            from uuid import uuid4
            session_id = str(uuid4())
            logger.info(f"🆔 Tạo session ID mới: {session_id}")
        
        # Xử lý files nếu có
        processed_files = None
        if files and any(file.filename for file in files):
            processed_files = []
            for file in files:
                if file.filename:  # Kiểm tra file có tồn tại
                    # Đọc file content
                    file_content = await file.read()
                    
                    # Encode thành base64
                    file_base64 = base64.b64encode(file_content).decode('utf-8')
                    
                    # Xác định mime type
                    mime_type = file.content_type or "application/octet-stream"
                    
                    processed_files.append(FileInfo(
                        name=file.filename,
                        mime_type=mime_type,
                        data=file_base64
                    ))
                    
                    logger.info(f"📎 Processed file: {file.filename} ({mime_type}, {len(file_content)} bytes)")
        
        # Xử lý message thông qua host server
        if processed_files:
            # Có files đính kèm
            result = await host_server.process_message_with_files(
                message=message,
                user_id=user_id,
                session_id=session_id,
                files=processed_files
            )
        else:
            # Chỉ có text
            result = await host_server.process_message(
                message=message,
                user_id=user_id,
                session_id=session_id
            )
        
        logger.info(f"✅ Xử lý thành công, agent được sử dụng: {result.get('agent_used', 'None')}")
        
        return ChatResponse(
            response=result["response"],
            agent_used=result.get("agent_used"),
            session_id=result.get("session_id"),
            clarified_message=result.get("clarified_message"),
            analysis=result.get("analysis"),
            data=result.get("data"),
            status="success",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xử lý message: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi khi xử lý message: {str(e)}"
        )



@app.get("/agents/status")
async def get_agents_status():
    """Kiểm tra trạng thái tất cả agents"""
    try:
        status = await host_server.get_all_agents_status()
        return {
            "status": "success",
            "agents": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str, user_id: Optional[str] = None):
    """Lấy lịch sử chat cho session"""
    try:
        if user_id:
            chat_history = await host_server.get_chat_history(user_id, session_id)
        else:
            chat_history = host_server.get_chat_history_fallback(session_id)
        
        if not chat_history:
            return {
                "status": "success",
                "session_id": session_id,
                "user_id": user_id,
                "messages": [],
                "message": "Không có lịch sử chat cho session này"
            }
        
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "messages": chat_history.get_recent_messages(50),
            "created_at": chat_history.created_at.isoformat(),
            "last_updated": chat_history.last_updated.isoformat(),
            "total_messages": len(chat_history.messages)
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}/history")
async def clear_chat_history(session_id: str, user_id: Optional[str] = None):
    """Xóa lịch sử chat cho session"""
    try:
        if user_id:
            await host_server.clear_chat_history(user_id, session_id)
        else:
            host_server.clear_chat_history_fallback(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "message": "Đã xóa lịch sử chat thành công",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear chat history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions/create")
async def create_new_session():
    """Tạo session ID mới"""
    try:
        # Import uuid để tạo session ID
        from uuid import uuid4
        
        # Tạo session ID mới
        new_session_id = str(uuid4())
        
        # Khởi tạo chat history cho session mới
        host_server.a2a_client_manager._ensure_chat_history(new_session_id)
        
        logger.info(f"✅ Đã tạo session mới: {new_session_id}")
        
        return {
            "status": "success",
            "session_id": new_session_id,
            "message": "Session mới đã được tạo thành công",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create new session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_active_sessions():
    """Liệt kê các session đang active"""
    try:
        # Lấy tất cả chat histories từ A2A client manager
        sessions_info = []
        
        for session_id, chat_history in host_server.a2a_client_manager.chat_histories.items():
            sessions_info.append({
                "session_id": session_id,
                "created_at": chat_history.created_at.isoformat(),
                "last_updated": chat_history.last_updated.isoformat(),
                "message_count": len(chat_history.messages),
                "last_message_preview": chat_history.messages[-1]["content"][:100] + "..." if chat_history.messages else ""
            })
        
        return {
            "status": "success",
            "active_sessions": len(sessions_info),
            "sessions": sessions_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Lấy danh sách tất cả sessions của user"""
    try:
        sessions = await host_server.get_user_sessions(user_id)
        
        # Lấy thông tin chi tiết cho từng session
        sessions_info = []
        for session_id in sessions:
            try:
                chat_history = await host_server.get_chat_history(user_id, session_id)
                if chat_history:
                    sessions_info.append({
                        "session_id": session_id,
                        "created_at": chat_history.created_at.isoformat(),
                        "last_updated": chat_history.last_updated.isoformat(),
                        "message_count": len(chat_history.messages),
                        "last_message_preview": chat_history.messages[-1]["content"][:100] + "..." if chat_history.messages else ""
                    })
            except Exception as e:
                logger.warning(f"Cannot get details for session {session_id}: {e}")
                sessions_info.append({
                    "session_id": session_id,
                    "error": "Cannot retrieve details"
                })
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_sessions": len(sessions_info),
            "sessions": sessions_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Lấy config từ environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"🚀 Khởi động Host Agent Server tại {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
