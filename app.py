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
st.title("☁️ Cloud Event Tracker")

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

    # ANALYSE
    df = run_query()
    if not df.empty:
        # Datum formatieren
        df['event_date'] = pd.to_datetime(df['event_date'])
        df['Wochentag'] = df['event_date'].dt.day_name()
        
        st.subheader("Deine Statistik")
        st.bar_chart(df['Wochentag'].value_counts())
        
        st.write("Historie:")
        st.dataframe(df)
    else:
        st.info("Noch keine Daten in der Datenbank.")