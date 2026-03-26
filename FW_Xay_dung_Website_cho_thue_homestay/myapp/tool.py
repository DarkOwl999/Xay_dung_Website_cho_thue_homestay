import requests
import polyline

class RoutingTool:
    OSRM_URL = "http://router.project-osrm.org/route/v1"
    def __init__(self):
        pass
    def get_route(self, start_lat, start_lng, end_lat, end_lng, mode='driving'):
        try:
            s_lat, s_lng = float(start_lat), float(start_lng)
            e_lat, e_lng = float(end_lat), float(end_lng)
        except ValueError:
            return {'error': 'Tọa độ lỗi.'}
        osrm_mode_map = {
            'driving': 'driving', 
            'cycling': 'bike', 
            'walking': 'foot'
        }
        osrm_profile = osrm_mode_map.get(mode, 'driving')
        coords = f"{s_lng},{s_lat};{e_lng},{e_lat}"
        url = f"{self.OSRM_URL}/{osrm_profile}/{coords}"    
        params = {
            'overview': 'full', 
            'geometries': 'polyline', 
            'steps': 'true',
            'alternatives': 'true' 
        }       
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            if response.status_code == 200 and data.get('code') == 'Ok':
                routes_result = []                
                speeds = {
                    'walking': 5, 
                    'cycling': 30, 
                    'driving': 40  
                }
                speed_kmh = speeds.get(mode, 40)
                for index, route in enumerate(data['routes']):
                    distance_km = route['distance'] / 1000              
                    duration_min = round((distance_km / speed_kmh) * 60)
                    if duration_min < 1: duration_min = 1
                    summary_name = ""
                    if route.get('legs') and len(route['legs']) > 0:
                         summary_name = route['legs'][0].get('summary', '')             
                    if not summary_name:
                        summary_name = f"Tuyến đường {index + 1}"
                    routes_result.append({
                        'id': index,
                        'summary': summary_name,
                        'distance_km': round(distance_km, 2),
                        'duration_min': duration_min,
                        'route_points': polyline.decode(route['geometry'])
                    })
                return {
                    'routes': routes_result, 
                    'mode': mode
                }
            else:
                return {'error': 'Không tìm thấy đường đi nào.'}
        except Exception as e:
            return {'error': f'Lỗi hệ thống: {str(e)}'}
        
class GISSearchTool:
    def __init__(self):
        # Dùng API Nominatim của OpenStreetMap để Geocoding (Miễn phí)
        self.geocode_url = "https://nominatim.openstreetmap.org/search"

    def get_apartments_in_region(self, keyword, apartments_db):
        """
        Thuật toán GIS:
        1. Geocoding: Đổi tên khu vực thành Khung ranh giới (Bounding Box)
        2. Spatial Filter: Lọc các điểm (Căn hộ) nằm lọt trong Khung ranh giới đó.
        """
        # 1. Gọi API để lấy tọa độ vùng
        headers = {'User-Agent': 'MyGISApp/1.0'}
        params = {
            'q': f"{keyword}, TP.HCM, Việt Nam", # Định vị vào TPHCM cho chuẩn
            'format': 'json',
            'limit': 1
        }
        
        try:
            res = requests.get(self.geocode_url, params=params, headers=headers, timeout=5)
            data = res.json()
            
            if data:
                # API trả về Bounding Box dạng: [lat_min, lat_max, lon_min, lon_max]
                bbox = data[0]['boundingbox']
                lat_min, lat_max = float(bbox[0]), float(bbox[1])
                lon_min, lon_max = float(bbox[2]), float(bbox[3])

                # 2. Phân tích không gian: Tìm các căn hộ lọt vào trong Bbox này
                valid_apartments = []
                for apt in apartments_db:
                    # Logic kiểm tra Point nằm trong Bounding Box
                    if (lat_min <= apt.lat <= lat_max) and (lon_min <= apt.lng <= lon_max):
                        valid_apartments.append(apt)
                
                # Nếu tìm thấy theo GIS thì trả về kết quả
                if valid_apartments:
                    return valid_apartments
        except Exception as e:
            print("Lỗi Geocoding:", e)
        
        # 3. Fallback: Lỡ nhập tên đường nhỏ API không ra, thì lọc theo chuỗi (như cũ)
        fallback_results = []
        keyword_lower = keyword.lower()
        for apt in apartments_db:
            if keyword_lower in apt.name.lower() or keyword_lower in apt.address.lower():
                fallback_results.append(apt)
        
        return fallback_results