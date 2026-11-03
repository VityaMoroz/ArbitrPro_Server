from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import re
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = "9031960778:AAEbIR1vGdSfnI4-bGgmuk9IBLJLeBjUQAc"
CHAT_ID = "696713898"

class Lead(BaseModel):
    lead_type: str
    name: str
    phone: str
    company: str = ""
    comment: str = ""
    source: str = ""
    page_url: str = ""

def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    if len(digits) == 10:
        return "+7" + digits
    return "+" + digits

@app.post("/api/lead")
async def create_lead(lead: Lead):
    phone = normalize_phone(lead.phone)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    is_partner = lead.lead_type == "referral_partner"
    
    if is_partner:
        type_text = "🤝 <b>АРБИТРАЖНЫЙ ПАРТНЕР</b>"
        title = "Заявка на партнерство"
    else:
        type_text = "📞 <b>КЛИЕНТ (Консультация)</b>"
        title = "Заявка на встречу"

    text = (
        f"🆕 <b>{title}</b>\n"
        f"Тип: {type_text}\n\n"
        f"👤 <b>Имя:</b> {lead.name}\n"
        f"📞 <b>Телефон:</b> <a href='tel:{phone}'>{phone}</a>\n"
    )
    
    if lead.company:
        text += f"🏢 <b>Компания:</b> {lead.company}\n"
        
    if lead.comment:
        text += f"💬 <b>Комментарий:</b> {lead.comment}\n"
        
    text += f"\n🌐 <b>Источник:</b> {lead.source or 'Сайт'}\n"
    text += f"🕒 <b>Дата:</b> {date_str}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                raise HTTPException(status_code=500, detail="Telegram error")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
            
    return {"ok": True, "message": "Lead received"}
