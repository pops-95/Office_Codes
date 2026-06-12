import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/media/soumik/18D07164D07148D0/CODE/GIT/Office_Codes/Ros2/samdhan_ng_processing/install/chlorophyll_node'
