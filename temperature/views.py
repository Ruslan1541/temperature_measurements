from django.http import JsonResponse, HttpResponse
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
from django.shortcuts import render, redirect

# Replace these with your actual InfluxDB settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = 'eysyl_gzK_cXoZXY0VAyEK3OSHai7B4wtCOD6xrRsrEdIjn5eSrR7QwLb5MDXw94vJcX88XCyxV2A5p9JMpu0w=='
INFLUXDB_ORG = 'GGWP'
INFLUXDB_BUCKET = "temperature_data"

def get_temperature_data(request):
    if not request.user.is_authenticated:
        return redirect('account:login')
    try:
        # Initialize the InfluxDB client
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api: QueryApi = client.query_api()

        # Write the query to retrieve the last 100 points
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "temperature")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 100)
        '''
        tables = query_api.query(query)

        # Extract data points
        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "time": record.get_time(),
                    "value": record.get_value(),
                })

        # Return as JSON response
        return JsonResponse({"data": data}, safe=False)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def temperature_data(request):
    if not request.user.is_authenticated:
        return redirect('account:login')
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()

        # Query to get temperature data
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: -24h)
          |> filter(fn: (r) => r._measurement == "temperature")
          |> keep(columns: ["_time", "_value"])
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 100)
        '''
        tables = query_api.query(query)

        # Parse query results into a list of dictionaries
        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "timestamp": record.get_time(),
                    "temperature": record.get_value(),
                })
        
        # Render data in a template
        return render(request, 'temperature/temperature_list.html', {'readings': data})

    except Exception as e:
        return render(request, 'error.html', {'error': str(e)})
