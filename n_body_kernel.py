#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#"""
#Created on Sun Feb 18 09:48:53 2024
#
#@author: Ekarit Panacharoensawad
#"""

import numpy as np
from collections import defaultdict
from scipy.integrate import ode

class N_body:
    def __init__(self):
        self.G = 6.6743015e-11
        self.solution = []
        self.pretty_result = defaultdict(list)
            #anser in the format of {name1:np.array([t,x,y,z,vx,vy,vz]), ...}
    def clear(self):
        self.solution = []
        self.pretty_result = defaultdict(list)
    def set_ic(self, 
               ic=np.array([[0,0,0,0,0,0,1.98847e30],
                   [149.6e9,0,0,0,29.8e3,0,5.9722e24],
                   [149.978e9,0,0,0,30822,0,7.34767309e22]]),
               t0 = 0,
               names = None):
        '''
        ic: initial condition in the format of
            np.array(
                [[rx,ry,rz,vx,vy,vz,m],
                ...
                 [rx,ry,rz,vx,vy,vz,m]
                ])
                unit: rx = meter, vx = m/s, m = kg
                the number or row is the same as the number of object
        t0 = initial time in second
        names = list of name of each ic, for example, names = [
            'Sun', 'Earth', 'Moon']    
        Hint:
            Sun mass = 1.98847e30 kg, 251e3 m/s (
                relative to Milky Way center of mass)
            Earth mass = 5.9722e24 kg, 29.8e3 m/s (
                relative to sun), 149.6e9 m from sun
            moon mass = 7.34767309e22 kg, 1022 m/s (
                relative to earth), 0.378e9 m from earth
        '''
        self.n = len(ic)
        if self.n < 2:
            raise ValueError("n cannot be less than 2")
        if names == None:
            names = ['m_'+str(i) for i in range(self.n)]
        self.names = names
        self.ic = ic
        self.current_condition = np.array(self.ic)
        self.ic_for_ode_solver = np.array([i[:6] for i in self.ic]).flatten()
        self.m = ic[:,-1]
        self.t0 = t0
        self.current_time_second = t0 #second
    def equation_of_motion(self, t, y):
        '''
        function in the format of f(t,y) where
            t = time in second
            y = (n,) shape numpy array
                n is the number of equationsor 6 x number of objects
                for 3 body problem
                y[0] = rx0;  y[6] = rx1;  y[12] = rx2
                y[1] = ry0;  y[7] = ry1;  y[13] = ry2
                y[2] = rz0;  y[8] = rz1;  y[14] = rz2
                y[3] = vx0;  y[9] = vx1;  y[15] = vx2
                y[4] = vy0;  y[10] = vy1;  y[16] = vy2
                y[5] = vz0;  y[11] = vz1;  y[17] = vz2

                Return: function result (float) of shape (3*n,)
                which is the righthand side of each d/dt equation
                f[0]= d rx0 /dt fn; f[6] = d rx1 /dt fn; f[12] = d rx2 /dt fn
                f[1]= d ry0 /dt fn; f[7] = d ry1 /dt fn; f[13] = d ry2 /dt fn
                f[2]= d rz0 /dt fn; f[8] = d rz1 /dt fn; f[14] = d rz2 /dt fn
                f[3]= d vx0 /dt fn; f[9] = d vx1 /dt fn; f[15] = d vx2 /dt fn
                f[4]= d vy0 /dt fn; f[10] = d vy1 /dt fn; f[16] = d vy2 /dt fn
                f[5]= d vz0 /dt fn; f[11] = d vz1 /dt fn; f[17] = d vz2 /dt fn
        '''
        n = self.n
        m = self.m
        G = self.G
        ans = []
        for i in range(n): # force acted upon object i
            ans = ans + [y[3+i*6], y[4+i*6], y[5+i*6]]
                #append  vx,       vy,       vz
            #cal s
            sx = np.empty((n,n))
            sy = np.empty((n,n))
            sz = np.empty((n,n))
            s = np.empty((n,n))
            for j in range(n):
                if i != j:
                    sx[i,j] = y[j*6] - y[i*6]
                    sy[i,j] = y[1+j*6] - y[1+i*6]
                    sz[i,j] = y[2+j*6] - y[2+i*6]
                    s[i,j] = (sx[i,j]**2+sy[i,j]**2+sz[i,j]**2)**0.5
            ax = 0
            ay = 0
            az = 0
            for j in range(n): # froce from objecct j
                if i != j:
                    ax += m[j]*sx[i,j]/s[i,j]**3
                    ay += m[j]*sy[i,j]/s[i,j]**3
                    az += m[j]*sz[i,j]/s[i,j]**3
            ax = ax*G
            ay = ay*G
            az = az*G
            ans = ans + [ax,ay,az]
        return ans
    def solve_ode(self, t):
        """
        t = end time in second
        """
        self.dt = t
        ode_solver = ode(self.equation_of_motion)
        ode_solver.set_integrator('dopri5', rtol= 1e-8,nsteps=10000)
        ode_solver.set_initial_value(self.ic_for_ode_solver,0)
            #ode solver, take input as dt (time difference), thus
            #it always start at zero as the initial condition
            #the current time is tracked externally
        ode_solver.set_solout(self.update_solution)
        ode_solver.integrate(t)
        self.current_time_second = self.current_time_second + t

    def update_solution(self, t, y):
        self.solution.append([t,*y])
        for i,name in enumerate(self.names):
            value = [t]+[y[j+6*i] for j in range(6)]
            self.pretty_result[name].append(value)
            self.current_condition[i,:6] = np.array([y[j+6*i] 
                                                     for j in range(6)])
        return None
    def update_ic(self):
        self.t0 = float(self.current_time_second)
        self.solution = []
        self.pretty_result = defaultdict(list)        
        self.ic_for_ode_solver = np.array(
            [i[:6] for i in self.current_condition]).flatten()        

