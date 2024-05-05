import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import os
import re
import json

path='./nasa_data'
files = os.listdir(path)
ic_nasa = dict()
for i in files:
    with open('/'.join([path,i]),'r') as f:
        text = f.read()
        name = re.search('([a-zA-Z]+)',text.split("\n")[1][29:],re.M)[1]
        print(name)
        raw = re.search(r'2460323.500000000 = A.D. 2024-Jan-14 00:00:00.0000 TDB \n\s*X =.*\n.*\n',text)[0]
        raw_split = raw.split("\n")
        r_text = raw_split[1]
        v_text = raw_split[2]
        x = float(re.search(r'X\s*=\s*([\-.+eE0-9]*)',r_text)[1])
        y = float(re.search(r'Y\s*=\s*([\-.+eE0-9]*)',r_text)[1])
        z = float(re.search(r'Z\s*=\s*([\-.+eE0-9]*)',r_text)[1])
        vx = float(re.search(r'VX\s*=\s*([\-.+eE0-9]*)',v_text)[1])
        vy = float(re.search(r'VY\s*=\s*([\-.+eE0-9]*)',v_text)[1])
        vz = float(re.search(r'VZ\s*=\s*([\-.+eE0-9]*)',v_text)[1])
        mass_text = re.search(r'^.*Mass[,]?.*10.*=\s*[~0-9].*$',text,re.M)[0]
        mass_extract1 = re.search(r'Mass[^=]*=\s*[^\s]*\s*',mass_text)[0]

        num_val = float(re.search(r'= ~?([^+]*)',mass_extract1.strip())[1].strip())
        unit_str = re.search(r'([k]?g)',mass_extract1)[1]
        exponent_val = float(re.findall(r'10\^[0-9]{2}',mass_extract1)[0].replace("^",'e'))/10
        #10^22 = 10e22 / 10 = 1e22
        if unit_str == 'g':
            multiplier = 1e-3
        else:
            multiplier = 1
        m = num_val*exponent_val*multiplier
        ic_nasa[name]=[x,y,z,vx,vy,vz,m]
        
ic_nasa_adjust_unit = dict()
for key, value in ic_nasa.items():
    ic_nasa_adjust_unit[key] = [i*1000 for i in value[:-1]]+[value[-1]]
    
ic = []
names = ['Sun','Mercury','Venus','Earth','Moon','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto']
for i in names:
    ic.append(ic_nasa_adjust_unit[i])
ic = np.array(ic)
ic_relative_to_sun = np.hstack([ic[:,:-1]-ic[0,:-1],ic[:,-1].reshape(-1,1)])

data_to_json = []
for name in names:
    mat = ic_nasa_adjust_unit[name]
    data_to_json.append([name,mat[6],*mat[0:6]])

data_to_json_relative_to_sun = []
for name in names:
    mat = ic_nasa_adjust_unit[name]
    data_to_json_relative_to_sun.append([name,mat[6],*(np.array(mat[0:6])-np.array(ic_nasa_adjust_unit['Sun'][0:6]))])

cmap = plt.colormaps.get_cmap('jet')
colors = cmap(np.linspace(0,1,len(names)))
colors_hex = [matplotlib.colors.rgb2hex(colors[i]) for i in range(len(names))]
for out_name, selected_data in zip(['solar_system.json','solar_system_relative_to_sun.json'],
                                   [data_to_json,data_to_json_relative_to_sun]):
    
    json_data = {
        "obj_data":selected_data,
        "object_color_list":colors_hex,
        "sim_control_dict,current_time_day_var": "0.0",
        "sim_control_dict,current_time_ts_var": "2024-01-14T00:00:00.000000000", 
        "sim_control_dict,time_step_entry_s_var": "86400.0", 
        "sim_control_dict,time_step_entry_d_var": "1.0", 
        "sim_control_dict,rotation_x_entry_var": "45.0", 
        "sim_control_dict,rotation_y_entry_var": "-45.0", 
        "sim_control_dict,rotation_z_entry_var": "-90.0"
    }
    with open(out_name,'w') as f:
        json.dump(json_data, f)
