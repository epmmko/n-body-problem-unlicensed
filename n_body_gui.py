#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#"""
#Completed on Sun May 5 10:57:00 2024
#
#@author: Ekarit Panacharoensawad
#"""
import tkinter as tk
from tkinter import filedialog
import threading
from collections import deque
import tkinter.ttk as ttk
from ast import literal_eval #for updating the listbox
from scipy.spatial.transform import Rotation as RTT
import numpy as np
import copy
from n_body_kernel import N_body
import pandas as pd # pd.to_datetime
import json

class MainView:
    def __init__(self):
        np.random.seed(42)
        self.save_load_attributes = ['obj_data','object_color_list',
                                     'sim_control_dict,current_time_day_var',
                                     'sim_control_dict,current_time_ts_var',
                                     'sim_control_dict,time_step_entry_s_var',
                                     'sim_control_dict,time_step_entry_d_var',
                                     'sim_control_dict,rotation_x_entry_var',
                                     'sim_control_dict,rotation_y_entry_var',
                                     'sim_control_dict,rotation_z_entry_var']
        self.items_to_be_disabled_upon_start = ['Start','Next','Previous',
                'current_time_ts_entry', 'rotation_x_entry', 
                'rotation_y_entry',
                'rotation_z_entry', 'Barycenter Tracking', 
                'Stationary Initial Barycenter',
                'Selected-object tracking','Cartesian coordinates']
        self.menu_items_to_be_disabled_upon_start = [
            "Add object","Delete object"]
        self.last_readable_x_angle = 0
        self.last_readable_y_angle = 0
        self.last_readable_z_angle = 0
        self.bary_to_reference_point = np.array([0,0,0])
        self.windows_dict=dict()
        self.nbody = N_body()
        self.SCREEN_MULTIPLIER = 10
        self.root = tk.Tk()
        self.object_name_list = tk.StringVar(value=['Sun','Earth','Moon'])
        #random color list of 3
        self.object_color_list = [
            "#" + "".join(["{:02x}".format(int(i)) 
                           for i in np.random.rand(3)*255]) for j in range(3)]
        self.object_property_list = ['Object id','Name', 'mass (kg)', 'x (m)',
                                     'y (m)', 'z (m)', 'vx (m/s)', 'vy (m/s)', 
                                     'vz (m/s)']
        self.prop_name_to_tk_name = dict()
        self.tk_name_to_prop_name = dict()
        self.prop_to_entry_name = dict()
            #{'Object id': '!entry', 'Name': '!entry2', 
            #'mass (kg)': '!entry3', 'x (m)': '!entry4', 
            #'y (m)': '!entry5', 'z (m)': '!entry6', 'vx (m/s)': '!entry7', '
            #vy (m/s)': '!entry8', 'vz (m/s)': '!entry9'}
        self.entry_to_prop_name = dict()
        self.last_listbox_selection = 0
        self.obj_data = [['Sun', 1.98847e30, 0,0,0,0,0,0],
                         ['Earth', 5.97219000e+24, -5.73998389e+10,  
                          1.35483548e+11, -6.88414616e+06, -2.79205524e+04, 
                          -1.17429731e+04,  1.16079410e-01],
                         ['Moon', 7.34767309e22, -5.70948268e+10,  
                          1.35289254e+11, -3.18429298e+07, -2.73272114e+04, 
                          -1.08367046e+04,  5.77124775e+01]]
        self.root.title("N-Body Simulation")
        self.pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.pane.add(self.make_canvas(self.pane), weight=1)
        self.pane.add(self.make_property_view(self.pane), weight=1)
        self.pane.grid(column=0,row=0,sticky='news')
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.render_list = []
        self.create_listbox_context_menu(self.listbox)
        self.create_context_menu(self.canvas)
        self.create_main_menu(self.root)
        self.binding()
        self.style = ttk.Style()
        self.style.configure('.', font=(None,16))
        self.style.configure('Treeview',rowheight=42)
        self.style.configure('Treeview.Heading', font=(None,16))
        
        #set initial condition
        self.listbox.selection_set(0)
        self.show_object_properties(None)
        self.sim_control_clear()
    def binding(self):
        self.canvas.bind("<Button-1>",self.create_circle)
        self.canvas.bind("<Button-3>", 
            lambda e:self.context_menu.post(e.x_root, e.y_root))
        self.listbox.bind("<<ListboxSelect>>",self.show_object_properties)
        self.listbox.bind("<Button-3>", 
            lambda e: self.prop_context_menu.post(e.x_root, e.y_root))
        self.sim_control_dict['time_step_entry_s'].bind(
            "<Motion>",self.move_on_time_step_entry_s)
        self.sim_control_dict['time_step_entry_d'].bind(
            "<Motion>",self.move_on_time_step_entry_d)
        self.sim_control_dict['time_step_entry_s_var'].trace_add(
            'write',self.trace_callback_edit_s_timestep)
        self.sim_control_dict['time_step_entry_d_var'].trace_add(
            'write',self.trace_callback_edit_d_timestep)
    def create_main_menu(self, root):
        root.option_add('*tearOff', tk.FALSE)
        self.main_menu = tk.Menu(root)
        root['menu'] = self.main_menu
        self.menu_file = tk.Menu(self.main_menu)
        self.main_menu.add_cascade(menu=self.menu_file, label='File')
        self.menu_file.add_command(label='Open', command=self.open_file)
        self.menu_file.add_command(label='Save as', command = self.save_as)
        self.menu_help = tk.Menu(self.main_menu)
        self.main_menu.add_cascade(menu=self.menu_help, label='Help')
        self.menu_help.add_command(label='About N-Body Simulation', 
                                   command=self.menu_help_about)
    def open_file(self):
        file_name = filedialog.askopenfilename(
            filetypes=(('json file','*.json'),))
        with open(file_name, 'r') as f:
            loaded_data = json.load(f)
        for key, value in loaded_data.items():
            if key.find(',') == -1:
                setattr(self, key, value)
            else:
                getattr(self, key.split(',')[0])[key.split(',')[1]].set(value)
        #add obj onto the listbox
        self.object_name_list.set([i[0] for i in self.obj_data])
        for i,color in enumerate(self.object_color_list):
            self.listbox.itemconfig(i,{'fg':color})
        self.listbox.selection_clear(0,'end')
        self.listbox.selection_set('end')
        self.listbox.see('end')
        self.listbox.event_generate("<<ListboxSelect>>")
        self.sim_control_clear()
    def save_as(self):
        file_name = filedialog.asksaveasfilename(
            filetypes=(('json file','*.json'),))
        data_to_be_saved = dict()
        for att in self.save_load_attributes:
            if att.find(',') == -1:
                val = getattr(self,att)
            else:
                val = getattr(self,att.split(',')[0])[att.split(',')[1]].get()
            data_to_be_saved[att]=val
        with open(file_name, 'w') as f:
            json.dump(data_to_be_saved, f)
        print(file_name)
    def menu_help_about(self):
        about_text = (
"""Author: Ekarit Panacharoensawad
License: The Unlicensed (https://unlicense.org)
Version: 1.0.2024.05.05
Released date: May 5, 2024
Permanent download link: https://github.com/epmmko/n-body-problem-unlicensed
Description: This software provides the calculation of position and velocity 
    for two or more objects based on Newton's second law of motion 
    (n-body problem). The calculation is adjusting automatically
    as the number of objects is changed. More objects lead to slow calculation.
Limitation: This calculation does not account for any collision.
    The objects' velocity should be a lot less than the speed of light.
    If two objects are at the exact same position, the gravitational force 
    between object becomes infinity, and the answer to the equation of motion 
    at the next time step cannot be calculated.
Comparison with existing software: Even though this code was written by myself, 
    this n-body problem is a classic physics problem that already has multiple
    solution out there on the internet. Some of them even consider collision 
    (https://www.aanda.org/articles/aa/full_html/
     2012/01/aa18085-11/aa18085-11.html, 
     https://github.com/hannorein/rebound/, GPL-3.0 license).
    Some of them uses GPU and can run galaxy level simulation 
    (https://github.com/Hsin-Hung/N-body-simulation, Apache-2.0 license). 
    This software does not use GPU, cannot handle galaxy level simulation. 
    In fact, if we have about 5+ objects, the simulation will get quite slow.
    It does not have the correction to the numerical error as it run as other 
    approaches may have 
    (e.g. https://engineering.purdue.edu/people/kathleen.howell.1/
     Publications/Journals/2006_JSR_MarHowWil.pdf). 
    We will see that if we use symmetric initial condition, eventually the 
    objects' trajectories become asymmetric. Nevertheless, this software uses
    "The Unlicense" which means no conditions apply. The unlicensed works can 
    be distributed without source code and under different terms.
Possible usage: It can serve as
    *An easy example on how to solve the second law of motion.
    *An example on how to connect numerical result with GUI
    *An example on using the second thread to not freeze GUI while running
        * The zoom-in/out option is working while running the program
    *Teaching material for physics law implementation
        *For students in numerical method class (sophomore or junior year 
            for physics/math/computer science students
        *For students in math and science class 
            (K-12, depending on the depth that you want to do)
    *For me, the main audience is my daughters. It is for them to to see how 
    objects move.
        I do not really go into the coding or calculation parts. 
        I also use this code as a cheat sheet for Tk library.
    *...and of course, it can be used for fun. 
        It’s kinda cool to see how things move!
For the serious usage: This program can serve as an example on
        1) how to solve n-body problem with the number of object to be defined 
            at the run-time
        2) how to render it on the screen with the use of free libraries
    The default setting is based on the solar system coordinate from Nasa 
        on the time of 2460323.500000000 = A.D. 2024-Jan-14 00:00:00.0000 TDB 
        (Barycentric Dynamical Tim). This means it can be used to calculate 
        the realistic location of planets relative to the sun if the correct
        information is provided. The numerical method used is 
        Dormand & Prince (4)5 order with the relative tolerance of 1e-8. 
        This should allow somewhat accurate calculation of the real system.
Comments:
    *Coding part
        *Each window should be created as a separate canvas.
        *There should be a function to add a circle or an "x" mark on the 
            the screen (not to combine them together)
        *The mouse wheel for scrolling the scroll bar of the about text is 
            restricted to X11 machine.
            Platform independent GUI should be considered'
        *Add tooltip for all widgets.
    *Functionality
        *It would be nice to see the recent object path. 
            This may be added as a line behind the object
        *The object with higher mass should be larger
        *The circle edge of the object should change color depending on 
            the object's speed.
        *The ability to move the object in canvas then update the xyz 
            coordinate should be added
        *The ability to adjust the object velocity by double-clicking 
            the object and assign the velocity is nice to have
    *Major modification
        *Use javascript and make similar GUI/calculation, 
            then serves it on a website.
        *Make it more kids-friendly such that kindergarten students can use
            (may need to do the tablet version)
Acknowledgment: The author would like to thank physicists, mathematicians, 
    engineers, computer scientists, programmers, the open-source movement, 
    his teachers, and all related persons for the development of the equation
    of motion, the development of the numerical method for solving the 
    equation of motions, the development of hardware, software, the internet
    including but not limiting to the libraries used in this source code, 
    the programming language itself, the Linux OS that the author is using 
    for free, and free-websites that the author used for equation of motion 
    theory (wikipedia.org), developing the GUI (tkdocs), debugging the program
    (stackoverflow.com), and distribute this work (github.com). The author is 
    merely the person who used the existing laws of physics, mathematical and 
    computational knowledge together with the existing python libraries to do 
    the relevant calculations and generating the results. Last but not least, 
    he would like to thank his friend and family for continuous support during
    his entire life.
Request: If you find that this program, source code, or the trick to solve the
    second law of motion for any number of objects programmatically is useful, 
    please try to find a way to contribute (maybe, donating some money to 
    Unicef). Thank you for your consideration.
""")
        about_window_exists = False
        if 'about' in self.windows_dict:
            try:
                self.windows_dict['about'].lift()
                self.windows_dict['about'].focus_force()
                self.windows_dict['about'].grab_set()
                self.windows_dict['about'].grab_release()
                about_window_exists = True
            except Exception:
                pass
        if not about_window_exists:
            self.windows_dict['about'] = tk.Toplevel()
            top = self.windows_dict['about']
            top.geometry("1200x600")
            top.title("About")
            self.windows_dict['about_widgets'] = dict()
            widgets = self.windows_dict['about_widgets']
            widgets['frame'] = ttk.Frame(top,padding=(5,5))
            widgets['scrollable_canvas'] = tk.Canvas(widgets['frame'])
            widgets['yscroll'] = ttk.Scrollbar(widgets['frame'], 
                orient=tk.VERTICAL, command=widgets['scrollable_canvas'].yview)
            widgets['xscroll'] = ttk.Scrollbar(widgets['frame'], 
                orient=tk.HORIZONTAL, 
                command=widgets['scrollable_canvas'].xview)
            widgets['scrollable_canvas'].configure(yscrollcommand=
                widgets['yscroll'].set, xscrollcommand=widgets['xscroll'].set)
            widgets['scrollable_canvas'].bind('<Configure>', 
                lambda e: widgets['scrollable_canvas'].configure(
                scrollregion=widgets['scrollable_canvas'].bbox("all")))
            widgets['inner_frame'] = ttk.Frame(widgets['scrollable_canvas'])
            widgets['label'] = ttk.Label(widgets['inner_frame'],
                                         text=about_text)
            widgets['frame'].grid(column=0,row=0,sticky='nsew')
            widgets['inner_frame'].grid(column=0,row=0,sticky='nsew')
            widgets['label'].grid(column=0,row=0,sticky='nsew')
            top.rowconfigure(0, weight=1)
            top.columnconfigure(0, weight=1)
            widgets['frame'].rowconfigure(0, weight=1)
            widgets['frame'].columnconfigure(0, weight=1)
            widgets['scrollable_canvas'].grid(column=0,row=0,sticky='nsew')
            widgets['yscroll'].grid(column=1,row=0,sticky='nsew')
            widgets['xscroll'].grid(column=0,row=1,sticky='nsew')
            widgets['scrollable_canvas'].create_window((0,0), 
                window=widgets['inner_frame'],anchor='nw')
            widgets['label'].bind("<Button-4>", 
                self._on_about_window_mousewheel_up) #specific to X11
            widgets['label'].bind("<Button-5>", 
                self._on_about_window_mousewheel_down) #specific to X11
            widgets['label'].bind("<Shift-Button-4>", 
                self._on_about_window_mousewheel_left) #specific to X11
            widgets['label'].bind("<Shift-Button-5>", 
                self._on_about_window_mousewheel_right) #specific to X11            
    def _on_about_window_mousewheel_up(self, event):
        self.windows_dict['about_widgets']['scrollable_canvas'].yview_scroll(
            -1, "units")
    def _on_about_window_mousewheel_down(self, event):
        self.windows_dict['about_widgets']['scrollable_canvas'].yview_scroll(
            1, "units")
    def _on_about_window_mousewheel_right(self, event):
        self.windows_dict['about_widgets']['scrollable_canvas'].xview_scroll(
            1, "units")
    def _on_about_window_mousewheel_left(self, event):
        self.windows_dict['about_widgets']['scrollable_canvas'].xview_scroll(
            -1, "units")

    def create_context_menu(self, root):
        root.option_add('*tearOff', tk.FALSE)
        self.context_menu = tk.Menu(root)
        self.context_menu.add_command(command=self.zoom_in, label="Zoom-in")
        self.context_menu.add_command(command=self.zoom_out, label="Zoom-out")
    def create_listbox_context_menu(self, root):
        root.option_add('*tearOff', tk.FALSE)
        self.prop_context_menu = tk.Menu(root)
        self.prop_context_menu.add_command(command=self.add_object,
                                           label="Add object")
        self.prop_context_menu.add_command(command=self.delete_object,
                                           label="Delete object")
    def zoom_in(self):
        self.SCREEN_MULTIPLIER = self.SCREEN_MULTIPLIER * 0.5
        self.sim_control_clear()
    def zoom_out(self):
        self.SCREEN_MULTIPLIER = self.SCREEN_MULTIPLIER * 2
        self.sim_control_clear()
    def add_object(self):
        current_list = list(literal_eval(self.object_name_list.get()))
        len_current_list = len(current_list)
        default_name = 'object '+str(len_current_list+1)
        #item list before adding
        self.listbox.insert('end', default_name)
        self.obj_data.append(
            [default_name, 1.0e24, 1e5, 0, 0, 1e4, 0.5e5, 500.0])
        self.object_color_list.append("#" + "".join(["{:02x}".format(int(i))
            for i in np.random.rand(3)*255]))
        self.update_barycenter()
        self.listbox.selection_clear(0,'end')
        self.listbox.selection_set('end')
        
        self.listbox.itemconfig(len_current_list,
            {'fg':self.object_color_list[len_current_list]})
        
        self.listbox.see('end')
        self.sim_control_clear()
        self.listbox.event_generate("<<ListboxSelect>>")
    def delete_object(self):
        try:
            selection_id = self.listbox.curselection()[0]
            print("selection_id = ",selection_id)
            len_current_list = len(self.obj_data)
            self.obj_data.pop(selection_id)
            self.object_color_list.pop(selection_id)
            self.update_barycenter()
            new_listbox_value_prep = list(literal_eval(
                self.object_name_list.get()))
            new_listbox_value_prep.pop(selection_id)
            self.object_name_list.set(new_listbox_value_prep)
            if selection_id == len_current_list - 1:
                self.listbox.selection_clear(0,'end')
                self.listbox.selection_set('end')
                self.listbox.see('end')
            #update color
            for i,color in enumerate(self.object_color_list):
                self.listbox.itemconfig(i,{'fg':color})
            self.listbox.event_generate("<<ListboxSelect>>")
            self.sim_control_clear()
        except Exception as e:
            print(e)
    def make_pallette(self, root):
        self.pallette_label = ttk.Label(root,text="pallette")
        self.pallette_label.grid(column=0,row=0,sticky='nsew')
        return self.pallette_label
    def make_canvas(self, root):
        w = 1200
        h = 900
        self.canvas_w = w
        self.canvas_h = h
        #section width, height
        self.sw = w/2
        self.sh = h/2
        #    z    y
        #    |  /
        #    |/____x
                
        #+y top | x'-y'
        #   0   |   1
        #     +x|
        #----------------
        #+zfront|+z side
        #   2   |   3
        #     +x|     +y
        
        self.cv_tl = [(0, 0),(w/2,0),(0,h/2),(w/2,h/2)] 
            #top left point for each section
        cv_tl = self.cv_tl
        self.cv_c = [(w/4,h/4),(0.75*w,h/4),(w/4,0.75*h),(0.75*w,0.75*h)]  
            #center point for each section
        self.canvas = canvas = tk.Canvas(
            root, width = self.canvas_w , height = self.canvas_h,bg='#ddd')
        self.canvas.create_line(0, self.canvas_h/2, self.canvas_w, 
            self.canvas_h/2, fill="#000000", width=1) #horizontal
        self.canvas.create_line(self.canvas_w/2,0,self.canvas_w/2, 
            self.canvas_h, fill="#000000", width=1) #vertical
        init_texts = (("Top View: x-y", "+x", "+y"),
                      ("Rotated View","+x","+y"),
                      ("Front View: x-z", "+x", "+z"),
                      ("Side View: y-z", "+y","+z"))
        axis_color = {"+x":"#AA0000","+y":"#00AA00", "+z":"#0000AA"}
        for check in enumerate(zip(cv_tl,init_texts)):
            print(check)
        
        self.dxyz_3d_x_axis0 = [40,0,0]
        self.dxyz_3d_y_axis0 = [0,-40,0]
        self.dxyz_3d_z_axis0 = [0,0,40]
        for i,((x0,y0),texts) in enumerate(zip(cv_tl,init_texts)):
            if i!=1:
                build_canvas_text = ((x0+10,y0+10,texts[0]),
                    (x0+53,y0+55,texts[1]),(x0+15,y0+20,texts[2]))
                build_canvas_arrow = (
                    (x0+10, y0+50, x0+50, y0+50,axis_color[texts[1]]), 
                    (x0+10, y0+50, x0+10, y0+10,axis_color[texts[2]]),)
                for ann in build_canvas_text: #write annotation
                    self.canvas.create_text(ann[0],ann[1],text=ann[2],
                        font='TkSmallCaptionFont',anchor='sw')
                for arrow in build_canvas_arrow:
                    self.canvas.create_line(*arrow[:4],fill=arrow[4],
                                            arrow='last')
            else: #draw 3D axis separtely to be rotated later
                ann = (x0+10,y0+10,texts[0])
                self.x0y0_3d_axis = (x0+60,y0+50)
                x00 = self.x0y0_3d_axis[0]
                y00 = self.x0y0_3d_axis[1]
                self.canvas.create_text(ann[0],ann[1],text=ann[2],
                                        font='TkSmallCaptionFont',anchor='sw')                
                self.x3d_axis = self.canvas.create_line(x00, y00, 
                    x00+self.dxyz_3d_x_axis0[0], y00+self.dxyz_3d_x_axis0[1],
                    fill=axis_color[texts[1]],arrow='last')
                self.y3d_axis = self.canvas.create_line(
                    x00, y00, x00+self.dxyz_3d_y_axis0[0], 
                    y00+self.dxyz_3d_y_axis0[1],
                    fill=axis_color[texts[2]],arrow='last')
                self.z3d_axis = self.canvas.create_line(
                    x00, y00, x00+self.dxyz_3d_z_axis0[0], 
                    y00+self.dxyz_3d_z_axis0[1],
                    fill=axis_color["+z"],arrow='last')
                print("self.x3d_axis = {:}".format(self.x3d_axis))
        self.base_canvas_id_tuple = self.canvas.find_all()
        
        return canvas
    def make_property_view(self, root):
        def make_listview(root):
            self.listbox_frame = ttk.Frame(root,padding=(5,5))
            self.listview_name = ttk.Label(self.listbox_frame, 
                                           text = "Object Names", width = 40)
            self.listview_name.grid(column=0,row=0,
                                    sticky=(tk.N, tk.S, tk.E, tk.W))
            self.listbox = tk.Listbox(self.listbox_frame, height=10, 
                                      listvariable=self.object_name_list,
                                      font=(None,16), exportselection=False)
            #initial color of text in listbox
            for i,color in enumerate(self.object_color_list):
                self.listbox.itemconfig(i,{'fg':color})
            self.listbox.grid(column=0,row=1,sticky=(tk.N, tk.S, tk.E, tk.W))
            self.listbox.columnconfigure(0,weight=1)
            self.listbox_frame.grid(column=0,row=0,
                                    sticky=(tk.N, tk.S, tk.E, tk.W))
            self.listbox_frame.columnconfigure(0,weight=1)
            #add h-scroll bar
            self.hscroll_listbox_frame = ttk.Scrollbar(self.listbox_frame, 
                orient=tk.HORIZONTAL, command=self.listbox.xview)
            self.hscroll_listbox_frame.grid(column=0,row=2,sticky='ew')
            self.listbox['xscrollcommand'] = self.hscroll_listbox_frame.set
            #add v-scroll bar
            self.vscroll_listbox_frame = ttk.Scrollbar(self.listbox_frame, 
                orient=tk.VERTICAL, command=self.listbox.yview)
            self.vscroll_listbox_frame.grid(column=1,row=1,sticky='ns')
            self.listbox['yscrollcommand'] = self.vscroll_listbox_frame.set

            return self.listbox_frame
        def make_prop_entry(root):
            self.prop_entry_frame = ttk.LabelFrame(
                root, text='Properties',padding=(5,5))
            self.prop_label_dict = dict()
            self.prop_entry_dict = dict()
            self.prop_entry_text_var = dict()
            for i,prop_name in enumerate(self.object_property_list):
                self.prop_label_dict[prop_name] = ttk.Label(
                    self.prop_entry_frame, text=prop_name)
                self.prop_entry_text_var[prop_name] = tk.StringVar()
                tk_name = self.prop_entry_text_var[prop_name]._name
                self.prop_name_to_tk_name[prop_name] = tk_name
                self.tk_name_to_prop_name[tk_name] = prop_name
                    #build name to tk_name dicts
                self.prop_entry_text_var[prop_name].trace_add('write',
                    self.trace_call_back)
                self.prop_entry_dict[prop_name] = ttk.Entry(
                    self.prop_entry_frame,
                    textvariable=self.prop_entry_text_var[prop_name])
                self.prop_to_entry_name[prop_name] = (
                    self.prop_entry_dict[prop_name]._name)
                self.entry_to_prop_name[
                    self.prop_entry_dict[prop_name]._name] = prop_name
                self.prop_label_dict[prop_name].grid(
                    column=0,row=i,sticky='nsew')
                self.prop_entry_dict[prop_name].grid(
                    column=1,row=i,sticky='nsew')

            self.prop_entry_frame.columnconfigure(0,weight=1)
            self.prop_entry_frame.columnconfigure(1,weight=1)
            self.prop_entry_dict['Object id'].config(state='disabled')
            return self.prop_entry_frame
        def make_sim_control(root):
            self.sim_control_frame = ttk.LabelFrame(root, 
                text='Simulation Control', padding=(5,5))
            self.sim_control_dict = dict()
            self.sim_control_dict['frame_time'] = ttk.Frame(
                self.sim_control_frame)
            self.sim_control_dict['current_time_ts'] = ttk.Label(
                self.sim_control_dict['frame_time'],
                text = "Current Time", font=(None,11))
            self.sim_control_dict['current_time_ts_var'] = tk.StringVar()
            self.sim_control_dict['current_time_ts_var'].set(
                '2024-01-14T00:00:00.000000')
            self.sim_control_dict['current_time_ts_entry'] = ttk.Entry(
                self.sim_control_dict['frame_time'],
                textvariable=self.sim_control_dict['current_time_ts_var'],
                justify='right', width = 26)         
            self.sim_control_dict['current_time_ts_unit'] = ttk.Label(
                self.sim_control_dict['frame_time'], 
                text = "yyyy-mm-ddThh:mm:ss", font=(None,11))
            self.sim_control_dict['current_time_day_label'] = ttk.Label(
                self.sim_control_dict['frame_time'],
                text = "Current Time", font=(None,11))
            self.sim_control_dict['current_time_day_var'] = tk.StringVar()
            self.sim_control_dict['current_time_day_var'].set('0')
            self.sim_control_dict['current_time_day_entry'] = ttk.Entry(
                self.sim_control_dict['frame_time'],
                textvariable=self.sim_control_dict['current_time_day_var'],
                justify='right')            
            self.sim_control_dict['current_time_day_unit'] = ttk.Label(
                self.sim_control_dict['frame_time'],
                text = "day", font=(None,11))
            self.sim_control_dict['time_step_label'] = ttk.Label(
                self.sim_control_dict['frame_time'], 
                text = "Time Step", font=(None,11))
            self.sim_control_dict['time_step_entry_s_var'] = tk.StringVar()
            self.sim_control_dict['time_step_entry_s_var'].set('86400')
            self.sim_control_dict['time_step_entry_s'] = ttk.Entry(
                self.sim_control_dict['frame_time'],
                textvariable=self.sim_control_dict['time_step_entry_s_var'],
                justify='right')
            self.sim_control_dict['time_step_entry_s'].config(state='disabled')
            self.sim_control_dict['time_step_entry_d_var'] = tk.StringVar()
            self.sim_control_dict['time_step_entry_d_var'].set('1')
            self.sim_control_dict['time_step_entry_d'] = ttk.Entry(
                self.sim_control_dict['frame_time'],
                textvariable=self.sim_control_dict['time_step_entry_d_var'],
                justify='right')            
            self.sim_control_dict['time_step_label_s_unit'] = ttk.Label(
                self.sim_control_dict['frame_time'], text = "sec", 
                font=(None,11))
            self.sim_control_dict['time_step_label_d_unit'] = ttk.Label(
                self.sim_control_dict['frame_time'], text = "day", 
                font=(None,11))
            self.sim_control_dict['view_mode_labelframe'] = ttk.LabelFrame(
                self.sim_control_frame, text="View Mode",
                padding=(5,5))
            self.sim_control_dict['view_mode_radio_var'] = tk.StringVar()
            self.view_mode_build = ['Barycenter Tracking',
                'Stationary Initial Barycenter','Selected-object tracking',
                'Cartesian coordinates']
            for mode_str in self.view_mode_build:
                self.sim_control_dict[mode_str] = ttk.Radiobutton(
                    self.sim_control_dict['view_mode_labelframe'], 
                    text=mode_str,
                    variable=self.sim_control_dict['view_mode_radio_var'], 
                    value=mode_str)
            self.sim_control_dict['view_mode_radio_var'].set(
                'Stationary Initial Barycenter')
            self.sim_control_dict['rotation_labelframe'] = ttk.LabelFrame(
                self.sim_control_frame, text="Rotation", padding=(5,5))
            
            self.rotation_label = {'rotation_x_label':'x-axis: ',
                                   'rotation_y_label':'y-axis: ',
                                   'rotation_z_label':'z-axis: '}
            self.rotation_entry = [
                'rotation_x_entry','rotation_y_entry','rotation_z_entry']
            self.rotation_scale = [
                'rotation_x_scale','rotation_y_scale','rotation_z_scale']
            self.rotation_entry_var = ['rotation_x_entry_var',
                'rotation_y_entry_var','rotation_z_entry_var']
            for label, entry, scale, entry_var in zip(
                    self.rotation_label.keys(),
                    self.rotation_entry,
                    self.rotation_scale,
                    self.rotation_entry_var):
                self.sim_control_dict[entry_var] = tk.StringVar()
                self.sim_control_dict[entry_var].set("0")
                self.sim_control_dict[entry_var].trace_add(
                    'write',self.rotation_event)
                self.sim_control_dict[scale] = ttk.Scale(
                    self.sim_control_dict['rotation_labelframe'],
                    orient='horizontal', length = 200, from_=-180, to_=180,
                    variable=self.sim_control_dict[entry_var],
                    command=self.rotation_event)
                self.sim_control_dict[label] = ttk.Label(
                    self.sim_control_dict['rotation_labelframe'],
                    text=self.rotation_label[label])
                self.sim_control_dict[entry] = ttk.Entry(
                    self.sim_control_dict['rotation_labelframe'],
                    textvariable=self.sim_control_dict[entry_var])

            self.sim_control_button_build = [
                ('Previous',self.sim_control_previous),
                ('Start',self.sim_control_start),
                ('Pause',self.sim_control_pause),
                ('Next',self.sim_control_next),
                ('Clear',self.sim_control_clear)]
            for name, func in self.sim_control_button_build:
                self.sim_control_dict[name] = ttk.Button(
                    self.sim_control_frame, text=name,command=func)
            sim_control_gridding = [('frame_time',0,0,'we',4),
                                    ('current_time_ts',0,0,'we'),
                                    ('current_time_ts_entry',0,1,'we',2,1,5),
                                    ('current_time_ts_unit',0,3,'we',2),
                                    ('current_time_day_label',1,0,'we'),
                                    ('current_time_day_entry',1,1,'we',3,1,5),
                                    ('current_time_day_unit',1,4,'we'),
                                    ('time_step_label',2,0,'we'),
                                    ('time_step_entry_s',2,1,'we',1,1,5),
                                    ('time_step_label_s_unit',2,2,'we'),
                                    ('time_step_entry_d',2,3,'we',1,1,5),
                                    ('time_step_label_d_unit',2,4,'we'),                                    
                                    ('view_mode_labelframe',3,0,'we',4),
                                    ('Barycenter Tracking',0,0),
                                    ('Stationary Initial Barycenter',1,0),
                                    ('Selected-object tracking',2,0),
                                    ('Cartesian coordinates',3,0),
                                    ('rotation_labelframe',4,0,'we',4),
                                    ('rotation_x_label',0,0),
                                    ('rotation_y_label',1,0),
                                    ('rotation_z_label',2,0),
                                    ('rotation_x_scale',0,1),
                                    ('rotation_y_scale',1,1),
                                    ('rotation_z_scale',2,1),
                                    ('rotation_x_entry',0,2),
                                    ('rotation_y_entry',1,2),
                                    ('rotation_z_entry',2,2),
                                    ('Previous',5,0),
                                    ('Start',5,1),
                                    ('Pause',5,2),
                                    ('Next',5,3),
                                    ('Clear',6,0,'we',4)]
            for values in sim_control_gridding:
                print(values[0])
                self.gridding(self.sim_control_dict[values[0]],*values[1:])
            return self.sim_control_frame
        self.prop_frame = ttk.Frame(root)
        self.prop_pane_bottom = make_prop_entry(self.prop_frame)
        self.prop_pane_top = make_listview(self.prop_frame)
        make_sim_control(self.prop_frame)

        self.prop_pane_top.grid(column=0,row=0,sticky='nsew')
        self.prop_pane_bottom.grid(column=0,row=1,sticky='nsew')
        self.prop_frame.grid(column=0,row=1,sticky='nsew')
        self.prop_pane_top.columnconfigure(0,weight=1)
        self.prop_pane_bottom.columnconfigure(0,weight=1)
        self.prop_frame.columnconfigure(0,weight=1)
        self.sim_control_frame.grid(column=0,row=2,sticky='nsew')
        for col in range(4):
            self.sim_control_frame.columnconfigure(col,weight=1)
        #add more label at the bottom right
        self.barycenter_label_var = tk.StringVar()
        self.update_barycenter()
        self.barycenter_label = ttk.Label(self.prop_frame,
            textvariable=self.barycenter_label_var,font=(None,10))
        self.barycenter_label.grid(column=0,row=3,sticky='nsew')    
        self.status_label_var = tk.StringVar()
        self.status_label_var.set("License: The Unlicense E.P.")
        self.status_label = ttk.Label(self.prop_frame, 
            textvariable=self.status_label_var)
        self.status_label.grid(column=0,row=4,sticky='nsew')
        return self.prop_frame
    def gridding(self, widget, row, column, sticky='we', 
                 columnspan=1, rowspan=1, padx=0,pady=0):
        widget.grid(column=column, row=row, sticky=sticky,
            columnspan=columnspan, rowspan=rowspan, padx=padx,pady=pady)

    def sim_control_previous(self):
        self.keep_on_going = False
        self.t1 = threading.Thread(target=self.cal_next_and_show, 
                                   args=(True,))
        self.t1.start()
    def sim_control_start(self):
        #disable entry that can crash the program
        for i in self.items_to_be_disabled_upon_start:
            self.sim_control_dict[i].config(state='disabled')  
        for i in self.menu_items_to_be_disabled_upon_start:
            self.prop_context_menu.entryconfigure(i, state='disabled')
        
        self.allow_number_updating = False
        self.keep_on_going = True
        self.t1 = threading.Thread(target=self.cal_next_and_show)
        self.t1.start()        
    def sim_control_pause(self):
        self.sim_control_clear(enable_all=True)
        for i in self.menu_items_to_be_disabled_upon_start:
            self.prop_context_menu.entryconfigure(i, state='normal')
        self.keep_on_going = False
        self.nbody_solution.clear()
        self.allow_number_updating = True
    def sim_control_next(self):
        self.keep_on_going = False
        self.t1 = threading.Thread(target=self.cal_next_and_show)
        self.t1.start()
    def cal_next_and_show(self, negative_time=False):
        self.nbody.clear()
        rv = np.array([i[1:] for i in self.obj_data]) 
            # r (distance) and v (velocity), excluding name variable
        ic = np.hstack([rv[:,1:],rv[:,0].reshape(-1,1)]) 
            #initial condition, moving mass from the first to the last column
        names = [i[0] for i in self.obj_data]
        t0_s = float(
            self.sim_control_dict['current_time_day_var'].get())*24*3600
        dt_s = float(self.sim_control_dict['time_step_entry_s_var'].get())
        if negative_time:
            dt_s = abs(dt_s) * -1.0
        self.nbody.set_ic(ic=ic,t0=t0_s,names=names)
        self.nbody.solve_ode(dt_s)
        self.nbody_solution = deque(self.nbody.solution)
        self.time_day_before_animation_loop = float(
            self.sim_control_dict['current_time_day_var'].get())
        self.pd_timestamp_before_animation_loop = pd.to_datetime(
            self.sim_control_dict['current_time_ts_var'].get())
        self.move_using_nbody_solution(self.nbody_solution)

        
    def sim_control_clear(self, enable_all = False):
        if enable_all:
            for i in self.items_to_be_disabled_upon_start:
                self.sim_control_dict[i].config(state='enabled')          
        self.draw_current_state()
    def create_circle(self, event):
        self.canvas.create_oval(event.x-3, event.y-3, 
            event.x+3, event.y+3, fill="#FF0000")
        print(f"x = {event.x}, y = {event.y}")
    def show_object_properties(self, event):
        try:
            selection_id = self.listbox.curselection()[0]
            data_list = self.obj_data[selection_id]
            self.prop_entry_text_var['Object id'].set(str(selection_id))
            for prop_name, data in zip(
                    self.object_property_list[1:], data_list):
                self.prop_entry_text_var[prop_name].set(str(data))
        except Exception as e:
            print(e)
    def trace_call_back(self,*event):
        #"For example, event = ('PY_VAR5', '', 'w')
        if hasattr(self.root.focus_get(),'_name'):
            tk_var_name = event[0]
            prop_name = self.tk_name_to_prop_name[tk_var_name]
            if self.root.focus_get()._name == self.prop_to_entry_name[
                    prop_name]:
                #without this if-statement, 
                #every time that string var change, this event is fired
                #this interferes with the initialization text 
                #into the string var
                current_str = self.root.globalgetvar(tk_var_name)
                index_value = self.object_property_list.index(prop_name)
                selection_id = self.listbox.curselection()[0]
                if index_value > 1:
                    try:
                        new_value = float(current_str)
                        self.obj_data[selection_id][index_value-1] = new_value
                        self.update_barycenter()
                        self.sim_control_clear() #redraw as added new option
                    except ValueError:
                        pass
                else:
                    try:
                        new_value = current_str
                        self.obj_data[selection_id][index_value-1] = new_value
                        new_listbox_value_prep = list(literal_eval(
                            self.object_name_list.get()))
                        new_listbox_value_prep[selection_id]=new_value
                        #e.g. self.object_name_list.get() = 
                        #    "('object 1', 'object 2')"
                        self.object_name_list.set(new_listbox_value_prep)
                        #e.g. new_listbox_value_prep = 
                        #    <class 'list'> ['Sun', 'Earth']
                    except ValueError:
                        pass
    def draw_current_state(self, redraw=True):
        """
        Will be called from "Clear" button
        and the change of number on the properties entry
        Update: picture on canvas
        """
        self.update_barycenter()
        
        if redraw:
            self.initial_bary_xyz = copy.copy(self.bary_xyz)
            self.update_minmax_of_object_in_canvas()
            for i in self.canvas.find_all():
                if not(i in self.base_canvas_id_tuple):
                    self.canvas.delete(i)
        
        #use equal scale ratio for each axis,
        #e.g. 1 px in y & 1 px in x have the same actual distance i m
        #draw x-y plane
        if redraw:
            #calculate range for x-y plane
            x_range_m = self.x_max_m - self.x_min_m
            y_range_m = self.y_max_m - self.y_min_m
            z_range_m = self.z_max_m - self.z_min_m

            if x_range_m/self.canvas_w > y_range_m/self.canvas_h: #xy-plane
                xy_x_range_m = float(x_range_m)
            else:
                xy_x_range_m = y_range_m / self.canvas_h * self.canvas_w
            if xy_x_range_m < z_range_m:
                xy_x_range_m = z_range_m

            range_m_xy = np.array(xy_x_range_m) * self.SCREEN_MULTIPLIER
            self.range_m_xy = range_m_xy
            self.update_distance_relative_to_barycenter(redraw=True)
        else:
            range_m_xy = self.range_m_xy
            self.update_distance_relative_to_barycenter(redraw=False)
        
        if redraw:
            self.xy_obj_id = [] #to be used later when moving object
            self.r_xy_obj_id = []
            self.xz_obj_id = []
            self.yz_obj_id = []
            self.bary_tuple_id = []
                   
        for screen_idx in range(4):
            xc = self.cv_c[screen_idx][0]
            yc = self.cv_c[screen_idx][1]
            if screen_idx == 1:
                iterable_var = enumerate(
                    self.rotated_xyz_relative_to_barycenter)
            else:
                iterable_var = enumerate(self.xyz_relative_to_barycenter)
            for j, xyz in iterable_var: #for each object
                pxyz = np.array(xyz)/range_m_xy * self.sw
                x,y,z = pxyz
                create_circle_of_each_screen = [
                    (xc+x-3,yc-y-3,xc+x+3,yc-y+3),
                    (xc+x-3,yc-y-3,xc+x+3,yc-y+3),
                    (xc+x-3,yc-z-3,xc+x+3,yc-z+3),
                    (xc+y-3,yc-z-3,xc+y+3,yc-z+3)]
                list_of_id_list = [
                    self.xy_obj_id,
                    self.r_xy_obj_id,
                    self.xz_obj_id,
                    self.yz_obj_id]
                if redraw:
                    val = self.canvas.create_oval(
                        *create_circle_of_each_screen[screen_idx], 
                        fill=self.object_color_list[j])
                    list_of_id_list[screen_idx].append(val)
                else:
                    self.canvas.coords(list_of_id_list[screen_idx][j],
                        *create_circle_of_each_screen[screen_idx])
            #draw bary center for each screen
            if screen_idx == 1:
                bx,by,bz = self.rotate_one_dot(
                    self.bary_to_reference_point)/range_m_xy * self.sw
                
            else:
                bx,by,bz = np.array(
                    self.bary_to_reference_point)/range_m_xy * self.sw
            bxy_s = [np.array((xc+bx, yc-by)),
                     np.array((xc+bx, yc-by)),
                     np.array((xc+bx, yc-bz)),
                     np.array((xc+by, yc-bz))]
            if redraw:
                val1 = self.canvas.create_line(*(bxy_s[screen_idx]-4),
                                               *(bxy_s[screen_idx]+4))
                val2 = self.canvas.create_line(
                    *(bxy_s[screen_idx]+np.array((-4,4))),
                    *(bxy_s[screen_idx]+np.array((4,-4))))
                self.bary_tuple_id.append((val1,val2))
            else:
                self.canvas.coords(self.bary_tuple_id[screen_idx][0],
                    *(bxy_s[screen_idx]-4),*(bxy_s[screen_idx]+4))
                self.canvas.coords(self.bary_tuple_id[screen_idx][1],
                    *(bxy_s[screen_idx]+np.array((-4,4))),
                    *(bxy_s[screen_idx]+np.array((4,-4))))
 
    def move_using_nbody_solution(self,all_data_row):
        """
        all_data_row is in the format of
        [[t0,x1,y1,z1,vx1,vy1,vz1,...,xn,yn,zn,vxn,vyn,vzn],
         ...
         [tm,x1,y1,z1,vx1,vy1,vz1,...,xn,yn,zn,vxn,vyn,vzn]]
        """
        #moving fast or not has to do with ODE calculation (and time step)
        #not much to do with the screen updating
        if len(all_data_row) > 0:
            data = all_data_row.popleft()
            dt_s_from_ode_solver = data.pop(0)

            self.sim_control_dict['current_time_day_var'].set(
                str(self.time_day_before_animation_loop 
                    + dt_s_from_ode_solver/3600/24.0))
            updated_ts = (self.pd_timestamp_before_animation_loop 
                          + pd.to_timedelta(dt_s_from_ode_solver,'s'))
            self.sim_control_dict['current_time_ts_var'].set(
                updated_ts.isoformat())
            xyzvuw = np.array(data).reshape(-1,6)
            for i in range(len(self.obj_data)): 
                #update xyz for each object in self.obj_data
                for j in range(6): #update only 
                    self.obj_data[i][2+j] = xyzvuw[i,j]

            self.show_object_properties(None)
            self.draw_current_state(False)
            self.root.after(
                1, lambda : self.move_using_nbody_solution(all_data_row))
        else:
            if self.keep_on_going:
                self.cal_next_and_show()
            else:
                self.sim_control_clear()
            
        
    def rotate_one_dot(self, xyz_dot):
        #xyz_dot is iterable of shape (3,) such as [1,0,0]
        #[1,2,3] means x = 1, y = 2, and z = 3
        try: 
            x_angle = float(
                self.sim_control_dict['rotation_x_entry_var'].get())
            self.last_readable_x_angle = x_angle
        except ValueError:
            x_angle = self.last_readable_x_angle
        try:
            y_angle = float(
                self.sim_control_dict['rotation_y_entry_var'].get())
            self.last_readable_y_angle = y_angle
        except ValueError:
            y_angle = self.last_readable_y_angle
        try:
            z_angle = float(
                self.sim_control_dict['rotation_z_entry_var'].get())
            self.last_readable_z_angle = z_angle
        except ValueError:
            z_angle = self.last_readable_z_angle
        #angle is for axis rotation
        #object rotate in the opposite direction of the axis
        rtt = RTT.from_euler('xyz',[-x_angle,y_angle,-z_angle],degrees=True)
        return rtt.apply(xyz_dot)
            #output from rtt.apply() is numpy array shape (3,)
        
    def rotation_event(self, event, *values):
        try: 
            x_angle = float(
                self.sim_control_dict['rotation_x_entry_var'].get())
            self.last_readable_x_angle = x_angle
        except ValueError:
            x_angle = self.last_readable_x_angle
        try:
            y_angle = float(
                self.sim_control_dict['rotation_y_entry_var'].get())
            self.last_readable_y_angle = y_angle
        except ValueError:
            y_angle = self.last_readable_y_angle
        try:
            z_angle = float(
                self.sim_control_dict['rotation_z_entry_var'].get())
            self.last_readable_z_angle = z_angle
        except ValueError:
            z_angle = self.last_readable_z_angle

        rtt = RTT.from_euler('xyz',[x_angle,y_angle,z_angle],degrees=True)
        self.dxyz_3d_x_axis = rtt.apply(self.dxyz_3d_x_axis0)
        self.dxyz_3d_y_axis = rtt.apply(self.dxyz_3d_y_axis0)
        self.dxyz_3d_z_axis = rtt.apply(self.dxyz_3d_z_axis0)
        
        x00 = self.x0y0_3d_axis[0]
        y00 = self.x0y0_3d_axis[1]        
        self.canvas.coords(self.x3d_axis, 
                           [x00, y00, x00+self.dxyz_3d_x_axis[0], 
                            y00+self.dxyz_3d_x_axis[1]])
        self.canvas.coords(self.y3d_axis, 
                           [x00, y00, x00+self.dxyz_3d_y_axis[0], 
                            y00+self.dxyz_3d_y_axis[1]])
        self.canvas.coords(self.z3d_axis, 
                           [x00, y00, x00+self.dxyz_3d_z_axis[0], 
                            y00+self.dxyz_3d_z_axis[1]])
        self.sim_control_clear(enable_all = False)

    def update_barycenter(self):
        """"
        update self.barycenter_label_var
        update self.bary_xyz
        bary_center_x = (M1x1 + M2x2 + ... Mnxn)/(M1+...+Mn)
        self.obj_data = [['object 1', 1.0e24, 0, 0, 0, 1e5, 0.5e5, 500.0],
                         ['object 2', 1.0e24, 1e5, 0, 0, 1e5, 0.5e5, 500.0]]
        """
        try:
            data = np.array([[float(i) for i in row[1:5]] 
                             for row in self.obj_data])
            bary_x = sum(data[:,0]*data[:,1])/sum(data[:,0])
            bary_y = sum(data[:,0]*data[:,2])/sum(data[:,0])
            bary_z = sum(data[:,0]*data[:,3])/sum(data[:,0])
            self.bary_xyz = [bary_x,bary_y,bary_z]
            self.barycenter_label_var.set(
                "Barycenter = ({:.7e}, {:.7e}, {:.7e}) m".format(
                    bary_x,bary_y,bary_z))
        except ValueError:
            pass
    def update_minmax_of_object_in_canvas(self):
        #update value of min and max of x,y,z of the object
        #the result has the unit of meter
        data = np.array(
            [[float(i) for i in row[2:5]] for row in self.obj_data])
        self.x_min_m = data[:,0].min()
        self.x_max_m = data[:,0].max()
        self.y_min_m = data[:,1].min()
        self.y_max_m = data[:,1].max()
        self.z_min_m = data[:,2].min()
        self.z_max_m = data[:,2].max()
        #for rotated coordinate
        r_data = np.array([self.rotate_one_dot(i) for i in data])
        self.r_x_min_m = r_data[:,0].min()
        self.r_x_max_m = r_data[:,0].max()
        self.r_y_min_m = r_data[:,1].min()
        self.r_y_max_m = r_data[:,1].max()
        self.r_z_min_m = r_data[:,2].min()
        self.r_z_max_m = r_data[:,2].max()        
        
    def update_distance_relative_to_barycenter(self, redraw):
        #
        if (self.sim_control_dict['view_mode_radio_var'].get() 
            == 'Stationary Initial Barycenter'):
            if redraw:
                ref_pt = self.bary_xyz
            else:
                ref_pt = self.initial_bary_xyz
        elif (self.sim_control_dict['view_mode_radio_var'].get() 
              == 'Barycenter Tracking'):
            ref_pt = self.bary_xyz
        elif (self.sim_control_dict['view_mode_radio_var'].get() 
              == 'Selected-object tracking'):
            selection_id = self.listbox.curselection()[0]
            ref_pt = self.obj_data[selection_id][2:5]
        else:
            ref_pt = [0,0,0]
            
        
        self.bary_to_reference_point = np.array(
            self.bary_xyz) - np.array(ref_pt)
        data = np.array(
            [[float(i) for i in row[2:5]] for row in self.obj_data])
        self.xyz_relative_to_barycenter = np.array([[i[0] - ref_pt[0],
            i[1] - ref_pt[1],
            i[2] - ref_pt[2]] for i in data])
        self.rotated_xyz_relative_to_barycenter = np.array(
            [self.rotate_one_dot(i) for i in self.xyz_relative_to_barycenter])
    def move_on_time_step_entry_s(self,event):
        self.sim_control_dict['time_step_entry_s'].config(state='enabled')
        self.sim_control_dict['time_step_entry_d'].config(state='disabled')
    def move_on_time_step_entry_d(self,event):
        self.sim_control_dict['time_step_entry_s'].config(state='disabled')
        self.sim_control_dict['time_step_entry_d'].config(state='enabled')
    def trace_callback_edit_s_timestep(self,*event):
        try:
            second = float(
                self.sim_control_dict['time_step_entry_s_var'].get())
            day = second / 3600.0/24.0
            self.sim_control_dict['time_step_entry_d_var'].set(str(day))
        except ValueError:
            pass
    def trace_callback_edit_d_timestep(self,*event):
        try:
            day = float(self.sim_control_dict['time_step_entry_d_var'].get())
            second = day * 3600.0*24.0
            self.sim_control_dict['time_step_entry_s_var'].set(str(second))    
        except ValueError:
            pass
if __name__ == '__main__':
    main_view = MainView()
    main_view.root.mainloop()


#Reference
#https://stackoverflow.com/questions/6548837/
#    how-do-i-get-an-event-callback-when-a-tkinter-entry-widget-is-modified
#https://stackoverflow.com/questions/16745507/
#    tkinter-how-to-use-threads-to-preventing-main-event-loop-from-freezing
#https://stackoverflow.com/questions/71677889/
#    create-a-scrollbar-to-a-full-window-tkinter-in-python
#https://stackoverflow.com/questions/17355902/
#    tkinter-binding-mousewheel-to-scrollbar
#https://tcl.tk/man/tcl8.6/TkCmd/bind.htm#M9