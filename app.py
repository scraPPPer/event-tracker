import streamlit as st
import pandas as pd
from supabase import create_client
import datetime
from datetime import timedelta

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

# --- 4. ANALYSE & INTELLIGENZ (Version 2.0) ---
df = run_query()

if not df.empty:
    # 1. Datenaufbereitung & Übersetzung
    df['event_date'] = pd.to_datetime(df['event_date'])
    df = df.sort_values(by='event_date')
    
    # Deutsche Namen mapping
    days_de = {
        'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
        'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
    }
    months_de = {
        1: '01 Jan', 2: '02 Feb', 3: '03 Mär', 4: '04 Apr', 5: '05 Mai', 6: '06 Jun',
        7: '07 Jul', 8: '08 Aug', 9: '09 Sep', 10: '10 Okt', 11: '11 Nov', 12: '12 Dez'
    }
    
    # Neue Spalten mit deutschen Werten
    df['Wochentag'] = df['event_date'].dt.day_name().map(days_de)
    df['Monat'] = df['event_date'].dt.month.map(months_de) # Trick: Zahl voranstellen für Sortierung (01 Jan)
    df['Jahr'] = df['event_date'].dt.year
    df['Tage_seit_letztem'] = df['event_date'].diff().dt.days

    st.header("📊 Deep Dive Analyse")

    # --- A. DIE PROGNOSE (KI "Light") ---
    if len(df) >= 2:
        avg_days = df['Tage_seit_letztem'].mean()
        last_date = df['event_date'].iloc[-1]
        # Prognose berechnen
        next_date = last_date + datetime.timedelta(days=avg_days)
        
        # UI für die Prognose
        col1, col2, col3 = st.columns(3)
        col1.metric("Durchschn. Abstand", f"{avg_days:.1f} Tage")
        col2.metric("Letztes Mal", last_date.strftime("%d.%m.%Y"))
        col3.metric("Nächste Prognose", next_date.strftime("%d.%m.%Y"), 
                   delta=f"in ca. {int(avg_days)} Tagen")
    else:
        st.info("Trage mindestens 2 Ereignisse ein, um eine Prognose zu erhalten.")

    st.markdown("---")

    # --- B. MUSTER-ERKENNUNG (HEATMAP) ---
    st.subheader("Wann passiert es am häufigsten? (Heatmap)")
    
    # 1. Daten für Heatmap vorbereiten
    heatmap_data = pd.crosstab(df['Wochentag'], df['Monat'])
    
    # 2. Sortierung erzwingen (Logisch statt Alphabetisch)
    # Liste der Wochentage in korrekter Reihenfolge
    sort_order_days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    # Wir filtern die Liste, damit nur Tage drin sind, die auch Daten haben (verhindert Fehler)
    active_days = [d for d in sort_order_days if d in heatmap_data.index]
    heatmap_data = heatmap_data.reindex(active_days)
    
    # 3. Darstellung (TEST-MODUS: Ohne Farben)
    st.dataframe(heatmap_data, use_container_width=True)
    
    # "Insight" Text generieren (Wo ist das Maximum?)
    if not heatmap_data.empty:
        max_val = heatmap_data.max().max()
        # Finde heraus, wo das Maximum liegt
        max_col = heatmap_data.max(axis=0).idxmax() # Monat
        max_row = heatmap_data.max(axis=1).idxmax() # Tag
        if max_val > 1:
            st.success(f"💡 **Erkenntnis:** Die häufigste Kombination ist **{max_row} im {max_col[3:]}** ({max_val} Mal).")

    # --- C. STATISTIK NACH ZEITRAUM ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("**Häufigkeit nach Jahr**")
        year_counts = df['Jahr'].value_counts().sort_index()
        # Chart configuration für saubere X-Achse (Jahre als Text, nicht Zahl mit Komma)
        st.bar_chart(year_counts)

    with c2:
        st.write("**Saisonalität (Häufigkeit nach Monat)**")
        month_counts = df['Monat'].value_counts().sort_index()
        st.bar_chart(month_counts)

    # --- D. ZEITLICHER VERLAUF (Timeline) ---
    st.subheader("Verlauf der Ereignisse")
    # Wir gruppieren jetzt nach MONAT (M), nicht mehr Tag. Das macht die Kurve lesbarer.
    timeline = df.set_index('event_date').resample('M').size()
    st.area_chart(timeline)

    # --- ROHDATEN ---
    with st.expander("Alle Daten ansehen"):
        st.dataframe(df.sort_values(by='event_date', ascending=False), use_container_width=True)

else:
    st.info("Noch keine Daten vorhanden.")
