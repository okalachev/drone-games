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
land = list(map(lambda i: rospy.ServiceProxy('land' + str(i), srv.Trigger), nums))

param_set = list(map(lambda i: rospy.ServiceProxy('mavros' + str(i) + '/param/set', ParamSet), nums))


def set_rate_k(drone, k):
    param_set[drone]('MC_ROLLRATE_K', k)
    param_set[drone]('MC_PITCHRATE_K', k)


navigate[1](x=0, y=0, z=5, frame_id='body', auto_arm=True)
