import rospy
from clover import srv
from std_srvs.srv import Trigger

rospy.init_node('flight')

drones = 3


get_telemetry = map(range(drones), lambda i: rospy.ServiceProxy('get_telemetry' + str(i), srv.GetTelemetry))
navigate = map(range(drones), lambda i: rospy.ServiceProxy('navigate' + str(i), srv.Navigate))
navigate_global = map(range(drones), lambda i: rospy.ServiceProxy('navigate_global' + str(i), srv.NavigateGlobal))
set_position = map(range(drones), lambda i: rospy.ServiceProxy('set_position' + str(i), srv.SetPosition))
set_velocity = map(range(drones), lambda i: rospy.ServiceProxy('set_velocity' + str(i), srv.SetVelocity))
set_attitude = map(range(drones), lambda i: rospy.ServiceProxy('set_attitude' + str(i), srv.SetAttitude))
set_rates = map(range(drones), lambda i: rospy.ServiceProxy('set_rates' + str(i), srv.SetRates))
land = map(range(drones), lambda i: rospy.ServiceProxy('land' + str(i), srv.Trigger))


navigate[0](x=0, y=0, z=5, frame_id='body', auto_arm=True)
