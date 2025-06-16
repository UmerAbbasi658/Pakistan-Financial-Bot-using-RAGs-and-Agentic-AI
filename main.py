from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from agents.stock_agent import handle_stock_query
from agents.economy_agent import handle_economy_query
from utils.email_utils import send_email_with_attachments
from groq import Groq
import os
from dotenv import load_dotenv
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="templates")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

class ChatRequest(BaseModel):
    message: str
    mode: str = "stock"
    chat_history: list = []
    user_email: str | None = None

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    logger.info("Serving index page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Received chat request: {request.model_dump()}")
    if request.mode not in ["stock", "economy"]:
        logger.error(f"Invalid mode: {request.mode}")
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'stock' or 'economy'.")

    try:
        message_lower = request.message.lower()
        # Ultra-simplified email detection
        if any(keyword in message_lower for keyword in ["email", "send", "mail", "share", "summary", "conversation"]):
            logger.info(f"Email request detected for message: {request.message}")
            if not request.user_email or "@" not in request.user_email:
                logger.info("Requesting user email")
                return {"response": "Please provide your email address to receive the summary. For example, reply with: 'Send to user@example.com'."}
            else:
                logger.info(f"Generating email summary for {request.user_email}")
                system_prompt = """
                You are an assistant that generates professional email content and summaries for a chatbot focused on Pakistan's stock market and economy. Given the chat history and mode (stock or economy), create:
                1. A clear email subject (e.g., 'Pakistan Stock Market Chat Summary').
                2. A professional email body summarizing the conversation in simple terms, including key points.
                3. A PDF filename for the chat history summary (e.g., 'chat_summary_2025.pdf').
                Provide the response as a JSON object with fields: subject, body, pdf_filename.
                """
                try:
                    groq_response = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Mode: {request.mode}\nChat History: {json.dumps(request.chat_history)}"}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    email_data = json.loads(groq_response.choices[0].message.content)
                    logger.info(f"Email data generated: {email_data}")
                except Exception as e:
                    logger.error(f"Groq email generation error: {str(e)}")
                    raise Exception(f"Failed to generate email content: {str(e)}")

                pdf_path = f"data/temp_attachments/{email_data['pdf_filename']}"
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                from utils.email_utils import generate_pdf
                logger.info(f"Generating PDF at {pdf_path}")
                try:
                    generate_pdf(request.chat_history, pdf_path)
                except Exception as e:
                    logger.error(f"PDF generation failed: {str(e)}")
                    raise Exception(f"PDF generation failed: {str(e)}")

                try:
                    send_email_with_attachments(
                        to_email=request.user_email,
                        subject=email_data["subject"],
                        body=email_data["body"],
                        attachments=[pdf_path]
                    )
                    logger.info(f"Email sent to {request.user_email}")
                except Exception as e:
                    logger.error(f"Email sending failed: {str(e)}")
                    raise Exception(f"Email sending failed: {str(e)}")
                return {"response": f"Summary sent to {request.user_email}."}

        if request.mode == "stock":
            response = handle_stock_query(request.message)
        else:
            response = handle_economy_query(request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {"response": f"Error processing request: {str(e)}"}
    
# Local development entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)