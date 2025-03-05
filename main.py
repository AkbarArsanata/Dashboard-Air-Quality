import streamlit as st
import subprocess
import sys
import os

# Set page configuration
st.set_page_config(page_title="Dashboard Kualitas Udara", layout="centered")

def install_requirements():
    try:
        # Periksa apakah file requirements.txt ada
        if not os.path.isfile("requirements.txt"):
            st.error("File requirements.txt tidak ditemukan.")
            return

        # Jalankan perintah pip install -r requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "Requirement.txt"])
        st.success("Paket berhasil diinstal.")
    except subprocess.CalledProcessError as e:
        st.error(f"Terjadi kesalahan saat menginstal paket: {e}")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

# Panggil fungsi untuk menginstal paket
install_requirements()

# Import paket yang diperlukan setelah instalasi
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from windrose import WindroseAxes
    import seaborn as sns
    import matplotlib.dates as mdates
    st.success("Semua paket berhasil diimpor.")
except ImportError as e:
    st.error(f"Terjadi kesalahan saat mengimpor paket: {e}")

# Load data from CSV
try:
    cleaned_dataframe = pd.read_csv(r"C:/Users/User/Downloads/Submision Analisis Data dengan Python/Dashboard/cleaned_dataframe.csv")
except FileNotFoundError:
    st.error("File not found. Please check the file path.")
    st.stop()

# Convert 'tanggal' column to datetime
cleaned_dataframe['tanggal'] = pd.to_datetime(cleaned_dataframe['tanggal'])

# Set 'tanggal' as the index
cleaned_dataframe.set_index('tanggal', inplace=True)

# Title of the Dashboard
st.markdown('<h1 style="text-align: center;">Dashboard Kualitas Udara</h1>', unsafe_allow_html=True)

# Function to plot temperature data
def plot_temperature_data(df):
    stations = df['station'].unique()
    
    # Resample for monthly frequency and calculate mean temperature
    monthly_data = df.resample('M')['TEMP'].mean().reset_index()
    
    # Find global max and min temperatures
    global_max_temp = monthly_data['TEMP'].max()
    global_min_temp = monthly_data['TEMP'].min()
    
    # Find dates for global max and min temperatures
    global_max_date = monthly_data[monthly_data['TEMP'] == global_max_temp]['tanggal'].iloc[0]
    global_min_date = monthly_data[monthly_data['TEMP'] == global_min_temp]['tanggal'].iloc[0]
    
    # Create plot
    plt.figure(figsize=(14, 8))
    
    for station in stations:
        station_data = df[df['station'] == station]
        monthly_station_data = station_data.resample('M')['TEMP'].mean()
        plt.plot(monthly_station_data.index, monthly_station_data, label=station, marker='o')
    
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

# Function to convert wind direction to degrees
def wind_direction_to_degrees(direction):
    directions = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return directions.get(direction, np.nan)

# Ensure DataFrame has the required columns
required_columns = ['wd', 'WSPM', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
for col in required_columns:
    if col not in cleaned_dataframe.columns:
        st.error(f"DataFrame harus memiliki kolom '{col}'.")
        st.stop()

# Convert wind direction to degrees
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

# Function to plot scatter plot of average pollutant levels vs wind direction
def plot_pollutant_vs_wind_direction(df):
    df = df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'wd']].copy()
    average_pollutants = df.groupby('wd').mean().reset_index()
    
    plt.figure(figsize=(14, 8))
    sns.scatterplot(data=average_pollutants, x='wd', y='PM2.5', label='PM2.5', marker='o')
    sns.scatterplot(data=average_pollutants, x='wd', y='PM10', label='PM10', marker='s')
    sns.scatterplot(data=average_pollutants, x='wd', y='SO2', label='SO2', marker='^')
    sns.scatterplot(data=average_pollutants, x='wd', y='NO2', label='NO2', marker='P')
    sns.scatterplot(data=average_pollutants, x='wd', y='CO', label='CO', marker='D')
    sns.scatterplot(data=average_pollutants, x='wd', y='O3', label='O3', marker='X')
    
    plt.yticks(np.arange(0, average_pollutants[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].max().max() + 300, 300))
    plt.legend(title='Polusi')
    plt.title('Rata rata tingkat polusi berdasarkan arah mata angin')
    plt.xlabel('Mata Angin')
    plt.ylabel('Rata rata tingkat polusi')
    plt.tight_layout()
    st.pyplot(plt)

# Function to plot bar chart of maximum average pollutant levels with wind direction annotations
def plot_max_pollutant_levels(df):
    pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
    averages = []
    directions = []
    
    for pollutant in pollutants:
        max_value = df[pollutant].max()
        max_direction = df.loc[df[pollutant] == max_value, 'wd'].values[0]
        averages.append(max_value)
        directions.append(max_direction)
    
    data = pd.DataFrame({'Polutan': pollutants, 'Rata-rata': averages, 'Arah Angin': directions})
    colors = {
        'PM2.5': 'red',
        'PM10': 'orange',
        'SO2': 'green',
        'NO2': 'blue',
        'CO': 'purple',
        'O3': 'brown'
    }
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(data['Polutan'], data['Rata-rata'], color=[colors[p] for p in data['Polutan']])
    
    # Annotate bars with arrows only
    for bar, direction in zip(bars, data['Arah Angin']):
        yval = bar.get_height()
        plt.annotate('', xy=(bar.get_x() + bar.get_width()/2, yval),
                     xytext=(bar.get_x() + bar.get_width()/2, yval + 100),
                     arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.title('Polutan Tertinggi Berdasarkan Arah Angin')
    plt.xlabel('Jenis Polutan')
    plt.ylabel('Rata-rata Konsentrasi')
    plt.ylim(0, max(averages) + 100)
    plt.legend(bars, data['Polutan'], title='Polutan')
    plt.tight_layout()
    st.pyplot(plt)

# Function to assign clusters based on pollutant levels
def assign_clusters(row):
    pm2_5 = row['PM2.5']
    pm10 = row['PM10']
    so2 = row['SO2']
    no2 = row['NO2']
    co = row['CO']
    o3 = row['O3']

    if (0 <= pm2_5 <= 35 and 0 <= pm10 <= 50 and 0 <= so2 <= 10 and
        0 <= no2 <= 30 and 0 <= co <= 500 and 0 <= o3 <= 50):
        return 'Low Pollution'
    elif (36 <= pm2_5 <= 75 and 51 <= pm10 <= 100 and 11 <= so2 <= 20 and
          31 <= no2 <= 60 and 501 <= co <= 1000 and 51 <= o3 <= 70):
        return 'Moderate Pollution'
    else:
        return 'High Pollution'

# Apply the function to assign clusters
cleaned_dataframe['Cluster'] = cleaned_dataframe.apply(assign_clusters, axis=1)

# Function to plot stacked bar chart of pollution levels at each station
def plot_pollution_levels_by_station(df):
    proportion_df = df.groupby(['station', 'Cluster']).size().unstack(fill_value=0)
    proportion_df = proportion_df.div(proportion_df.sum(axis=1), axis=0)
    
    fig1, ax1 = plt.subplots()
    proportion_df.plot(kind='bar', stacked=True, color=['red', 'orange', 'green'], ax=ax1)
    ax1.set_title('Proportion of Pollution Levels at Each Station')
    ax1.set_xlabel('Station')
    ax1.set_ylabel('Proportion')
    ax1.legend(title='Pollution Level')
    ax1.set_xticklabels(proportion_df.index, rotation=45)
    fig1.tight_layout()
    st.pyplot(fig1)

# Function to plot yearly proportions of pollution levels
def plot_yearly_pollution_levels(df):
    yearly_cluster_counts = df.resample('Y').Cluster.value_counts().unstack().fillna(0)
    yearly_proportions = yearly_cluster_counts.div(yearly_cluster_counts.sum(axis=1), axis=0)
    
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    yearly_proportions.plot(kind='bar', stacked=True, ax=ax2)
    ax2.set_title('Proporsi Tingkat Polusi per Bulan')
    ax2.set_xlabel('Tahun')
    ax2.set_ylabel('Proporsi')
    ax2.legend(title='Pollution Level')
    ax2.set_xticks(range(len(yearly_proportions.index)))
    ax2.set_xticklabels(yearly_proportions.index.strftime('%Y'), rotation=45)
    fig2.tight_layout()
    st.pyplot(fig2)

# Function to plot pie chart of average pollutant concentrations
def plot_average_pollutant_concentrations(df):
    average_pollutants = df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean()
    custom_colors = ['#FF9999','#66B3FF','#99FF99','#FFCC99','#C2C2F0','#FF6666']
    
    fig3, ax3 = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax3.pie(
        average_pollutants,
        labels=average_pollutants.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=custom_colors,
        wedgeprops=dict(width=0.3, edgecolor='w')
    )
    ax3.set_title('Proporsi Konsentrasi Polutan')
    ax3.legend(wedges, average_pollutants.index, title="Polutan", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    fig3.tight_layout()
    st.pyplot(fig3)

# Function to plot monthly averages of pollutants
def plot_monthly_pollutant_averages(df):
    monthly_avg = df.resample('M').agg({
        'PM2.5': 'mean',
        'PM10': 'mean',
        'SO2': 'mean',
        'NO2': 'mean',
        'CO': 'mean',
        'O3': 'mean'
    }).reset_index()
    monthly_avg.set_index('tanggal', inplace=True)
    
    fig4, ax4 = plt.subplots(figsize=(14, 8))
    ax4.plot(monthly_avg.index, monthly_avg['PM2.5'], label='PM2.5', marker='o')
    ax4.plot(monthly_avg.index, monthly_avg['PM10'], label='PM10', marker='s')
    ax4.plot(monthly_avg.index, monthly_avg['SO2'], label='SO2', marker='^')
    ax4.plot(monthly_avg.index, monthly_avg['NO2'], label='NO2', marker='P')
    ax4.plot(monthly_avg.index, monthly_avg['CO'], label='CO', marker='*')
    ax4.plot(monthly_avg.index, monthly_avg['O3'], label='O3', marker='X')

    ax4.xaxis.set_major_locator(mdates.YearLocator())
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax4.xaxis.set_minor_locator(mdates.MonthLocator())
    ax4.grid(axis='x', which='both', linewidth=0.1)
    ax4.set_title('Grafik Tahuhan Polutant')
    ax4.set_xlabel('Tahun')
    ax4.set_ylabel('Tingkat Konsentrasi Polutan')
    ax4.legend()
    fig4.tight_layout()
    st.pyplot(fig4)

# Main function to run the dashboard
def main():
    with st.container():
        st.markdown('<h2 style="text-align: center;">Kondisi Temperature Berdasarkan Waktu</h2>', unsafe_allow_html=True)
        plot_temperature_data(cleaned_dataframe)
        plot_temperature_heatmap(cleaned_dataframe)
    
    with st.container():
        st.markdown('<h2 style="text-align: center;">Pengaruh Polusi Berdasarkan Angin</h2>', unsafe_allow_html=True)
        plot_wind_rose(cleaned_dataframe)
        plot_pollutant_vs_wind_direction(cleaned_dataframe)
        plot_max_pollutant_levels(cleaned_dataframe)
    
    with st.container():
        st.markdown('<h2 style="text-align: center;">Hasil Analisis Polusi</h2>', unsafe_allow_html=True)
        plot_pollution_levels_by_station(cleaned_dataframe)
        plot_yearly_pollution_levels(cleaned_dataframe)
        plot_average_pollutant_concentrations(cleaned_dataframe)
        plot_monthly_pollutant_averages(cleaned_dataframe)

if __name__ == "__main__":
    main()
