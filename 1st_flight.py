import rospy
from clover import srv
from std_srvs.srv import Trigger
from mavros_msgs.srv import ParamSet

rospy.init_node('flight')

drones = 3
nums = range(1, drones + 1)


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
    param_set[drone]('MC_ROLLRATE_K', k)
    param_set[drone]('MC_PITCHRATE_K', k)

def wait_arrival(drone=0, tolerance=1):
    while not rospy.is_shutdown():
        telem = get_telemetry[drone](frame_id='navigate_target')
        if telem.x ** 2 + telem.y ** 2 + telem.z ** 2 < tolerance**2:
            break
        rospy.sleep(0.2)

crd_list = []

with open('/home/user/drone-games/tasks/cargo/2/gps_spline.pts') as file:
    for line in file:
        line = line.rstrip()
        l = line.split()
        crd_list.append((float(l[0]), float(l[1]), float(l[2])))


navigate[0](x=0, y=0, z=5, speed=1, frame_id='body', auto_arm=True)
rospy.sleep(5)

for crd in crd_list:
    navigate_global[0](lat=crd[0], lon=crd[1], z=crd[2], speed=5, frame_id='body')
    #wait_arrival()
    rospy.sleep(15)

land[0]()
