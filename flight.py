#!/usr/bin/env python3
# coding=utf8
import rospy
from clover import srv
from std_srvs.srv import Trigger
from mavros_msgs.srv import ParamSet
from mavros_msgs.msg import ParamValue
from spline import spline_drone, enu_vector, drop_t, droppoints
from pygeodesy.geoids import GeoidPGM

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

_egm96 = GeoidPGM('/usr/share/GeographicLib/geoids/egm96-5.pgm', kind=-3)


def geoid_height(lat, lon):
    """Calculates AMSL to ellipsoid conversion offset.
    Uses EGM96 data with 5' grid and cubic interpolation.
    The value returned can help you convert from meters 
    above mean sea level (AMSL) to meters above
    the WGS84 ellipsoid.

    If you want to go from AMSL to ellipsoid height, add the value.

    To go from ellipsoid height to AMSL, subtract this value.
    """
    return _egm96.height(lat, lon)


def amsl_to_wgs(lat, lon, alt):
    return alt + geoid_height(lat, lon)
    
def wgs_to_amsl(lat, lon, alt):
    return alt - geoid_height(lat, lon)


def set_rate_k(drone, k):
    param_set[drone](param_id='MC_ROLLRATE_K', value=ParamValue(real=k))
    rospy.sleep(0.2)
    param_set[drone](param_id='MC_PITCHRATE_K', value=ParamValue(real=k))

def wait_arrival(drone=0, tolerance=2, timeout=rospy.Duration(10)):
    start_time = rospy.get_rostime()
    while not rospy.is_shutdown():
        telem = get_telemetry[drone](frame_id='navigate_target')
        if telem.x ** 2 + telem.y ** 2 + (telem.z ** 2 / 4) < tolerance**2:
            break
        if rospy.get_rostime() - start_time > timeout:
            print('wait arrival timeout')
            break
        #print(f"velocity XYZ: {telem.vx} {telem.vy} {telem.vz}")
        rospy.sleep(0.05)
        
# set initial params
for drone in range(drones):
    set_rate_k(drone, 3.0)
    rospy.sleep(0.5)
    set_rate_k(drone, 3.0)
rospy.sleep(1)

# todo: check nans

crd_list = []

with open('/home/user/drone-games/tasks/cargo/3/gps_spline.pts') as file:
    for line in file:
        line = line.rstrip()
        l = line.split()
        crd_list.append((float(l[0]), float(l[1]), float(l[2])))

home_position_0 = get_telemetry[0](frame_id='map')
home_position_1 = get_telemetry[1](frame_id='map')
home_position_2 = get_telemetry[2](frame_id='map')

starts = [get_telemetry[drone]() for drone in range(drones)]

# Координаты первой точки траектории в локальных системах каждого из дронов
#first_point_coords = [
#    enu_vector([home_position_0.lat, home_position_0.lon, home_position_0.alt], crd_list[0]),
#    enu_vector([home_position_1.lat, home_position_1.lon, home_position_1.alt], crd_list[0]),
#    enu_vector([home_position_2.lat, home_position_2.lon, home_position_2.alt], crd_list[0])
#]

# okalachev:
#first_point_coords = [
#    enu_vector([home_position_0.lat, home_position_0.lon, 0], crd_list[0]),
#    enu_vector([home_position_1.lat, home_position_1.lon, 0], crd_list[0]),
#    enu_vector([home_position_2.lat, home_position_2.lon, 0], crd_list[0])
#]

first_point_coords = []
for drone in range(drones):
    # amsl
    #first_point_coords.append(
    #   enu_vector([starts[drone].lat, starts[drone].lon, wgs_to_amsl(starts[drone].lat, starts[drone].lon, starts[drone].alt)],
    #       crd_list[0])
    #)

    # to put cargo alt. on ground
    #first_point_coords.append(
    #   enu_vector([starts[drone].lat, starts[drone].lon, 120-18],
    #       crd_list[0])
    #)

    # rel
    first_point_coords.append(
       enu_vector([starts[drone].lat, starts[drone].lon, 0],
           crd_list[0])
    )
    


print('first point coords', first_point_coords)

navigate[0](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
navigate[1](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
navigate[2](x=0, y=0, z=20, speed=5, frame_id='body', auto_arm=True)
rospy.sleep(10)

cargo_dropped = [False] * drones

resolution = 1000

i = 0
for t, crd in [(a/resolution, (
        spline_drone(a/resolution, 0),
        spline_drone(a/resolution, 1),
        spline_drone(a/resolution, 2)
        )) for a in range(resolution)
    ]:  # При 100 точках расстоние между ними будет около 10 м

    i+=1
    print(f"flying to {crd}")
    #set_position[0](x=crd[0][0]+first_point_coords[0][0]+home_position_0.x, y=crd[0][1]+first_point_coords[0][1]+home_position_0.y, z=crd[0][2]+first_point_coords[0][2]+home_position_0.z, auto_arm=True, frame_id='map')
    #set_position[1](x=crd[1][0]+first_point_coords[1][0]+home_position_1.x, y=crd[1][1]+first_point_coords[1][1]+home_position_1.y, z=crd[1][2]+first_point_coords[1][2]+home_position_1.z, auto_arm=True, frame_id='map')
    #set_position[2](x=crd[2][0]+first_point_coords[2][0]+home_position_2.x, y=crd[2][1]+first_point_coords[2][1]+home_position_2.y, z=crd[2][2]+first_point_coords[2][2]+home_position_2.z, auto_arm=True, frame_id='map')
    
    for drone in range(drones):
        set_position[drone](x=crd[drone][0]+first_point_coords[drone][0]+starts[drone].x, y=crd[drone][1]+first_point_coords[drone][1]+starts[drone].y, z=crd[drone][2]+first_point_coords[drone][2]+starts[drone].z, auto_arm=True, frame_id='map')
    
    wait_arrival(tolerance=5)
    
    for drone in range(drones):
       if t >= drop_t[drone] - 1/resolution and not cargo_dropped[drone]:
           print('fly to drop point')
           z = get_telemetry[drone]().z
           navigate_global[drone](lat=droppoints[drone][0], lon=droppoints[drone][1], z=z, speed=1)
           wait_arrival(drone, tolerance=1)
           rospy.sleep(2)
           
           print('drop cargo %s' % (drone + 1))
           cargo_dropped[drone] = True
           client.call_async('dropCargo', 'iris%s' % (drone + 1)).join()
           set_rate_k(drone, 0.3)
    
    # Тут надо будет сравнивать текущее t с t сброса груза
    # Найти t сброса груза можно найдя в gps_spline.pts точку с lat, lon
    # соответствующими точке сброса, и взяв ее t (той же строки) из spline_t.txt

    # if i == 7:
    #     client.call_async('dropCargo', vehicle_name).join()
    #     set_rate_k(0, 0.3)


# navigate_global[0](lat=crd_list[0][0], lon=crd_list[0][1], z=10, speed=SPEED, frame_id='map')
# wait_arrival()

for drone in range(drones):
    print('wait arrival ', drone)
    wait_arrival(drone, tolerance=2)
    
for drone in range(drones):
    print('land drone ', drone)
    land[drone]()
