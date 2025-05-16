import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-top-read",
    client_id=st.secrets["SPOTIPY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIPY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIPY_REDIRECT_URI"]
))

st.title("🎵 Dein persönlicher Spotify-Jahresrückblick")

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

# Interaktive Balkengrafik
fig = px.bar(df, x="Popularity", y="Track", orientation="h",
             title="Beliebtheit deiner Top-Tracks", color="Popularity", height=400)
st.plotly_chart(fig, use_container_width=True)

# Top Genres
st.subheader("🎤 Verteilung deiner Lieblingsgenres")

top_artists = sp.current_user_top_artists(limit=20, time_range=time_range)
genre_list = []

for artist in top_artists["items"]:
    genre_list.extend(artist["genres"])

genre_counts = pd.Series(genre_list).value_counts().head(10)

# Interaktives Pie Chart
fig2 = px.pie(values=genre_counts.values, names=genre_counts.index,
              title="Deine häufigsten Genres", hole=0.4)
st.plotly_chart(fig2, use_container_width=True)

# Veröffentlichungsjahr
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

# Interaktives Histogramm
fig3 = px.histogram(df_years, x="Release Year", nbins=len(set(years)),
                    title="Veröffentlichungsjahre deiner Top-Songs", color="Release Year")
st.plotly_chart(fig3, use_container_width=True)

# CSV Download
csv_data = df_years.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📄 CSV mit Song-Daten herunterladen",
    data=csv_data,
    file_name="top_tracks_by_year.csv",
    mime="text/csv"
)
