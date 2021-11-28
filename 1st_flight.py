#!/usr/bin/env python3
# coding=utf8
import rospy
from clover import srv
from std_srvs.srv import Trigger
from mavros_msgs.srv import ParamSet
from mavros_msgs.msg import ParamValue
from spline import spline_drone, enu_vector

rospy.init_node('flight')

import airsim

cl = airsim.MultirotorClient()
cl.confirmConnection()
cl.enableApiControl(True)
client = cl.client

vehicle_name = "iris1"



drones = 3
nums = range(1, drones + 1)
SPEED = 15

get_telemetry = list(map(lambda i: rospy.ServiceProxy('get_telemetry' + str(i), srv.GetTelemetry), nums))
navigate = list(map(lambda i: rospy.ServiceProxy('navigate' + str(i), srv.Navigate), nums))
navigate_global = list(map(lambda i: rospy.ServiceProxy('navigate_global' + str(i), srv.NavigateGlobal), nums))
set_position = list(map(lambda i: rospy.ServiceProxy('set_position' + str(i), srv.SetPosition), nums))
set_velocity = list(map(lambda i: rospy.ServiceProxy('set_velocity' + str(i), srv.SetVelocity), nums))
set_attitude = list(map(lambda i: rospy.ServiceProxy('set_attitude' + str(i), srv.SetAttitude), nums))
set_rates = list(map(lambda i: rospy.ServiceProxy('set_rates' + str(i), srv.SetRates), nums))
land = list(map(lambda i: rospy.ServiceProxy('land' + str(i), Trigger), nums))

param_set = list(map(lambda i: rospy.ServiceProxy('mavros' + str(i) + '/param/set', ParamSet), nums))


def set_rate_k(drone, k):
    param_set[drone](param_id='MC_ROLLRATE_K', value=ParamValue(real=k))
    param_set[drone](param_id='MC_PITCHRATE_K', value=ParamValue(real=k))

def wait_arrival(drone=0, tolerance=2):
    while not rospy.is_shutdown():
        telem = get_telemetry[drone](frame_id='navigate_target')
        if telem.x ** 2 + telem.y ** 2 + telem.z ** 2 < tolerance**2:
            break
        #print(f"velocity XYZ: {telem.vx} {telem.vy} {telem.vz}")
        rospy.sleep(0.2)

crd_list = []

with open('/home/user/drone-games/tasks/cargo/2/gps_spline.pts') as file:
    for line in file:
        line = line.rstrip()
        l = line.split()
        crd_list.append((float(l[0]), float(l[1]), float(l[2])))

home_position_0 = get_telemetry[0](frame_id='map')
home_position_1 = get_telemetry[1](frame_id='map')
home_position_2 = get_telemetry[2](frame_id='map')

# Координаты первой точки траектории в локальных системах каждого из дронов
first_point_coords = [
    enu_vector([home_position_0.lat, home_position_0.lon, home_position_0.alt], crd_list[0]),
    enu_vector([home_position_1.lat, home_position_1.lon, home_position_1.alt], crd_list[0]),
    enu_vector([home_position_2.lat, home_position_2.lon, home_position_2.alt], crd_list[0])
]

navigate[0](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
navigate[1](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
navigate[2](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
rospy.sleep(10)

i = 0
for t, crd in [(a/100.0, (
        spline_drone(a/100.0, 0),
        spline_drone(a/100.0, 1),
        spline_drone(a/100.0, 2)
        )) for a in range(100)
    ]:  # При 100 точках расстоние между ними будет около 10 м

    i+=1
    print(f"flying to {crd}")
    set_position[0](x=crd[0][0]+first_point_coords[0][0], y=crd[0][1]+first_point_coords[0][1], z=crd[0][2]+first_point_coords[0][2], auto_arm=True, frame_id='map')
    set_position[1](x=crd[1][0]+first_point_coords[1][0], y=crd[1][1]+first_point_coords[1][1], z=crd[1][2]+first_point_coords[1][2], auto_arm=True, frame_id='map')
    set_position[2](x=crd[2][0]+first_point_coords[2][0], y=crd[2][1]+first_point_coords[2][1], z=crd[2][2]+first_point_coords[2][2], auto_arm=True, frame_id='map')
    wait_arrival()
    # Тут надо будет сравнивать текущее t с t сброса груза
    # Найти t сброса груза можно найдя в gps_spline.pts точку с lat, lon
    # соответствующими точке сброса, и взяв ее t (той же строки) из spline_t.txt

    # if i == 7:
    #     client.call_async('dropCargo', vehicle_name).join()
    #     set_rate_k(0, 0.3)


# navigate_global[0](lat=crd_list[0][0], lon=crd_list[0][1], z=10, speed=SPEED, frame_id='map')
# wait_arrival()

land[0]()
