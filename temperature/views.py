
from django.http import JsonResponse, HttpResponse
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from django.shortcuts import render, redirect
from django.conf import settings
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
matplotlib.use('Agg')

INFLUXDB_URL = settings.INFLUXDB["url"]
INFLUXDB_TOKEN = settings.INFLUXDB["token"]
INFLUXDB_ORG = settings.INFLUXDB["org"]
INFLUXDB_BUCKET_TEMP = settings.INFLUXDB["bucket_temperature"]
INFLUXDB_BUCKET_PRES = settings.INFLUXDB["bucket_pressure"]

def fetch_temperature_data():
    """Fetches the temperature data from InfluxDB."""
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        query_api = client.query_api()
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET_TEMP}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "temperature")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 100)
        '''
        return query_api.query(query)
    except Exception as e:
        raise RuntimeError(f"Error fetching data from InfluxDB: {e}")
    
def fetch_pressure_data():
    """Fetches the pressure data from InfluxDB."""
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        query_api = client.query_api()
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET_PRES}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "pressure")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 100)
        '''
        return query_api.query(query)
    except Exception as e:
        raise RuntimeError(f"Error fetching data from InfluxDB: {e}")

def serve_plot(request):
    """Generates a temperature and pressure plot and serves it as a PNG image."""
    try:
        tables = fetch_temperature_data()
        pres_tables = fetch_pressure_data()

        temp_times, temperatures, pressures = [], [], []
        for table in tables:
            for record in table.records:
                temp_times.append(record.get_time())
                temperatures.append(record.get_value())
        
        pres_times, pressures = [], []
        for table in pres_tables:
            for record in table.records:
                pres_times.append(record.get_time())
                pressures.append(record.get_value())

        fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(16, 10))
        
        ax[0].plot(temp_times, temperatures, label="Temperature (°C)", color="blue")
        ax[0].set_xlabel("Time")
        ax[0].set_ylabel("Temperature (°C)")
        ax[0].set_title("Temperature Over the Last 24 Hours")
        ax[0].legend()
        ax[0].grid(True)
        
        ax[1].plot(pres_times, pressures, label="Pressure (Pa)", color="green")
        ax[1].set_xlabel("Time")
        ax[1].set_ylabel("Pressure (Pa)")
        ax[1].set_title("Pressure Over the Last 24 Hours")
        ax[1].legend()
        ax[1].grid(True)

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        return HttpResponse(buffer, content_type="image/png")

    except RuntimeError as e:
        return HttpResponse(f"Error generating plot: {str(e)}", status=500)
    except Exception as e:
        return HttpResponse(f"Unexpected error: {str(e)}", status=500)

def get_temperature_data(request):
    try:
        tables = fetch_temperature_data()

        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "time": record.get_time(),
                    "value": record.get_value(),
                })

        return JsonResponse({"data": data}, safe=True)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=500)

def temperature_data(request):
    if not request.user.is_authenticated:
        return redirect('account:login')
    try:
        tables = fetch_temperature_data()

        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "timestamp": record.get_time(),
                    "temperature": record.get_value(),
                })

        if request.headers.get('x-requested-with') == 'XMLHttpRequest': 
            return JsonResponse({"readings": data})

        return render(request, 'temperature/temperature_list.html', {'readings': data, 'show_devices_header': False})

    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})
    
def pressure_data(request):
    if not request.user.is_authenticated:
        return redirect('account:login')
    try:
        tables = fetch_pressure_data()

        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "timestamp": record.get_time(),
                    "pressure": record.get_value(),
                })


        if request.headers.get('x-requested-with') == 'XMLHttpRequest': 
            return JsonResponse({"readings": data})
        
        return render(request, 'pressure/pressure_list.html', {'readings': data, 'show_devices_header': False})

    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})

def get_pressure_data(request):
    try:
        tables = fetch_pressure_data()

        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "time": record.get_time(),
                    "value": record.get_value(),
                })

        return JsonResponse({"data": data}, safe=True)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=500)