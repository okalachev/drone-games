import math
from scipy.interpolate import interp1d


D_VALUE = 2  # Параметр D из задания - расстояние от дрона до центра масс группы
DRONE_COUNT = 3

#!!!
# в Mavros при выдаче в топик global_position/global высота задана в элипсоиде WGS-84 и не равна высоте над уровнем моря (AMSL)
# см. https://wiki.ros.org/mavros#mavros.2FPlugins.Avoiding_Pitfalls_Related_to_Ellipsoid_Height_and_Height_Above_Mean_Sea_Level
#!!!
# преобразование дельты gps в дельту xyz по простейшей формуле (из интернета)
def enu_vector(g1, g2):
    n = g2[0] - g1[0]
    e = g2[1] - g1[1]
    u = g2[2] - g1[2]
    refLat = (g1[0] + g2[0]) / 2
    nm = n * 333400 / 3  # deltaNorth * 40008000 / 360
    em = e * 1001879 * math.cos(
        math.radians(refLat)) / 9  # deltaEast * 40075160 *cos(refLatitude) / 360
    return [em, nm, u]


with open('/home/user/drone-games/tasks/cargo/3/gps_spline.pts') as file:
    gps_coords = [[float(a) for a in line.rstrip().split()] for line in file]

with open('/home/user/drone-games/tasks/cargo/3/spline_t.txt') as file:
    gps_coords_t = [float(line.rstrip()) for line in file if line.rstrip()]

local_coords = [enu_vector(gps_coords[0], g2) for g2 in gps_coords]


drop_t = []

with open('/home/user/drone-games/tasks/cargo/3/gps_droppoint.pts') as file:
    droppoints = [[float(a) for a in line.rstrip().split()] for line in file]
    for droppoint in droppoints:
       for i, coords in enumerate(gps_coords):
           if coords[0] == droppoint[0] and coords[1] == droppoint[1]:
           	drop_t.append(gps_coords_t[i])
           	break


print('drop_t', drop_t)


splines_xyz = (interp1d(gps_coords_t, [xyz[0] for xyz in local_coords], kind='cubic'),
               interp1d(gps_coords_t, [xyz[1] for xyz in local_coords], kind='cubic'),
               interp1d(gps_coords_t, [xyz[2] for xyz in local_coords], kind='cubic'))


# Изначальный сплайн (по точкам из условия)
def spline(t):
    return (float(splines_xyz[0](t)), float(splines_xyz[1](t)), float(splines_xyz[2](t)))


# Возвращает точку траектории на момент времени t (t лежит от 0 до 1 для всего полета,
# от начальной точки до конечной) для дрона drone_num. Дроны расположены треугольником
# вокруг точки изначального (построенного по точкам из условия задачи) сплайна, каждый
# на расстоянии D_VALUE от этой точки. Траектория в локальной системе относительно
# своей первой точки!
def spline_drone(t, drone_num):
    return (
        float(splines_xyz[0](t) + D_VALUE * math.cos(2 * math.pi / DRONE_COUNT * drone_num)), 
        float(splines_xyz[1](t) + D_VALUE * math.sin(2 * math.pi / DRONE_COUNT * drone_num)), 
        float(splines_xyz[2](t))
    )
