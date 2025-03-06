import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# Set page configuration
st.set_page_config(page_title="Dashboard Kualitas Udara", layout="centered")

# URL langsung ke file CSV di Google Drive
url = "https://drive.google.com/uc?id=1naaH6_WxCXsZr_ym6XM6fwPAF7lsE_zL"

try:
    # Membaca data dari URL
    cleaned_dataframe = pd.read_csv(url)
    st.write("Data berhasil dimuat:")
    st.write(cleaned_dataframe.head())
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

# Create a unique index by adding a counter for duplicate dates
cleaned_dataframe['counter'] = cleaned_dataframe.groupby('tanggal').cumcount()
cleaned_dataframe.set_index(['tanggal', 'counter'], inplace=True)

# Title of the Dashboard
st.markdown('## Dashboard Kualitas Udara', unsafe_allow_html=True)

# Date Range Selector
start_date = cleaned_dataframe.index.get_level_values(0).min().date()
end_date = cleaned_dataframe.index.get_level_values(0).max().date()
date_range = st.date_input("Pilih Rentang Tanggal", [start_date, end_date])

# Convert date_range to proper datetime objects for DataFrame filtering
if len(date_range) == 2:
    start_date, end_date = date_range
    # Convert date objects to datetime with time at beginning and end of day
    start_datetime = pd.Timestamp(datetime.datetime.combine(start_date, datetime.time.min))
    end_datetime = pd.Timestamp(datetime.datetime.combine(end_date, datetime.time.max))
else:
    # Fallback if date range selection is incomplete
    start_datetime = pd.Timestamp(cleaned_dataframe.index.get_level_values(0).min())
    end_datetime = pd.Timestamp(cleaned_dataframe.index.get_level_values(0).max())

def plot_temperature_data(df, start_date, end_date):
    # Check if 'TEMP' column exists
    if 'TEMP' not in df.columns:
        st.error("Kolom 'TEMP' tidak ditemukan dalam DataFrame.")
        return
    
    # Ensure start_date and end_date are within the DataFrame index
    if start_date < df.index.get_level_values(0).min() or end_date > df.index.get_level_values(0).max():
        st.error("Rentang tanggal yang dipilih berada di luar data yang tersedia.")
        return
    
    # Filter data based on selected date range using .loc
    try:
        filtered_df = df.loc[(slice(start_date, end_date), slice(None)), :]
    except KeyError as e:
        st.error(f"Terjadi kesalahan saat memfilter data: {e}")
        return
    
    # Check if filtered data is empty
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk rentang tanggal yang dipilih.")
        return
    
    stations = filtered_df['station'].unique()
    
    # Resample for monthly frequency and calculate mean temperature
    monthly_data = filtered_df.reset_index().groupby(['tanggal']).agg({'TEMP': 'mean'}).resample('M', on='tanggal').mean().reset_index()
    
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
        monthly_station_data = station_data.reset_index().groupby(['tanggal']).agg({'TEMP': 'mean'}).resample('M', on='tanggal').mean()
        plt.plot(monthly_station_data.index, monthly_station_data['TEMP'], label=station, marker='o')
    
    # Annotate global max and min temperatures with arrows only
    plt.annotate('', xy=(global_max_date, global_max_temp),
                 xytext=(global_max_date, global_max_temp + 1),
                 arrowprops=dict(facecolor='red', shrink=0.05))
    
    plt.annotate('', xy=(global_min_date, global_min_temp),
                 xytext=(global_min_date, global_min_temp - 1),
                 arrowprops=dict(facecolor='blue', shrink=0.05))
    
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
