import os
import datetime
import socket
from sqlalchemy.orm import Session
import google.generativeai as genai
from dotenv import load_dotenv

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_gemini_response(user_message: str, db: Session):
    
    def get_calendar_service():
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                
                flow.redirect_uri = 'http://localhost:8081/'
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print("\nLütfen yetkilendirme için aşağıdaki linke tıklayın:\n")
                print(auth_url)
                print("\n")
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', 8081))
                s.listen(1)
                
                conn, addr = s.accept()
                request = conn.recv(4096).decode('utf-8')
                
                path = ""
                try:
                    path = request.split(' ')[1]
                    mesaj = "Yetkilendirme basarili, bu sekmeyi kapatabilirsiniz."
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(mesaj)}\r\n\r\n{mesaj}"
                    conn.sendall(response.encode('utf-8'))
                except Exception as e:
                    print("Istek islenemedi:", e)
                finally:
                    conn.close()
                    s.close()
                
                if path:
                    flow.fetch_token(authorization_response='http://localhost:8081' + path)
                    creds = flow.credentials

            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)

    def ekle_takvim_etkinligi(baslik: str, baslangic_tarihi: str, bitis_tarihi: str, aciklama: str = "") -> str:
        try:
            service = get_calendar_service()
            
            t_baslangic = baslangic_tarihi.replace(" ", "T").replace("Z", "")
            t_bitis = bitis_tarihi.replace(" ", "T").replace("Z", "")
            
            if "+" not in t_baslangic:
                t_baslangic += "+03:00" 
            if "+" not in t_bitis:
                t_bitis += "+03:00"

            event = {
              'summary': baslik,
              'description': aciklama,
              'start': {
                'dateTime': t_baslangic,
                'timeZone': 'Europe/Istanbul',
              },
              'end': {
                'dateTime': t_bitis,
                'timeZone': 'Europe/Istanbul',
              },
            }

            event_result = service.events().insert(calendarId='primary', body=event).execute()
            return f"Başarılı: '{baslik}' etkinliği kaydedildi. Link: {event_result.get('htmlLink')}"
        
        except Exception as e:
            return f"Hata oluştu: {str(e)}"
    
    bugun = datetime.date.today().strftime("%Y-%m-%d")

    model = genai.GenerativeModel(
        model_name='gemini-3.1-flash-lite', 
        tools=[ekle_takvim_etkinligi],
        system_instruction=(
            "Sen bir kişisel danışmansın.ve Adın haydo ve "
            "Kullanıcıya hitap ederken son derece saygılı ve "
            "çözüm odaklı bir dil kullanırsın. "
            f"Bugünün tarihi: {bugun}. "
            "Sana verilen takvim araçlarını kullanarak kullanıcının takvimine yeni etkinlikler ekleyebilirsin. "
            "Sana bir etkinlik ekleme emri geldiğinde, otomatik olarak 'ekle_takvim_etkinligi' aracını kullanmalısın."
            "Cümlelerin arasına hafif argo kelimler ekle."
            "Eğer kullanıcı sana olan saygısını bozarsa sende ona karşı olan saygını bozabilirsin ve küfürlü olarak konuşursa kesinlikle küfürle karşılık ver "
        )
    )

    chat = model.start_chat(enable_automatic_function_calling=True)
    
    try:
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"Sistem hatası: {str(e)}"