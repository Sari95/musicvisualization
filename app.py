import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import plotly.express as px

# Scope für Zugriff auf Nutzer-Daten
SCOPE = "user-top-read"

# Secrets aus Streamlit Secrets Manager
CLIENT_ID = st.secrets["SPOTIPY_CLIENT_ID"]
CLIENT_SECRET = st.secrets["SPOTIPY_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["SPOTIPY_REDIRECT_URI"]

# SpotifyOAuth Objekt (nur zur URL-Generierung und Token-Austausch)
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotifycache"  # optional, Token zwischenspeichern
)

st.title("🎵 Dein persönlicher Spotify-Jahresrückblick")

# 1. URL-Parameter auslesen (z.B. ?code=...)
query_params = st.query_params
code = query_params.get("code")

# 2. Wenn wir keinen Token im Session State haben, versuchen wir, ihn mit dem Code zu holen
if "token_info" not in st.session_state:
    if code:
        # Token holen mit Code
        token_info = sp_oauth.get_access_token(code[0], as_dict=True)
        st.session_state["token_info"] = token_info
        # Nach erfolgreichem Token-Austausch Redirect machen, um Query-Parameter zu entfernen
        st.set_query_params(**{})
    else:
        token_info = None
else:
    token_info = st.session_state["token_info"]

# 3. Wenn kein Token vorhanden oder abgelaufen -> Login-Link anzeigen
if not token_info or sp_oauth.is_token_expired(token_info):
    auth_url = sp_oauth.get_authorize_url()
    st.write("Bitte melde dich bei Spotify an, um deine Daten zu sehen:")
    st.markdown(f"[Spotify Login]({auth_url})", unsafe_allow_html=True)
    st.stop()

# 4. Token aus token_info lesen
access_token = token_info["access_token"]

# 5. Spotify-Client mit gültigem Token initialisieren
sp = spotipy.Spotify(auth=access_token)

# --- Ab hier dein Code mit Spotify API Aufrufen ---

time_range = st.selectbox("Zeitraum", ["short_term", "medium_term", "long_term"])

top_tracks = sp.current_user_top_tracks(limit=10, time_range=time_range)

track_names = [t["name"] for t in top_tracks["items"]]
popularities = [t["popularity"] for t in top_tracks["items"]]

df = pd.DataFrame({
    "Track": track_names,
    "Popularity": popularities
})

st.subheader("📋 Deine Top-Tracks")
st.dataframe(df)

fig = px.bar(df, x="Popularity", y="Track", orientation="h",
             title="Beliebtheit deiner Top-Tracks", color="Popularity", height=400)
st.plotly_chart(fig, use_container_width=True)

st.subheader("🎤 Verteilung deiner Lieblingsgenres")

top_artists = sp.current_user_top_artists(limit=20, time_range=time_range)
genre_list = []
for artist in top_artists["items"]:
    genre_list.extend(artist["genres"])

genre_counts = pd.Series(genre_list).value_counts().head(10)

fig2 = px.pie(values=genre_counts.values, names=genre_counts.index,
              title="Deine häufigsten Genres", hole=0.4)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("📅 Erscheinungsjahr deiner Top-Songs – Oldschool oder Charts?")

years = []
track_info = []

for track in top_tracks["items"]:
    release_date = track["album"]["release_date"]
    year = release_date[:4]
    years.append(int(year))
    track_info.append({
        "Track": track["name"],
        "Artist": track["artists"][0]["name"],
        "Album": track["album"]["name"],
        "Release Year": int(year),
        "Popularity": track["popularity"]
    })

df_years = pd.DataFrame(track_info)

fig3 = px.histogram(df_years, x="Release Year", nbins=len(set(years)),
                    title="Veröffentlichungsjahre deiner Top-Songs", color="Release Year")
st.plotly_chart(fig3, use_container_width=True)

csv_data = df_years.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📄 CSV mit Song-Daten herunterladen",
    data=csv_data,
    file_name="top_tracks_by_year.csv",
    mime="text/csv"
)
