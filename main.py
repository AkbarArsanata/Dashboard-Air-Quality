import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import seaborn as sns
import numpy as np
from windrose import WindroseAxes

# Set page configuration
st.set_page_config(page_title="Dashboard Kualitas Udara", layout="centered")

# URL langsung ke file CSV di Google Drive
url = "https://drive.google.com/uc?id=1naaH6_WxCXsZr_ym6XM6fwPAF7lsE_zL"

try:
    # Membaca data dari URL
    cleaned_dataframe = pd.read_csv(url)
except FileNotFoundError:
    st.error("File tidak ditemukan. Mohon periksa URL.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("File kosong. Mohon periksa file CSV.")
    st.stop()
except pd.errors.ParserError:
    st.error("Terjadi kesalahan dalam memparsing file CSV. Mohon periksa format file.")
    st.stop()
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    st.stop()

# Convert 'tanggal' column to datetime
cleaned_dataframe['tanggal'] = pd.to_datetime(cleaned_dataframe['tanggal'])
# Set 'tanggal' as the index
cleaned_dataframe.set_index('tanggal', inplace=True)

# Urutkan indeks untuk memastikan MultiIndex terurut
cleaned_dataframe.sort_index(inplace=True)

# Title of the Dashboard
st.markdown('## Dashboard Kualitas Udara', unsafe_allow_html=True)

# Date Range Selector
start_date = cleaned_dataframe.index.min().date()
end_date = cleaned_dataframe.index.max().date()
date_range = st.date_input("Pilih Rentang Tanggal", [start_date, end_date])

# Convert date_range to proper datetime objects for DataFrame filtering
if len(date_range) == 2:
    start_date, end_date = date_range
    # Convert date objects to datetime with time at beginning and end of day
    start_datetime = pd.Timestamp(datetime.datetime.combine(start_date, datetime.time.min))
    end_datetime = pd.Timestamp(datetime.datetime.combine(end_date, datetime.time.max))
else:
    # Fallback if date range selection is incomplete
    start_datetime = pd.Timestamp(cleaned_dataframe.index.min())
    end_datetime = pd.Timestamp(cleaned_dataframe.index.max())

def plot_temperature_data(df, start_date, end_date):
    # Check if 'TEMP' column exists
    if 'TEMP' not in df.columns:
        st.error("Kolom 'TEMP' tidak ditemukan dalam DataFrame.")
        return
    
    # Ensure start_date and end_date are within the DataFrame index
    if start_date < df.index.min() or end_date > df.index.max():
        st.error("Rentang tanggal yang dipilih berada di luar data yang tersedia.")
        return
    
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[start_date:end_date]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    stations = filtered_df['station'].unique()
    
    # Resample for monthly frequency and calculate mean temperature
    monthly_data = filtered_df.resample('M')['TEMP'].mean().reset_index()
    
    # Find global max and min temperatures
    global_max_temp = monthly_data['TEMP'].max()
    global_min_temp = monthly_data['TEMP'].min()
    
    # Find dates for global max and min temperatures
    global_max_date = monthly_data[monthly_data['TEMP'] == global_max_temp]['tanggal'].iloc[0]
    global_min_date = monthly_data[monthly_data['TEMP'] == global_min_temp]['tanggal'].iloc[0]
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    for station in stations:
        station_data = filtered_df[filtered_df['station'] == station]
        monthly_station_data = station_data.resample('M')['TEMP'].mean()
        plt.plot(monthly_station_data.index, monthly_station_data, label=station, marker='o')
    
    plt.title('Rata-rata Suhu Tahunan per Stasiun')
    plt.xlabel('Tanggal')
    plt.ylabel('Suhu (°C)')
    plt.legend(title='Stasiun')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(plt)

# Call the plotting function with the filtered data
plot_temperature_data(cleaned_dataframe, start_datetime, end_datetime)

# Function to plot temperature heatmap
def plot_temperature_heatmap(df):
    df['hour'] = df.index.hour
    df['date'] = df.index.date
    
    heatmap_data = df.groupby(['date', 'hour'])['TEMP'].mean().unstack()
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='coolwarm', annot=False, cbar_kws={'label': 'Suhu (°C)'})
    
    plt.title('Heatmap Suhu Rata-rata Berdasarkan Jam')
    plt.xlabel('Jam dalam Sehari')
    plt.ylabel('Tanggal')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    st.pyplot(plt)

# Ensure DataFrame has the required columns
required_columns = ['wd', 'WSPM', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
for col in required_columns:
    if col not in cleaned_dataframe.columns:
        st.error(f"DataFrame harus memiliki kolom '{col}'.")
        st.stop()

# Convert wind direction to degrees
def wind_direction_to_degrees(direction):
    directions = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return directions.get(direction, np.nan)

cleaned_dataframe['wd_deg'] = cleaned_dataframe['wd'].apply(wind_direction_to_degrees)

# Drop rows with NaN values in 'wd_deg' and 'WSPM'
cleaned_dataframe = cleaned_dataframe.dropna(subset=['wd_deg', 'WSPM'])

# Function to plot wind rose
def plot_wind_rose(df):
    fig1 = plt.figure(figsize=(10, 8))
    ax = WindroseAxes.from_ax(fig=fig1)
    ax.bar(df['wd_deg'], df['WSPM'], normed=True, opening=0.8, edgecolor='white')
    ax.set_legend(title="Kecepatan Angin (m/s)")
    ax.set_title("Rata rata kecepatan angin")
    st.pyplot(fig1)

# Plot temperature heatmap
plot_temperature_heatmap(cleaned_dataframe)

# Plot wind rose
plot_wind_rose(cleaned_dataframe)
