import os
import datetime
from sqlalchemy.orm import Session
import google.generativeai as genai
from dotenv import load_dotenv
import models

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_gemini_response(user_message: str, db:Session):
    
    def listele_takvim() -> str:

        try:
            etkinlikler = db.query(models.CalendarEvent).order_by(models.CalendarEvent.start_time.asc()).all()
            if not etkinlikler:
                return "Takvim şu an tamamen boş, hiçbir etkinlik bulunmuyor."
            
            sonuc = "Mevcut Takvim Etkinlikleri:\n"
            for e in etkinlikler:
                sonuc += f"- {e.title}: {e.start_time} - {e.end_time} (Açıklama: {e.description or 'Yok'})\n"
            return sonuc
        except Exception as e:
            return f"Hata oluştu: {str(e)}"

    def ekle_takvim(baslik: str, baslangic_tarihi: str , bitis_tarihi: str ,aciklama: str = None) -> str:
        try:

            t_baslangic = baslangic_tarihi.replace(" ", "T").replace("Z", "")
            t_bitis = bitis_tarihi.replace(" ", "T").replace("Z", "")
            
            if "+" in t_baslangic:
                t_baslangic = t_baslangic.split("+")[0]
            if "+" in t_bitis:
                t_bitis = t_bitis.split("+")[0]

            start = datetime.datetime.fromisoformat(t_baslangic)
            end = datetime.datetime.fromisoformat(t_bitis)
            
            yeni_etkinlik = models.CalendarEvent(
                title=baslik,
                description=aciklama,
                start_time=start,
                end_time=end
            )
            db.add(yeni_etkinlik)
            db.commit()
            db.refresh(yeni_etkinlik)
            return f"Başarılı: '{baslik}' etkinliği {baslangic_tarihi} tarihine başarıyla kaydedildi."
        except Exception as e:
            print(f"TAKViM HATASI: {str(e)}") 
            return f"Hata oluştu: {str(e)}"
        
    bugun = datetime.date.today().strftime("%Y-%m-%d")

    model = genai.GenerativeModel(
        model_name='models/gemini-3.5-flash',
        tools=[ekle_takvim, listele_takvim], 
        system_instruction=(
            "Sen kişisel bir danışmansın. "
            "kullanıcına hitap ederken her zaman saygılı ol ve"
            "çözüm odaklı bir dil kullan. "
            f"Bugünün tarihi: {bugun}. "
            "Sana verilen takvim araçlarını kullanarak kullanıcının takvimine yeni etkinlikler ekleyebilir "
            "veya mevcut etkinlikleri listeleyebilirsin. Sana bir etkinlik ekleme emri geldiğinde, "
            "tarih ve saati netleştirip otomatik olarak 'ekle_takvim' aracını kullanmalısın."
            "ve sana takvimi listeleye benzer bir komut geldiğinde 'listele_takvim' aracını kullanmalısın."
        )
    )

    chat = model.start_chat(enable_automatic_function_calling=True)
    
    try:
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"Bir hata ile karşılaştım: {str(e)}"