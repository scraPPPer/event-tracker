import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

# --- KONFIGURATION ---
# Trage hier deine Daten von Supabase ein (Project URL und Anon Key)
SUPABASE_URL = "https://lmifuvjjopxlkzywsiek.supabase.co"
SUPABASE_KEY = "sb_publishable_32xOVfxRfmT6i26jCvsnpw_BpX-3DsR"

# Verbindung herstellen
@st.cache_resource
def init_connection():
    if "HIER" in SUPABASE_URL: # Schutz, falls du vergessen hast, es zu ändern
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# --- DATENBANK FUNKTIONEN ---
def run_query():
    client = init_connection()
    if not client: return pd.DataFrame()
    
    # Daten holen
    response = client.table("events").select("*").execute()
    return pd.DataFrame(response.data)

def save_entry(name, date_obj, notes):
    client = init_connection()
    if not client: return
    
    data = {
        "event_name": name,
        "event_date": date_obj.strftime("%Y-%m-%d"),
        "notes": notes
    }
    client.table("events").insert(data).execute()

# --- APP ---
st.title("☁️ scraPPPers Event-Tracker")

client = init_connection()

if not client:
    st.error("Bitte trage oben im Code deine Supabase URL und KEY ein!")
else:
    # EINGABE
    with st.expander("Neues Event", expanded=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Was ist passiert?", "Kopfschmerzen")
        date = col2.date_input("Wann?", datetime.date.today())
        notes = st.text_area("Details")
        
        if st.button("Speichern"):
            save_entry(name, date, notes)
            st.success("Gespeichert!")
            st.cache_data.clear() # Daten neu laden erzwingen
            st.rerun()

    st.divider()

    # --- 4. ANALYSE & INTELLIGENZ ---
df = run_query()

if not df.empty:
    # 1. Datenaufbereitung
    df['event_date'] = pd.to_datetime(df['event_date'])
    df = df.sort_values(by='event_date') # Wichtig: Chronologisch sortieren
    
    # Neue Spalten für die Analyse berechnen
    df['Wochentag'] = df['event_date'].dt.day_name()
    df['Monat'] = df['event_date'].dt.month_name()
    df['Jahr'] = df['event_date'].dt.year
    
    # Berechne Tage seit dem letzten Ereignis (Intervall)
    df['Tage_seit_letztem'] = df['event_date'].diff().dt.days

    # --- DASHBOARD ---
    st.divider()
    st.header("📊 Deine Analyse")
    
    # KPIs (Key Performance Indicators)
    col1, col2, col3 = st.columns(3)
    col1.metric("Gesamtanzahl", len(df))
    
    if len(df) > 1:
        avg_days = df['Tage_seit_letztem'].mean()
        last_event = df['event_date'].iloc[-1].strftime("%d.%m.%Y")
        col2.metric("Durchschn. Abstand", f"{avg_days:.1f} Tage")
        col3.metric("Letztes Ereignis", last_event)
    
    # --- VISUALISIERUNG 1: Die "Mittwochs im Mai"-Matrix ---
    st.subheader("Wann passiert es am häufigsten?")
    st.caption("Je dunkler das Feld, desto mehr Ereignisse.")
    
    # Wir erstellen eine Kreuztabelle (Heatmap-Daten)
    # Zeilen: Wochentage, Spalten: Monate
    heatmap_data = pd.crosstab(
        df['Wochentag'], 
        df['Monat']
    )
    
    # Wochentage sortieren (damit Montag oben ist, nicht alphabetisch)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # Nur sortieren, wenn die Tage auch in den Daten vorkommen
    existing_days = [d for d in days_order if d in heatmap_data.index]
    heatmap_data = heatmap_data.reindex(existing_days)
    
    # Als bunte Tabelle anzeigen (Streamlit highlight_max)
    st.dataframe(heatmap_data.style.background_gradient(cmap="Blues"), use_container_width=True)

    # --- VISUALISIERUNG 2: Verlauf ---
    st.subheader("Zeitlicher Verlauf")
    st.line_chart(df.set_index('event_date')['event_name'].value_counts().resample('D').sum().fillna(0))

    # --- ROHDATEN ---
    with st.expander("Alle Daten anzeigen"):
        st.dataframe(df)

else:
    st.info("Noch keine Daten vorhanden. Trage oben dein erstes Ereignis ein!")