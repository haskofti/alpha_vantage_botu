import pandas as pd
import requests
from datetime import datetime
import smtplib
from email.message import EmailMessage

API_KEY = "WJYKTY3DYE8SY60J"  # ← Buraya kendi API anahtarını koy
SYMBOL = "XAUUSD"
EMAIL_GONDER = True
EMAIL_ADRESI = "hafi26@gmail.com"
INTERVALS = {
    "15min": "15min",
    "30min": "30min",
    "60min": "60min",
    "1d": "Daily"
}

def get_data(interval):
    try:
        if interval == "1d":
            function = "TIME_SERIES_DAILY"
        else:
            function = "TIME_SERIES_INTRADAY"

        url = f"https://www.alphavantage.co/query?function={function}&symbol={SYMBOL}&interval={interval}&outputsize=compact&apikey={API_KEY}"
        r = requests.get(url)
        data = r.json()

        if "Time Series" not in str(data):
            print(f"[{interval}] Veri alınamadı:", data)
            return None

        key = list(data.keys())[1]
        df = pd.DataFrame.from_dict(data[key], orient="index")
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        print(f"[{interval}] Veri alındı: İlk: {df.index[0]}, Son: {df.index[-1]}")
        return df
    except Exception as e:
        print(f"[{interval}] Hata:", e)
        return None

def calculate_indicators(df):
    df["ma20"] = df["Close"].rolling(window=20).mean()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["rsi14"] = 100 - (100 / (1 + df["Close"].pct_change().rolling(window=14).mean()))
    return df

def generate_signal(df, interval):
    latest = df.iloc[-1]
    sinyal_sayisi = 0

    if latest["ma20"] > latest["ma50"]: sinyal_sayisi += 1
    if latest["rsi14"] < 30: sinyal_sayisi += 1

    if sinyal_sayisi >= 2:
        entry = latest["Close"]
        tp = entry + (entry * 0.01)
        sl = entry - ((tp - entry) / 4)
        return f"[{interval}] AL\nGiriş: {entry:.2f}\nTP: {tp:.2f}\nSL: {sl:.2f}"
    return f"[{interval}] Sinyal Yok"

def send_email(content):
    if not EMAIL_GONDER:
        return
    try:
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = "XAUUSD Sinyal Raporu"
        msg["From"] = EMAIL_ADRESI
        msg["To"] = EMAIL_ADRESI

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADRESI, "jxdb eksm rumw huqb")
            server.send_message(msg)
        print("✅ Mail gönderildi.")
    except Exception as e:
        print("❌ Mail hatası:", e)

if __name__ == "__main__":
    rapor = f"Sinyal Raporu ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
    for key, val in INTERVALS.items():
        df = get_data(val)
        if df is not None:
            df = calculate_indicators(df)
            rapor += generate_signal(df, key) + "\n"
    print(rapor)
    send_email(rapor)