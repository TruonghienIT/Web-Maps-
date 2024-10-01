import sqlite3

from flask import Flask, request, jsonify, render_template
import googlemaps
import heapq
import time
from datetime import datetime

app = Flask(__name__)

# Thay YOUR_API_KEY bằng API Key của bạn
gmaps = googlemaps.Client(key='AIzaSyBnJKzKGqg4qjRpV_zFdrOxIoB4mOlXKJU')

time_start = time.time()
def heuristic(a, b):
    """ Ước lượng chi phí giữa hai điểm (đơn giản là khoảng cách Euclidean). """
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def a_star(start, goal, graph): #thuật toán này nhận vào 1 điểm start, điểm kết thúc goal và một đồ thị graph đại diện cho mạng lười đường đi (Các nút và đoạn nối giữa chúng)
    """ Thuật toán A* để tìm đường đi ngắn nhất trong đồ thị. """
    open_set = [] #đây là danh sách ưu tiên (sử dụng heapq để đảm bảo luôn chọn điểm có giá trị f(n) nhỏ nhất. Ban đầu chỉ chứa 1 điểm bắt đầu
    heapq.heappush(open_set, (0, start)) #thêm điểm bắt đầu với f = 0 danh sách mở
    came_from = {} #dùng để lưu trữ đường đi ngược lại, giúp tìm ra đường đi sau khi đến được đích
    g_score = {start: 0} #chi phí từ điểm bắt đầu đến 1 nút cụ thể
    f_score = {start: heuristic(start, goal)}  #chi phí dự đoán đi từ một điểm bắt đầu đến đích qua một nút cụ thể. Ban đầu, f_score là điểm bắt đầu là chi phí heuristic giữa nó và đích

    '''Vòng lặp chính'''
    while open_set:
        current = heapq.heappop(open_set)[1]  #Chọn điểm có giá trị f(n) nhỏ nhất từ danh sách mở(open_set). Điểm này được lưu trong biến current

        if current == goal: #Kiểm tra nếu current là đích thì ta tìm được đường đi và cần phải truy vết lại để xây dựng đường đi
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        #Nếu không phải đích, thuật toán sẽ tiếp tục kiểm tra các nút lân cận của nó

        for neighbor, cost in graph.get(current, []):
            tentative_g_score = g_score[current] + cost
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in [i[1] for i in open_set]: #Nếu nút lân cận chưa được xét hoặc chi phí mới nhỏ hơn chi phí trước đó, cập nhật lại thông tin và thêm vào danh sách mở
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return [] #sau khi tìm được đích, thuật toán sẽ truy ngược từ đích về điểm bắt đầu thông qua came_from và trả về đường đi tìm được



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/saved_directions', methods=['GET'])
def saved_directions():
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM directions ORDER BY id ASC')
    directions = cursor.fetchall()

    conn.close()

    return jsonify(directions)

def decode_unicode(s):
    return s.encode().decode('unicode_escape')


@app.route('/delete_directions/<int:id>', methods=['DELETE'])
def delete_directions(id):
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()


    cursor.execute('DELETE FROM directions WHERE id = ?', (id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return jsonify({'message': 'Xóa thành công!'}), 200
    else:
        conn.close()
        return jsonify({'error': 'Không tìm thấy chỉ đường với ID này!'}), 404


# //Invoke-WebRequest -Uri http://localhost:5000/delete_all_directions -Method Delete


@app.route('/delete_all_directions', methods=['DELETE'])
def delete_all_directions():
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM directions')
    conn.commit()

    cursor.execute('DELETE FROM sqlite_sequence WHERE name="directions"')

    conn.close()
    return jsonify({'message': 'Đã xóa tất cả dữ liệu thành công và ID đã được đặt lại!'}), 200


@app.route('/directions', methods=['GET'])
def directions():
    start = request.args.get('start')
    goal = request.args.get('goal')
    travelMode = request.args.get('travelMode').lower()


    # Gọi Google Maps API để lấy dữ liệu chỉ đường
    directions_result = gmaps.directions(start, goal, travelMode, alternatives = True,)
    print(len(directions_result))
    print(directions_result)
    print(travelMode)
    # Bạn cần phải phân tích kết quả từ Google Maps API và chuyển đổi nó thành đồ thị cho A*
    # Ví dụ: graph = parse_directions_to_graph(directions_result)

    # Tính toán đường đi sử dụng A*
    # path = a_star(start_coordinates, goal_coordinates, graph)
    # directions_result = gmaps.directions(start, goal, mode=mode)

    def parse_directions_to_graph(directions_result):
        """ Phân tích kết quả từ Google Maps API và tạo ra một đồ thị. """
        graph = {}

        #tạo đồ thị rỗng, trong đó gồm  : Key(tọa độ của một điểm trên bản đồ) và value (là danh sách các nút lân cận(các điểm có thể đi đến nút hiện tại) và chi phí (khoảng cách)để đi đến điểm đó

        for route in directions_result:
            legs = route.get('legs', [])
            for leg in legs:
                steps = leg.get('steps', [])
                for step in steps:
                    start_location = (step['start_location']['lat'], step['start_location']['lng'])
                    end_location = (step['end_location']['lat'], step['end_location']['lng'])
                    distance = step['distance']['value']  # khoảng cách giữa hai điểm

                    # Thêm vào đồ thị
                    if start_location not in graph:
                        graph[start_location] = []
                    graph[start_location].append((end_location, distance))

                    # Thêm cho đồ thị theo chiều ngược lại (nếu cần thiết)
                    if end_location not in graph:
                        graph[end_location] = []
                    graph[end_location].append((start_location, distance))  # Giả sử có thể đi ngược lại

        return graph

    if directions_result:
        # Phân tích kết quả để tạo đồ thị
        graph = parse_directions_to_graph(directions_result)

        # Lấy tọa độ bắt đầu và kết thúc
        start_coordinates = (directions_result[0]['legs'][0]['start_location']['lat'],
                             directions_result[0]['legs'][0]['start_location']['lng'])
        goal_coordinates = (directions_result[0]['legs'][0]['end_location']['lat'],
                            directions_result[0]['legs'][0]['end_location']['lng'])


        # Tính toán đường đi sử dụng A*
        path = a_star(start_coordinates, goal_coordinates, graph)


        # Trích xuất thông tin khoảng cách
        distance = directions_result[0]['legs'][0]['distance']['text']
        distance_value = directions_result[0]['legs'][0]['distance']['value']

        duration = directions_result[0]['legs'][0]['duration']['text']
        duration_value = directions_result[0]['legs'][0]['duration']['value']
        print(path)
        save_directions_to_db(start, goal, travelMode, distance, duration)
        time_end = time.time()
        print(f"Time taken {time_end - time_start}")
        # Trả về chỉ đường cùng với khoảng cách và lộ trình
        return jsonify({
            'directions': directions_result,
            'distance': distance,
            'distance_value': distance_value,
            'duration': duration,
            'duration_value': duration_value,
            'path': path,  # Lộ trình tính được bằng A*
        })
    else:
        return jsonify({'error': 'Không tìm thấy chỉ đường'}), 404

def save_directions_to_db(start, goal, travel_mode, distance, duration):
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO directions (start, goal, travel_mode, distance, duration)
        VALUES (?, ?, ?, ?, ?)
    ''', (start, goal, travel_mode, distance, duration))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    app.run(debug=True)
