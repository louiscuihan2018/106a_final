cmake_minimum_required(VERSION 2.8.3)
project(locobot_interface)







find_package(catkin REQUIRED COMPONENTS
    roscpp
    rospy
    std_msgs
    message_generation
    sensor_msgs
)








catkin_python_setup()

































add_service_files(
  FILES
  ArmEECommand.srv
  ArmJointCommand.srv
  BasePositionCommand.srv
  BaseVelocityCommand.srv
  GetPointcloud.srv
  GetImage.srv
  GripperCommand.srv
  SetPanTilt.srv
  GetGraspObstructed.srv
  GetFK.srv
  GetIK.srv
)









generate_messages(
  DEPENDENCIES
  std_msgs  
  sensor_msgs
)






























catkin_package(




)







include_directories(


)





















































































