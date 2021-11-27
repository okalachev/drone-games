import rospy
from clover import srv
from std_srvs.srv import Trigger
from mavros_msgs.srv import ParamSet

rospy.init_node('flight')

drones = 3
nums = range(1, drones + 1)


get_telemetry = map(lambda i: rospy.ServiceProxy('get_telemetry' + str(i), srv.GetTelemetry), nums)
navigate = map(lambda i: rospy.ServiceProxy('navigate' + str(i), srv.Navigate), nums)
navigate_global = map(lambda i: rospy.ServiceProxy('navigate_global' + str(i), srv.NavigateGlobal), nums)
set_position = map(lambda i: rospy.ServiceProxy('set_position' + str(i), srv.SetPosition), nums)
set_velocity = map(lambda i: rospy.ServiceProxy('set_velocity' + str(i), srv.SetVelocity), nums)
set_attitude = map(lambda i: rospy.ServiceProxy('set_attitude' + str(i), srv.SetAttitude), nums)
set_rates = map(lambda i: rospy.ServiceProxy('set_rates' + str(i), srv.SetRates), nums)
land = map(lambda i: rospy.ServiceProxy('land' + str(i), srv.Trigger), nums)

param_set = map(lambda i: rospy.ServiceProxy('mavros' + str(i) + '/param/set', ParamSet), nums)


def set_rate_k(drone, k):
    param_set[drone]('MC_ROLLRATE_K', k)
    param_set[drone]('MC_PITCHRATE_K', k)

def wait_arrival(tolerance=1):
    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        if telem.x ** 2 + telem.y ** 2 + telem.z ** 2 < tolerance**2:
            break
        rospy.sleep(0.2)

def get_points(file):

    lst = file.split("\n")
    pts = []
    for line in lst:
        line = line.split()
        pts.append((float(line[0]), float(line[1]), float(line[2])))
    return pts



crd_list = get_points(open('~/drone-games/tasks/cargo/2/gps_spline.pts', "r"))

navigate[1](x=0, y=0, z=5, speed=1, frame_id='body', auto_arm=True)
rospy.sleep(5)

for crd in crd_list:
    navigate_global[1](lat=crd[0], lon=crd[1], z=crd[2], speed=5, frame_id='body')
    wait_arrival()

land[1]()
